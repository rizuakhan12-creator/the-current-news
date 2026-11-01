"""Persist drafts on a fixed review branch; never publish or merge them.

Called by the trusted scheduled workflow after checkout of the default branch.
Requires GH_TOKEN and the GitHub-hosted runner's gh CLI.
"""
import json
import subprocess
import sys
from common import ROOT, read, canonical
import os

BRANCH='automation/news-drafts'

def run(*args, check=True):
    return subprocess.run(args,cwd=ROOT,check=check,capture_output=True,text=True)

def open_review(branch, title, body):
    repository = os.getenv('GITHUB_REPOSITORY', '')
    compare = f'https://github.com/{repository}/compare/main...{branch}?expand=1'
    prs = run('gh','pr','list','--head',branch,'--state','open','--json','number',check=False)
    existing = json.loads(prs.stdout) if prs.returncode == 0 else []
    if not existing:
        result = run('gh','pr','create','--draft','--head',branch,'--title',title,'--body',body,check=False)
        if result.returncode:
            print('Review branch saved. Automatic PR creation is unavailable; use the compare link to open a PR manually.')
    print(f'Review changes: {compare}')
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a',encoding='utf-8') as stream:
            stream.write(f'## {title}\n\n[Review branch and create a pull request]({compare})\n\nNo article was merged or published automatically.\n')

def restore():
    exists=run('git','ls-remote','--exit-code','--heads','origin',BRANCH,check=False)
    if exists.returncode == 2:
        return
    exists.check_returncode()
    run('git','fetch','origin',f'{BRANCH}:refs/remotes/origin/{BRANCH}')
    # Only content files are restored; remote scripts and workflow files are never executed.
    names=run('git','ls-tree','-r','--name-only','FETCH_HEAD','--','content/drafts/').stdout.splitlines()
    published=set()
    for p in (ROOT/'content/articles').glob('*.json'):
        published.update(canonical(s['url']) for s in read(p)['sources'])
    for name in names:
        from pathlib import PurePosixPath
        p=PurePosixPath(name)
        if p.parent != PurePosixPath('content/drafts') or p.suffix != '.json':
            continue
        text=run('git','show',f'FETCH_HEAD:{name}').stdout
        a=json.loads(text)
        if any(canonical(s['url']) in published for s in a['sources']):
            continue
        target=ROOT/name
        if not target.exists(): target.write_text(text,encoding='utf-8')

def save():
    run('git','config','user.name','github-actions[bot]')
    run('git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    existing=run('git','rev-parse','--verify',f'refs/remotes/origin/{BRANCH}',check=False)
    expected=existing.stdout.strip() if existing.returncode == 0 else ''
    run('git','switch','-C',BRANCH)
    run('git','add','content/drafts')
    if run('git','diff','--cached','--quiet',check=False).returncode == 0:
        print('No draft changes.'); return
    run('git','commit','-m','chore: prepare news drafts for editorial review')
    run('git','push',f'--force-with-lease=refs/heads/{BRANCH}:{expected}','origin',f'HEAD:refs/heads/{BRANCH}')
    open_review(BRANCH,'Review RSS leads for manual writing',
        'RSS metadata only; article fields are intentionally empty. Write original copy, verify the linked sources and rights, then use Prepare manual publication or scripts/approve.py. No AI service is used.')
    print('Draft review branch updated. No articles published.')

if __name__=='__main__':
    {'restore':restore,'save':save}[sys.argv[1]]()
