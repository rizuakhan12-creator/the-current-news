"""Run locally after checking every claim against the linked source."""
import argparse
from datetime import datetime, timezone
from common import ROOT, read, write, validate

parser = argparse.ArgumentParser()
parser.add_argument("id")
parser.add_argument("--reviewer", required=True)
parser.add_argument("--verified", action="store_true", required=True,
                    help="Attest that claims, attribution, source rights and image rights were checked")
args = parser.parse_args()
if not __import__('re').fullmatch(r"[a-f0-9]{20}", args.id):
    parser.error("Use the 20-character draft filename ID")
path = ROOT / "content/drafts" / f"{args.id}.json"
article = read(path)
if article.get('status') != 'draft':
    parser.error('Only a pending draft can be approved')
if article.get("needs_more_reporting"):
    parser.error("Resolve verification_notes and set needs_more_reporting=false after additional reporting")
if not args.reviewer.strip():
    parser.error("Reviewer name required")
now = datetime.now(timezone.utc).isoformat()
article.update(status="published", reviewed_by=args.reviewer.strip(), verified_at=now, published_at=now)
validate(article)
destination = ROOT / "content/articles" / f"{article['slug']}.json"
if destination.exists():
    parser.error("Article already exists")
write(destination, article)
path.unlink()
print(f"Approved {destination.name}. Review the diff and merge through a pull request.")
