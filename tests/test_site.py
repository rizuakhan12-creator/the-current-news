import importlib.util
import json
import os
import subprocess
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from common import canonical, fingerprint, validate

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('src','href') and v and v.startswith('/'): self.links.append(v)

class SiteTests(unittest.TestCase):
    def test_tracking_duplicates(self):
        self.assertEqual(fingerprint('https://example.org/story?utm_source=x#anchor'),fingerprint('https://example.org/story/'))
        with self.assertRaises(ValueError): canonical('javascript:alert(1)')
        with self.assertRaises(ValueError): canonical('http://example.org')

    def test_review_gate(self):
        a=dict(slug='test-story',category='Technology',title='Test title',summary='Summary',
               meta_description='Description',author='Editor',published_at='2026-10-30T09:00:00Z',
               paragraphs=['Text'],tags=['test'],sources=[dict(name='Source',url='https://example.org')])
        with self.assertRaises(ValueError): validate(a)

    def test_build_and_internal_links(self):
        env={**os.environ,'SITE_URL':'https://example.org/pressroom','PRODUCTION':'0','INCLUDE_DEMOS':'1'}
        subprocess.run([sys.executable,'scripts/build.py'],cwd=ROOT,env=env,check=True)
        for file in (ROOT/'dist').rglob('*.html'):
            parser=Links();parser.feed(file.read_text(encoding='utf-8'))
            for url in parser.links:
                path=unquote(urlsplit(url).path).removeprefix('/pressroom/')
                target=ROOT/'dist'/path
                if target.is_dir(): target=target/'index.html'
                self.assertTrue(target.exists(),f'{file.name}: {url}')
        self.assertFalse((ROOT/'dist/.env').exists())
        self.assertFalse((ROOT/'dist/content/drafts').exists())

    def test_production_excludes_demos(self):
        env={**os.environ,'SITE_URL':'https://example.org','PRODUCTION':'1','INCLUDE_DEMOS':'1'}
        subprocess.run([sys.executable,'scripts/build.py'],cwd=ROOT,env=env,check=True)
        indexed=json.loads((ROOT/'dist/assets/search.json').read_text())
        demos={json.loads(p.read_text(encoding='utf-8'))['slug'] for p in (ROOT/'content/articles').glob('*.json') if json.loads(p.read_text(encoding='utf-8')).get('demo')}
        self.assertFalse(demos.intersection(a['slug'] for a in indexed))
        for demo in demos: self.assertNotIn('/articles/'+demo+'/',(ROOT/'dist/sitemap.xml').read_text())
        self.assertFalse(json.loads((ROOT/'dist/assets/ads.json').read_text())['enabled'])
        if not indexed: self.assertIn('The next edition starts here',(ROOT/'dist/index.html').read_text(encoding='utf-8'))

    def test_reviewed_article_is_rendered_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp)/'site'
            shutil.copytree(ROOT,project,ignore=shutil.ignore_patterns('dist','.git','__pycache__','.venv'))
            article=dict(slug='reviewed-story',category='Technology',title='A checked story <script>unsafe()</script>',
                summary='An original source-linked summary.',meta_description='A checked description.',author='Editor',
                published_at='2026-10-30T09:00:00Z',paragraphs=['A paragraph with <script>unsafe()</script> text.'],
                tags=['reporting'],sources=[dict(name='Example source',url='https://example.org/report')],
                status='published',reviewed_by='Test Editor',verified_at='2026-10-30T08:00:00Z',ai_assisted=True)
            (project/'content/articles/reviewed-story.json').write_text(json.dumps(article),encoding='utf-8')
            (project/'content/drafts/private.json').write_text('{"secret_evidence":"PRIVATE-DRAFT-MARKER"}')
            env={**os.environ,'SITE_URL':'https://example.org/news','PRODUCTION':'1'}
            subprocess.run([sys.executable,'scripts/build.py'],cwd=project,env=env,check=True)
            page=(project/'dist/articles/reviewed-story/index.html').read_text(encoding='utf-8')
            self.assertIn('&lt;script&gt;',page)
            self.assertNotIn('<script>unsafe()',page)
            self.assertIn('NewsArticle',page)
            self.assertIn('Test Editor',page)
            self.assertIn('https://example.org/news/articles/reviewed-story/',page)
            self.assertIn('/articles/reviewed-story/',(project/'dist/sitemap.xml').read_text())
            self.assertNotIn('PRIVATE-DRAFT-MARKER',''.join(p.read_text(encoding='utf-8') for p in (project/'dist').rglob('*.html')))

if __name__=='__main__': unittest.main()
