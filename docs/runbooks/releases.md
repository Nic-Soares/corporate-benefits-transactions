# Runbook — Branches and releases

A data project with one author: no deploy and no users to protect from a bad
build. A version matters when a dataset is published, so releases are few and
made by hand.

---

## Flow

1. Work on a branch cut from `develop`: `<type>/st-XX.Y-<slug>`, Conventional
   Commits (`feat(simulation): …`), signed. Merge it into `develop` with
   `--no-ff` and a `merge(<scope>): …` commit.
2. When `develop` is ready to publish, merge it into `main` with `--no-ff`
   (`merge(release): …`) and push; CI runs on both branches.
3. A new dataset version (a Kaggle upload) is a release:
   - add its section to `CHANGELOG.md` and set `version` in `pyproject.toml`
     (Semantic Versioning: a change in the data's shape or columns is major,
     new data or columns minor, fixes patch);
   - regenerate the dataset from that commit (`make dataset SCALE=4`): its
     `dataset_metadata.json` records the commit;
   - tag and publish:

```bash
git checkout main && git pull
git tag -s vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

   Then Releases → Draft a new release → the tag, its `CHANGELOG.md` section as
   the notes, and the Kaggle version it matches.

## GitHub settings (once)

| Where | Setting |
|---|---|
| Settings → Rules → Rulesets → New branch ruleset `main` | Target `main`: restrict deletions, block force pushes. The published history can't be rewritten |
| Settings → Code security | Secret scanning and push protection on (free on a public repository) |
| Repository page → About | Topics: `portfolio` (the portfolio site reads `.portfolio/`), `dataset`, `synthetic-data` |

Not used on purpose: Dependabot (updates follow
[`dependency-upgrades.md`](dependency-upgrades.md) when there's a reason),
automated releases (a version only matters with a new dataset), required
pull requests (one author).
