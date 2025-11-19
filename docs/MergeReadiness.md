# Merge Readiness Playbook

This note documents the checks we just ran while trying to understand why the
`codex/add-simuniverse-evidence-corpus-blueprint-g4zfcn` branch could not be
merged into `main`, plus the exact steps required to land the branch on
`main`.

## What went wrong

* The repository checkout inside CI/local environments does not have a remote
  configured, so `git remote -v` prints nothing. Without the `origin`
  definition, commands such as `git fetch origin main` or `git push origin
  work:main` always fail because Git does not know where `main` lives.
* The only local branch is `work`. Running `git branch -a` confirms that there
  is no `main` tracking branch in the checkout, which explains why `git checkout
  main` (a prerequisite for merging) fails.

## Verifying the branch graph

Even though we cannot fetch the remote, the local history shows that `work` is a
strict descendant of the merge commit
`27060942476bbba10584285b0679940bdd3458ef` (the merge of PR #1). We verified the
shape of the graph with the following commands:

```bash
git merge-base work 2706094
git log 2706094..work --oneline
```

Because `work` contains only the new "Wire SimUniverse control plane and metrics
exporter" commit on top of the existing PR #1 merge, merging `work` into
`main`—once `main` is checked out—should be a fast-forward operation with no
conflicts.

## Fix and merge checklist

1. Configure the remote once inside your checkout:
   ```bash
   git remote add origin git@github.com:flamehaven01/Rex-Sim-Universe-Lab.git
   git fetch origin --prune
   ```
2. Create or update the local `main` branch to track the remote branch:
   ```bash
   git checkout -B main origin/main
   ```
3. Rebase or merge the feature branch. Because `work` is already ahead of
   `origin/main`, a fast-forward merge is enough:
   ```bash
   git checkout main
   git merge --ff-only work
   ```
4. Push the updated `main` branch (and optionally keep `work` in sync):
   ```bash
   git push origin main
   git push origin work --force-with-lease  # only if the remote branch needs updating
   ```
5. If the push still fails, double-check that your SSH key has permission to the
   GitHub repository and re-run `git remote -v` to ensure the remote URL is
   correct.

Following this checklist ensures every patch and update currently staged in the
`work` branch lands on `main` with the exact history we validated locally.
