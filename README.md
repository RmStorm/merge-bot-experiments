# merge-bot-experiments
Experiments in mergebot technology

Create four independent PRs from the latest `origin/main`, spaced approximately
20 seconds apart:

```bash
python3 scripts/create_experiment_prs.py
```

Requires Git, Python 3, and an authenticated GitHub CLI (`gh`). Commit or stash
tracked changes first. The script fetches and fast-forwards `main`, pushes one
commit per branch, opens each PR against `main`, and returns to `main`. Untracked
files are allowed. It does not add labels or merge PRs. GitHub scheduling may
slightly vary the actual CI start times.

To change the count or interval:

```bash
python3 scripts/create_experiment_prs.py --count 4 --interval 20
```
