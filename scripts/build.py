"""Dependency-free static HTML generator. Never copies drafts or secrets."""
import html
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from common import ROOT, read, validate

OUT = ROOT / "dist"
CONFIG = read(ROOT / "config/site.json")
URL = (os.getenv("SITE_URL") or CONFIG["url"]).rstrip("/")
PRODUCTION = os.getenv("PRODUCTION") == "1"
BASE = urlsplit(URL).path.rstrip("/")
if PRODUCTION and (urlsplit(URL).scheme != "https" or urlsplit(URL).hostname in (None, "your-domain.example")):
    raise ValueError("Set SITE_URL to the final HTTPS site address")

def e(value):
    return html.escape(str(value), quote=True)

def link(path=""):
    return BASE + "/" + path.lstrip("/")

def slug(value):
    return value.lower().replace(" ", "-")

def output(path, content):
    dest = OUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")

def ad(slot):
    if not ADS["enabled"]:
        return ""
    return f'<aside class="ad ad-{slot}" aria-label="Advertisement"><small>ADVERTISEMENT</small><div data-ad-slot="{slot}"></div></aside>'

def image_path(a):
    image = a.get('image', 'assets/'+slug(a['category'])+'.svg')
    p = Path(image)
    if not image.startswith('assets/') or p.is_absolute() or '..' in p.parts or not (ROOT/'static'/p).is_file():
        raise ValueError('Article image must reference an existing local static/assets file')
    return image

def card(a, hero=False):
    return f'''<article class="card {'hero-card' if hero else ''}">
      <a class="cover" href="{link('articles/'+a['slug']+'/')}" tabindex="-1" aria-hidden="true"><img src="{link(image_path(a))}" alt="" width="1000" height="640" {'fetchpriority="high"' if hero else 'loading="lazy"'}></a>
      <div class="card-copy"><span class="eyebrow">{e(a['category'])} {'· DEMO' if a.get('demo') else ''}</span>
      <h{'2' if hero else '3'}><a href="{link('articles/'+a['slug']+'/')}">{e(a['title'])}</a></h{'2' if hero else '3'}>
      <p>{e(a['summary'])}</p><div class="byline">{e(a['author'])} <span>· {e(a['published_at'][:10])} · {max(1,len(' '.join(a['paragraphs']).split())//200)} min read</span></div></div></article>'''

