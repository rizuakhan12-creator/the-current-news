import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)

def canonical(url):
    u = urlsplit(url)
    if u.scheme != "https" or not u.hostname or u.username or u.password:
        raise ValueError("Sources must use HTTPS without credentials")
    query = [(k,v) for k,v in parse_qsl(u.query) if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    return urlunsplit((u.scheme, u.netloc.lower(), u.path.rstrip("/") or "/", urlencode(sorted(query)), ""))

def fingerprint(url):
    return hashlib.sha256(canonical(url).encode()).hexdigest()[:20]

def title_key(title):
    return re.sub(r"\W+", "", title.casefold())

def validate(a):
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a["slug"]), "Invalid slug")
    require(a["category"] in read(ROOT / "config/site.json")["categories"], 'Unknown category')
    for key in ("title", "summary", "meta_description", "author", "published_at"):
        require(isinstance(a[key], str) and a[key].strip(), key)
    from datetime import datetime
    require(datetime.fromisoformat(a["published_at"].replace("Z", "+00:00")).tzinfo, "Timezone required")
    require(isinstance(a['paragraphs'], list) and a["paragraphs"] and all(isinstance(p, str) and p.strip() for p in a["paragraphs"]), 'Paragraphs required')
    require(isinstance(a['tags'], list) and all(isinstance(t, str) for t in a['tags']), 'Tags must be strings')
    if a.get('image'):
        require(a.get('image_alt') and a.get('image_credit'), 'Image alt text and credit required')
    require(a["sources"], "At least one source required")
    for source in a["sources"]:
        canonical(source["url"])
        require(source["name"], 'Source name required')
    if not a.get("demo"):
        require(a.get("reviewed_by") and a.get("verified_at"), "Editorial verification required")
