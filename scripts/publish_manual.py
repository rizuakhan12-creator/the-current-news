"""Prepare one explicitly reviewed article on a branch. Never merge or publish main."""
import os
import re
import subprocess
import sys
from common import ROOT, read, canonical
from review_queue import run, open_review, BRANCH

def main():
    ident = os.getenv('DRAFT_ID', '')
    reviewer = os.getenv('REVIEWER', '')
    if not re.fullmatch(r'[a-f0-9]{20}',ident) or not reviewer.strip():
        sys.exit('A valid draft ID and reviewer are required.')
    if os.getenv('CONFIRM_VERIFIED') != 'true':
        sys.exit('You must explicitly confirm source verification, original writing and reuse rights.')
    branch = f'editorial/{ident}'
    exists = run('git','ls-remote','--exit-code','--heads','origin',branch,check=False)
    if exists.returncode == 0:
        sys.exit(f'{branch} already exists. Review that branch instead of overwriting editorial work.')
    if exists.returncode != 2:
        exists.check_returncode()
    path = ROOT/'content/drafts'/f'{ident}.json'
    if not path.exists():
        run('git','fetch','origin',BRANCH)
        source = run('git','show',f'FETCH_HEAD:content/drafts/{ident}.json')
        path.write_text(source.stdout,encoding='utf-8')
    article = read(path)
    source_urls = {canonical(s['url']) for s in article['sources']}
    for published in (ROOT/'content/articles').glob('*.json'):
        if source_urls.intersection(canonical(s['url']) for s in read(published)['sources']):
            sys.exit('A published article already uses this source. Update that article instead of duplicating it.')
    subprocess.run([sys.executable,str(ROOT/'scripts/approve.py'),ident,'--reviewer',reviewer,'--verified'],cwd=ROOT,check=True)
    run('git','config','user.name','github-actions[bot]')
    run('git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    run('git','switch','-c',branch)
    run('git','add','content/articles','content/drafts')
    run('git','commit','-m',f'editorial: prepare reviewed article {ident}')
    run('git','push',f'--force-with-lease=refs/heads/{branch}:','origin',f'HEAD:refs/heads/{branch}')
    open_review(branch,'Review manually written article',
        f'Prepared after explicit source and rights verification by {reviewer}. Inspect the article before merging to main. No AI generation was used.')

if __name__ == '__main__':
    main()
