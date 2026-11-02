# Runbook — Branches and releases

How code goes from a branch to a versioned release, and the GitHub settings
that enforce it.

---

## Flow

1. Work on a branch cut from `develop`: `<type>/st-XX.Y-<slug>`, Conventional
   Commits (`feat(simulation): …`), signed.
2. Merge it into `develop` with `--no-ff` and a `merge(<scope>): …` commit, or
   through a pull request to `develop`.
3. A release is a pull request `develop` → `main` with CI green. Merge it with
   **Create a merge commit** (keeps the signed commits).
4. A push to `main` runs **Release** (`.github/workflows/release-please.yml`):
   release-please keeps a PR open on `main` with the next version and
   `CHANGELOG.md`, from the commit types since the last tag — `fix` → patch,
   `feat` → minor, `!` or `BREAKING CHANGE` → major. Merge that PR with
   **Squash and merge** (its own commit is unsigned; the squash commit is
   signed by GitHub): it tags `vX.Y.Z`, publishes the GitHub Release and bumps
   `pyproject.toml`.
5. Merge `main` back into `develop` (`git merge --no-ff origin/main`) so the
   version and the changelog are there too.

`docs`, `refactor`, `test`, `ci`, `chore` and `merge` commits don't make a
release on their own (hidden sections of `.github/release-please-config.json`).

## GitHub settings (once)

| Where | Setting |
|---|---|
| Settings → General | Default branch `main`. Pull requests: allow merge commits and squash merging; automatically delete head branches |
| Settings → Rules → Rulesets → New branch ruleset `main` | Target `main`. Restrict deletions, block force pushes, require a pull request before merging, require status checks to pass: `check` and `secrets` (CI) |
| Settings → Rules → Rulesets → New branch ruleset `develop` | Target `develop`. Restrict deletions, block force pushes (direct pushes stay allowed) |
| Settings → Code security | Secret scanning and push protection on (free on a public repository); Dependabot alerts on |
| Settings → Secrets and variables → Actions | `RELEASE_PLEASE_TOKEN` (below) |
| Repository page → About | Topics: `portfolio` (the portfolio site reads `.portfolio/`), `dataset`, `synthetic-data`, `python`, `duckdb` |

### `RELEASE_PLEASE_TOKEN`

The Release workflow opens its PR with this token instead of `GITHUB_TOKEN`:
PRs opened with `GITHUB_TOKEN` don't trigger other workflows, so CI would never
run on the release PR and the `main` ruleset would block it.

1. https://github.com/settings/personal-access-tokens/new (fine-grained).
2. Name `benefits-release`; resource owner `Nic-Soares`; expiration one year;
   repository access: **Only select repositories → `corporate-benefits-transactions`**.
3. Repository permissions, all **Read and write**: **Contents** (tags,
   releases, the release branch), **Pull requests** (the release PR),
   **Issues** (its `autorelease` labels).
4. Generate, copy into the repository's Actions secret `RELEASE_PLEASE_TOKEN`.

Check: after a push to `main`, Actions → Release passes.

## The first release (v1.0.0)

`CHANGELOG.md` and `.github/release-please-manifest.json` start at `1.0.0`,
written by hand. Tag the release commit on `main` and publish it, so
release-please counts from there:

```bash
git checkout main && git pull
git tag -s v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

Then Releases → Draft a new release → tag `v1.0.0`, title `v1.0.0`, the
1.0.0 section of `CHANGELOG.md` as the notes.
