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

def review_image_path(image, root):
    from pathlib import PurePosixPath
    path = PurePosixPath(image)
    if not image.startswith('assets/') or '\\' in image or '..' in path.parts or path.suffix.lower() not in {'.jpg','.jpeg','.png','.webp','.avif','.svg'}:
        raise ValueError('Image must be a local assets path with a supported extension')
    destination = (root/'static'/image).resolve()
    if (root/'static/assets').resolve() not in destination.parents:
        raise ValueError('Image must remain inside static/assets')
    return destination

def copy_review_image(image, ref, root):
    import subprocess
    destination = review_image_path(image, root)
    if destination.is_file():
        return
    result = subprocess.run(['git','show',f'{ref}:static/{image}'],cwd=root,check=True,capture_output=True)
    if not result.stdout or len(result.stdout) > 5_000_000:
        raise ValueError('Review image must be nonempty and at most 5 MB')
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(result.stdout)

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