def shell(title, description, path, body, article=None, noindex=False):
    canonical = URL + "/" + path
    schema = {"@context":"https://schema.org", "@type":"NewsMediaOrganization", "name":CONFIG["name"], "url":URL}
    if article and not article.get("demo"):
        schema = {"@context":"https://schema.org", "@type":"NewsArticle", "headline":article["title"],
                  "description":article["meta_description"], "datePublished":article["published_at"],
                  "dateModified":article.get("updated_at",article["published_at"]),
                  "author":{"@type":"Organization","name":article["author"]},
                  "publisher":{"@type":"Organization","name":CONFIG["name"]},
                  "image":URL+'/'+image_path(article),
                  "mainEntityOfPage":canonical, "citation":[s["url"] for s in article["sources"]]}
    nav = ''.join(f'<a href="{link("category/"+slug(c)+"/")}">{e(c)}</a>' for c in CONFIG['categories'])
    policies = ''.join(f'<a href="{link(slug(c)+"/")}">{c}</a>' for c in ['About Us','Contact Us','Privacy Policy','Terms and Conditions','Disclaimer'])
    demo = '<div class="demo-note">PREVIEW EDITION <span>Sample explainers demonstrate the layout. They are not live news reports.</span></div>' if any(a.get('demo') for a in ARTICLES) else ''
    structured = json.dumps(schema).replace('<','\\u003c')
    image = URL + '/' + (image_path(article) if article else 'assets/technology.svg')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
      <title>{e(title)} | {e(CONFIG['name'])}</title><meta name="description" content="{e(description)}"><link rel="canonical" href="{e(canonical)}">
      <meta name="robots" content="{'noindex,follow' if noindex or not PRODUCTION else 'index,follow'}">
      <meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{e(canonical)}"><meta property="og:image" content="{e(image)}"><meta name="twitter:card" content="summary_large_image">
      <meta name="color-scheme" content="light dark"><link rel="icon" href="{link('assets/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="{link('assets/style.css')}">
      <script type="application/ld+json">{structured}</script>{CMP}<script defer src="{link('assets/app.js')}"></script></head>
      <body><a class="skip" href="#main">Skip to content</a><div class="utility"><span>INDEPENDENT PERSPECTIVE. EVERY DAY.</span><span>A little context goes a long way.</span></div>
      <header><div class="masthead"><a class="brand" href="{link()}">the current<span>●</span></a><span class="tagline">Stay curious.<br>See the bigger picture.</span><div class="header-actions"><a class="search-link" href="{link('search/')}">⌕ <span>Search</span></a><button id="theme" aria-label="Toggle dark mode">◐</button></div></div><nav aria-label="Main navigation"><a href="{link()}">The Front Page</a>{nav}</nav></header>
      {demo}<main id="main">{body}</main>{ad('footer')}<footer><div class="footer-top"><a class="brand" href="{link()}">the current<span>●</span></a><p>Less noise. More perspective.<br>Stories worth your attention.</p></div><div class="footer-links">{policies}<button id="privacy-settings">Cookie settings</button></div><div class="copyright">© {datetime.now().year} {e(CONFIG['name'])}. Source-linked journalism, thoughtfully presented.</div></footer>
      <section id="consent" class="consent" aria-label="Privacy choices" hidden><strong>Your privacy, your choice.</strong><p>Essential preferences stay on this device. Optional advertising loads only after a valid consent signal.</p><div><button id="reject">Essential only</button><button id="accept">Allow optional ads</button></div><a href="{link('privacy-policy/')}">Read our privacy policy</a></section></body></html>'''

def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    global ADS, ARTICLES, CMP
    ADS = read(ROOT / 'config/ads.json')
    # Only explicitly enabled production ads. Browser configuration contains PUBLIC publisher codes only.
    ADS['enabled'] = bool(ADS.get('enabled') and PRODUCTION)
    CMP = ''
    if ADS.get('cmp_head_file'):
        p = (ROOT / ADS['cmp_head_file']).resolve()
        if ROOT not in p.parents or p.suffix != '.html':
            raise ValueError('CMP must be a trusted .html file within the repository')
        CMP = p.read_text(encoding='utf-8') if ADS['enabled'] else ''
    if ADS['enabled'] and ADS['consent_mode'] != 'external':
        raise ValueError('Production ads require external CMP integration')
    ARTICLES = []
    paths = list((ROOT/'content/articles').glob('*.json'))
    for path in paths:
        a = read(path)
        if a.get('status') != 'published':
            continue
        if a.get('demo') and (PRODUCTION or os.getenv('INCLUDE_DEMOS','1') != '1'):
            continue
        validate(a)
        ARTICLES.append(a)
    ARTICLES.sort(key=lambda a:a['published_at'], reverse=True)
    if len({a['slug'] for a in ARTICLES}) != len(ARTICLES):
        raise ValueError('Duplicate article slug')
    urls = ['', 'search/']
    featured = next((a for a in ARTICLES if a.get('featured')), ARTICLES[0] if ARTICLES else None)
    remainder = [a for a in ARTICLES if a is not featured]
    picks = ''.join(f'<li><span>0{i+1}</span><div><small>{e(a["category"])}</small><a href="{link("articles/"+a["slug"]+"/")}">{e(a["title"])}</a></div></li>' for i,a in enumerate(remainder[:3]))
    trending = ''.join(f'<a href="{link("articles/"+a["slug"]+"/")}">{e(a["title"])}</a>' for a in ARTICLES[:3])
    body = f'<div class="trending"><b>ON OUR RADAR <span>↗</span></b>{trending or "Our editors are preparing the first edition."}</div>{ad("homepage")}<div class="section-heading"><h1>The Front Page</h1><span>Good stories. A fresh perspective.</span></div>'
    if featured:
        body += f'<section class="lead-grid" aria-label="Featured stories">{card(featured,True)}<aside class="editors"><div class="eyebrow">THE SHORTLIST</div><h2>Worth your<br>attention<span>↗</span></h2><ol>{picks}</ol><div class="editor-note">A smarter scroll starts here.<br><span>Context over clickbait. Always.</span></div>{ad("sidebar")}</aside></section>'
    else:
        body += '<section class="empty"><h2>The next edition starts here.</h2><p>Our editorial desk is checking sources. Verified stories will appear after review.</p></section>'
    categories = ''.join(f'<a href="{link("category/"+slug(c)+"/")}">{c} <span>↗</span></a>' for c in CONFIG['categories'])
    body += f'<section class="latest"><div class="section-heading"><h2>The Latest</h2><a href="{link("search/")}">Explore all stories ↗</a></div><div class="cards">'+''.join(card(a) for a in remainder)+'</div></section>'+f'<section class="explore"><div class="eyebrow">FOLLOW YOUR CURIOSITY</div><h2>There’s a whole world to explore.</h2><div>{categories}</div></section>'
    output('index.html',shell(CONFIG['description'].split('.')[0],CONFIG['description'],'',body))
    for category in CONFIG['categories']:
        path = 'category/'+slug(category)+'/'
        group = [a for a in ARTICLES if a['category']==category]
        body = f'<div class="page-heading"><span class="eyebrow">YOUR WORLD, IN CONTEXT</span><h1>{e(category)}</h1><p>The stories and ideas shaping {e(category.lower())}.</p></div><div class="cards">'+(''.join(card(a) for a in group) or '<p>No published stories in this category yet. Check back soon.</p>')+'</div>'
        output(path+'index.html',shell(category, 'Latest '+category+' stories.',path,body)); urls.append(path)
    for a in ARTICLES:
        path='articles/'+a['slug']+'/'
        sources=''.join(f'<li><a href="{e(s["url"])}" rel="noopener noreferrer">{e(s["name"])} ↗</a></li>' for s in a['sources'])
        paragraphs=''.join('<p>'+e(p)+'</p>'+ (ad('article') if i==1 else '') for i,p in enumerate(a['paragraphs']))
        related=sorted((x for x in ARTICLES if x is not a), key=lambda x:x['category']!=a['category'])[:3]
        body=f'''<article class="article"><a class="eyebrow" href="{link('category/'+slug(a['category'])+'/')}">{e(a['category'])}</a><h1>{e(a['title'])}</h1><p class="dek">{e(a['summary'])}</p><div class="article-byline">By {e(a['author'])} <time datetime="{e(a['published_at'])}">{e(a['published_at'][:10])}</time><button id="share">Copy article link ↗</button><span id="share-status" role="status"></span></div>
        <figure><img src="{link(image_path(a))}" width="1000" height="640" alt="{e(a.get('image_alt', 'Abstract editorial illustration for '+a['category']))}"><figcaption>{e(a.get('image_credit','Editorial illustration · The Current'))}</figcaption></figure>
        <div class="reading">{'<p class="notice">Demo explainer — this sample is not a current news report.</p>' if a.get('demo') else ''}{'<p class="notice">AI-assisted draft, checked and approved by '+e(a['reviewed_by'])+'.</p>' if a.get('ai_assisted') else ''}{paragraphs}<section class="sources"><h2>Sources & further reading</h2><p>Read the original material. Source links do not imply endorsement.</p><ul>{sources}</ul></section><div class="tags">{''.join('<span>'+e(t)+'</span>' for t in a.get('tags',[]))}</div></div></article><section><div class="section-heading"><h2>Keep exploring</h2></div><div class="cards">{''.join(card(r) for r in related)}</div></section>'''
        output(path+'index.html',shell(a['title'],a['meta_description'],path,body,a,noindex=a.get('demo',False)))
        if not a.get('demo'): urls.append(path)
    options=''.join(f'<option>{e(c)}</option>' for c in CONFIG['categories'])
    body=f'<div class="page-heading"><span class="eyebrow">FIND YOUR NEXT READ</span><h1>Follow the story.</h1><p>Search our published stories by topic, title, or tag.</p></div><form id="search-form" class="search-form"><label>Search stories<input id="query" type="search" name="q" placeholder="What are you curious about?"></label><label>Category<select id="category"><option value="">All categories</option>{options}</select></label><button>Search ↗</button></form><p id="result-count" role="status"></p><div id="results" class="cards"></div><noscript>Enable JavaScript for search, or browse the category links above.</noscript>'
    output('search/index.html',shell('Search','Find published stories by topic.','search/',body,noindex=True))
    for title,text in policy_pages().items():
        path=slug(title)+'/'
        output(path+'index.html',shell(title,title+' for '+CONFIG['name'],path,'<div class="policy reading"><h1>'+title+'</h1>'+text+'</div>'));urls.append(path)
    output('404.html',shell('Page not found','This page could not be found.','404.html','<div class="page-heading"><h1>A little off the beaten path.</h1><p>This page is unavailable.</p><a href="'+link()+'">Return to the front page ↗</a></div>',noindex=True))
    output('assets/search.json',json.dumps([{k:a[k] for k in ['slug','title','summary','category','tags']} for a in ARTICLES]))
    output('assets/ads.json',json.dumps(ADS))
    output('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(URL+'/'+p)+'</loc></url>' for p in urls if p!='search/')+'</urlset>')
    output('robots.txt',f'User-agent: *\n{"Allow: /" if PRODUCTION else "Disallow: /"}\nSitemap: {URL}/sitemap.xml\n')
    output('.nojekyll','')
    print(f'Built {len(ARTICLES)} articles and {len(urls)} routes in {OUT}; production={PRODUCTION}')

def policy_pages():
    email=CONFIG.get('email','')
    contact=f'<a href="mailto:{e(email)}">{e(email)}</a>' if email else 'Our public contact address has not been configured. The publisher must add an editorial contact before launch.'
    notice='<p class="notice">Publisher setup required: adapt this starter policy to your organization, jurisdictions, vendors and actual practices before launch.</p>'
    return {
        'About Us':'<p>The Current is a source-linked publication covering technology, culture, sport, business, lifestyle and world affairs. Our aim is to offer clear context and useful reading.</p><h2>Our editorial process</h2><p>RSS automation collects source headlines and links for our editorial reading list. Editors write original articles, check claims against the source, confirm reuse rights and approve each story before publication. This publishing workflow uses no AI generation. A feed entry is not independent verification.</p><h2>Corrections</h2><p>We welcome specific corrections, supporting sources and the URL of the article involved. Material corrections should be noted on the article with an updated date.</p>',
        'Contact Us':'<p>For editorial questions, corrections, rights requests and advertising inquiries:</p><p>'+contact+'</p><p>Please include the relevant article link and supporting evidence. Do not send confidential information through email.</p>',
        'Privacy Policy':notice+'<p>This static website stores a theme preference and privacy choice in your browser. It has no built-in accounts, tracking analytics or contact database. Hosting providers may process request and security logs under their own policies.</p><h2>Advertising and consent</h2><p>Optional ad scripts are disabled by default. If enabled, the publisher must identify the vendors, their purposes, data categories, retention, international transfers and relevant rights here. Ad vendors may use cookies or similar identifiers only as permitted by applicable consent signals and law.</p><h2>Your choices</h2><p>Use Cookie settings in the footer to change the optional advertising choice. Withdrawing consent reloads the page to stop new ad loads; vendor cookie deletion and data rights requests may require the vendor’s own tools.</p><h2>Contact and rights</h2><p>'+contact+'</p><p>Add the controller’s legal identity, address, lawful bases, retention schedule, regional rights, children’s privacy practices, and complaint channels before public launch.</p>',
        'Terms and Conditions':notice+'<p>Content is offered for general information. You may link to our articles. Reuse of article text and artwork requires permission except where law permits otherwise. Third-party materials remain subject to their owners’ rights.</p><p>Do not interfere with the site, misuse its services or misrepresent its content. External websites operate under their own terms. Add the publisher’s identity, applicable law, consumer protections and dispute procedures after review.</p>',
        'Disclaimer':notice+'<p>Articles provide general information and are not professional financial, medical or legal advice. Sources may update their reporting; publication dates indicate when we published our version.</p><p>Advertisements are labeled and do not constitute editorial endorsement. Editors remain responsible for verification, original writing and source attribution. No traffic, advertising approval or revenue is guaranteed.</p>'
    }

if __name__=='__main__':
    build()
