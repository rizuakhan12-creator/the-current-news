import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import news

class RSSTests(unittest.TestCase):
    def test_atom_and_unsafe_xml(self):
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Source title</title><link href="https://example.org/a"/><summary>Short evidence</summary><updated>2026-10-30T09:00:00Z</updated></entry></feed>'
        self.assertEqual(news.parse_feed(atom)[0]['url'],'https://example.org/a')
        with self.assertRaises(ValueError): news.parse_feed(b'<!DOCTYPE rss [<!ENTITY x "bad">]><rss/>')
        with self.assertRaises(ValueError): news.parse_feed(b'<html/>')

    def test_collection_is_deduplicated_and_not_publishable(self):
        date=format_datetime(datetime.now(timezone.utc))
        xml=f'<rss><channel><item><title>A source headline</title><link>https://example.org/a?utm_source=x</link><description>&lt;b&gt;Source excerpt&lt;/b&gt;</description><pubDate>{date}</pubDate></item><item><title>Bad link</title><link>javascript:alert(1)</link></item><item><title>A source headline!</title><link>https://example.org/b</link></item></channel></rss>'.encode()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for folder in ('config','content/articles','content/drafts'): (root/folder).mkdir(parents=True)
            (root/'config/site.json').write_text(json.dumps({'categories':['Technology']}))
            (root/'config/feeds.json').write_text(json.dumps({'feeds':[dict(name='Test',url='https://example.org/feed',category='Technology',enabled=True,rights_confirmed=True)]}))
            with patch.object(news,'ROOT',root),patch.object(news,'fetch',return_value=xml),patch.dict(os.environ,{'MAX_ITEMS':'10','OPENAI_API_KEY':'unused-test-value'}):
                news.main()
                news.main()
            drafts=list((root/'content/drafts').glob('*.json'))
            self.assertEqual(len(drafts),1)
            article=json.loads(drafts[0].read_text())
            self.assertEqual(article['paragraphs'],[])
            self.assertEqual(article['title'],'')
            self.assertEqual(article['source_excerpt'],'Source excerpt')
            self.assertFalse(article['ai_assisted'])
            self.assertTrue(article['needs_more_reporting'])
            self.assertEqual(list((root/'content/articles').glob('*.json')),[])

    def test_manual_approval_rejects_empty_lead_then_accepts_authored_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for folder in ('scripts','config','content/articles','content/drafts'): (root/folder).mkdir(parents=True)
            for name in ('common.py','approve.py'): shutil.copy(ROOT/'scripts'/name,root/'scripts'/name)
            shutil.copy(ROOT/'config/site.json',root/'config/site.json')
            ident='a'*20
            path=root/'content/drafts'/f'{ident}.json'
            article=dict(slug='original-editorial-story',title='',summary='',meta_description='',author='',
                category='Technology',paragraphs=[],tags=[],sources=[dict(name='Source',url='https://example.org/a')],
                status='draft',content_origin='rss_manual',needs_more_reporting=True,ai_assisted=False)
            path.write_text(json.dumps(article))
            command=[sys.executable,str(root/'scripts/approve.py'),ident,'--reviewer','Human Editor','--verified']
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            article.update(title='Original reporting by our editor',summary='A manually written summary.',
                meta_description='Original description for search.',author='Human Editor',
                paragraphs=['Original checked reporting, written by the editor.'],needs_more_reporting=False)
            path.write_text(json.dumps(article))
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            published=json.loads((root/'content/articles/original-editorial-story.json').read_text())
            self.assertEqual(published['status'],'published')
            self.assertEqual(published['reviewed_by'],'Human Editor')
            self.assertFalse(path.exists())

if __name__=='__main__': unittest.main()
