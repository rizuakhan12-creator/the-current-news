"""Collect RSS/Atom leads for human authors. Standard library only; no AI calls."""
import html
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import HTTPRedirectHandler, Request, build_opener
from common import ROOT, read, write, canonical, fingerprint, title_key

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', value or ''))).strip()

def fetch(url):
    request = Request(canonical(url), headers={'User-Agent': 'TheCurrentRSSReader/1.0'})
    with build_opener(NoRedirect).open(request, timeout=30) as response:
        data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError('Feed exceeds 2 MB limit')
        return data

def parse_feed(data):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('Feed DTDs and entities are unsupported')
    root = ET.fromstring(data)
    local = lambda tag: tag.rsplit('}', 1)[-1]
    if local(root.tag) not in {'rss', 'feed', 'RDF'}:
        raise ValueError('Expected an RSS or Atom document')
    entries = []
    for item in root.iter():
        if local(item.tag) not in {'item', 'entry'}:
            continue
        values, url = {}, ''
        for child in item:
            name = local(child.tag)
            values[name] = ''.join(child.itertext())
            if name == 'link' and child.get('rel', 'alternate') == 'alternate':
                url = child.get('href') or child.text or url
        entries.append(dict(title=clean(values.get('title', ''))[:250], url=url.strip(),
            excerpt=clean(values.get('description') or values.get('summary') or '')[:1200],
            published=values.get('pubDate') or values.get('published') or values.get('updated') or values.get('date')))
    return entries

def source_date(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (ValueError, TypeError):
        parsed = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    if not parsed.tzinfo:
        raise ValueError('Source date requires a timezone')
    return parsed.astimezone(timezone.utc)

def main():
    feeds = read(ROOT/'config/feeds.json')['feeds']
    known_urls, known_titles = set(), set()
    for folder in ('articles', 'drafts'):
        for path in (ROOT/'content'/folder).glob('*.json'):
            a = read(path)
            known_titles.add(title_key(a.get('source_title') or a['title']))
            known_urls.update(canonical(s['url']) for s in a['sources'])
    created, errors, skipped = 0, 0, 0
    limit = min(max(int(os.getenv('MAX_ITEMS', '10')), 0), 30)
    for feed in feeds:
        if not feed.get('enabled'):
            continue
        if not feed.get('rights_confirmed'):
            raise ValueError(f"Review feed metadata reuse first: {feed['name']}")
        if feed['category'] not in read(ROOT/'config/site.json')['categories']:
            raise ValueError('Unknown feed category')
        if created >= limit:
            break
        try:
            entries = parse_feed(fetch(feed['url']))
            for item in entries[:30]:
                if created >= limit:
                    break
                try:
                    url = canonical(item['url'])
                    published = source_date(item['published'])
                except (ValueError, TypeError):
                    skipped += 1
                    continue
                if not item['title'] or url in known_urls or title_key(item['title']) in known_titles:
                    continue
                if published and not -3600 <= time.time()-published.timestamp() <= 7*86400:
                    continue
                ident = fingerprint(url)
                # Empty fields prevent a source excerpt being published as an authored article.
                data = dict(id=ident, slug=f'rss-{ident}', title='', summary='', meta_description='',
                    author='', paragraphs=[], tags=[], status='draft', content_origin='rss_manual',
                    ai_assisted=False, needs_more_reporting=True,
                    verification_notes=['Open the original source and verify each claim.',
                        'Write an original title, summary, description and article body.',
                        'Check text/image rights and all source links before approval.'],
                    source_title=item['title'], source_excerpt=item['excerpt'],
                    source_published_at=published.isoformat() if published else None,
                    fetched_at=datetime.now(timezone.utc).isoformat(), category=feed['category'],
                    sources=[dict(name=feed['name'], url=url)], featured=False, demo=False)
                write(ROOT/'content/drafts'/f'{ident}.json', data)
                known_urls.add(url)
                known_titles.add(title_key(item['title']))
                created += 1
        except Exception as exc:
            errors += 1
            print(f"Feed failed: {feed['name']} ({type(exc).__name__}). Check the final HTTPS feed URL.", file=sys.stderr)
    print(f'Collected {created} RSS leads; {errors} feed errors; {skipped} invalid entries. No articles published. No AI requests made.')
    if errors:
        sys.exit(1)

if __name__ == '__main__':
    main()
