# Secrets in repositories

The single most common modern security failure isn't a fancy 0-day — it's a developer who hard-coded `AWS_SECRET_ACCESS_KEY` into a config file, committed it, and pushed to a public repo. Sometimes they notice five minutes later, force-push to "delete" it, and assume the problem is gone. It isn't. Once a secret hits a public Git history, you must treat it as compromised forever — and the fix is to rotate the secret, not rewrite the history.

This module covers how secrets leak, how to find them as a defender (or in a CTF), how to actually scrub them, and how to never leak one again.

---

## Why this module matters

- **It's the most common real-world breach vector for developers.** GitGuardian's annual report logs millions of secrets exposed in public repos each year. Most are real, working credentials.
- **The dollar impact is huge.** Leaked AWS keys typically generate four- or five-figure crypto-mining bills within hours of exposure (scanners watch GitHub's public event stream in real time). Leaked Stripe keys can drain customer accounts. Leaked Slack tokens enable impersonation across an entire organisation.
- **The fix is counter-intuitive.** Developers' instinct is "delete the file and push again." That's the wrong fix. The right fix is rotate-then-scrub, in that order, and treat the secret as burnt.

---

## How secrets leak — the patterns

| Pattern | Example | Why it happens |
|---------|---------|----------------|
| `.env` committed | `DATABASE_URL=postgres://...:hunter2@db.prod.example.com/app` | Devs forget the file is tracked because it's "local" |
| Hard-coded credential in source | `client.connect(api_key="sk_live_4eC39H...")` | Quick fix during development, never cleaned up |
| Test fixture with real key | `tests/fixtures/aws-creds.json` | Copied production creds for testing |
| Private key in repo | `id_rsa`, `*.pem`, `deploy.key` | Sample server config, dev convenience |
| CI / build logs | GitHub Actions echoing `${{ secrets.STRIPE_KEY }}` | Misconfigured `set -x` or `echo`-debugging |
| Docker image layers | Layer adds key, later layer deletes it — but the layer is still there | Devs think `RUN rm secret` removes the layer history |
| Compiled binary | Embedded secret survives `strings binary` | Hard-coded at compile time |
| Public Postman / OpenAPI specs | Examples include real bearer tokens | Documentation copy-paste from a working request |
| Mobile app bundle | Hard-coded in `.apk`/`.ipa` | Misunderstanding of "client-side secret" (there is no such thing) |
| Public Pastebin / gist | Quick debug paste with secret left in | "I'll delete it after" |
| Wayback Machine archive | Snapshot taken while secret was live | Archive doesn't forget |

If a leaked secret can reach the internet, assume it has. The credential should be rotated before you even start thinking about cleanup.

---

## Git's data model — why history is forever

Git stores **every version of every file** as content-addressed blobs in `.git/objects/`. When you `git rm secret.txt` and commit, you create a new commit that doesn't reference the blob, but the blob itself still exists in the object database, reachable by its SHA.

```
commit C1 ── points to ── tree T1 ── contains ── blob "leaked-key"
commit C2 ── points to ── tree T2 ── does not contain blob
                                     ↑
                          (you committed "delete the file" here)
```

`git log` from `C2` doesn't show the file, but:

```bash
git cat-file -p <blob-sha>           # contents still recoverable
git show C1:path/to/secret.txt       # contents still recoverable
git log --all --full-history -- path/to/secret.txt
git fsck --unreachable               # finds blobs no commit references
```

On GitHub specifically: even after you delete a repo, **dangling commits remain accessible by SHA** for an extended period (and forks/clones preserve everything indefinitely). The infamous [Truffle Security writeup on force-push hacks](https://trufflesecurity.com/blog/anyone-can-access-deleted-and-private-repo-data-github) showed that force-pushes do not remove the data — they just make it unreachable through normal navigation. The blob is still in the object database, and anyone who knows the SHA can fetch it.

**Mental model: history is forever. Pretend git was append-only.**

---

## Finding secrets — basic Git archaeology

You don't need fancy tools to start. Three Git commands cover most of the manual hunt:

### `git log` — when did this exist?

```bash
git log --all --full-history -- path/to/secret.env
git log --all -S "AKIA" --source                # search for any commit that added/removed "AKIA"
git log --all --grep "password"                 # search commit messages
```

The `-S` flag (pickaxe) finds commits where the count of a string changed — extremely useful for tracking when a secret was first added and (apparently) removed.

### `git show` — what was the content?

```bash
git show <commit-sha>:path/to/file              # file as of that commit
git show <commit-sha>                           # full diff of the commit
```

### `git rev-list` and `git cat-file`

Walk every object reachable from any branch:

```bash
git rev-list --all | head
git rev-list --all -- path/to/secret.env        # commits touching that path

# Dump a specific blob by SHA
git cat-file -p <blob-sha>

# Find dangling objects (often the smoking gun after a force-push)
git fsck --lost-found
ls .git/lost-found/
```

### Searching every blob

```bash
# Print every blob and grep for a pattern
git rev-list --objects --all \
  | awk '{print $1}' \
  | xargs -I{} git cat-file -p {} 2>/dev/null \
  | grep -E 'AKIA[0-9A-Z]{16}|sk_live_|ghp_'
```

Slow on big repos but works.

> **CTF tip.** The CSOT Week 1 [git-forensics-lite](../../CTFs/week-01/git-forensics-lite/) challenge is exactly this kind of hunt — the flag lives in a commit that was "removed" by a later commit. `git log --all`, find the suspicious SHA, `git show` it.

---

## Automated secret scanners

For real audits and CI integration, you use scanners.

| Tool | Strengths | Notes |
|------|-----------|-------|
| [`trufflehog`](https://github.com/trufflesecurity/trufflehog) | Verifies credentials by hitting the provider's API; deep history scan | Best signal-to-noise; runs in CI |
| [`gitleaks`](https://github.com/gitleaks/gitleaks) | Fast regex-based scanner; pre-commit hook | Great for blocking new commits |
| [`git-secrets`](https://github.com/awslabs/git-secrets) | AWS-focused, pre-commit | Lightweight |
| [GitGuardian](https://www.gitguardian.com/) | Hosted, SaaS, real-time GitHub coverage | Commercial; the company that publishes the annual report |
| GitHub native secret scanning | Built-in for public + paid Advanced Security on private | Free for public repos |

### `trufflehog`

```bash
sudo apt install golang
go install github.com/trufflesecurity/trufflehog/v3@latest

trufflehog git https://github.com/your/repo --only-verified
trufflehog filesystem /path/to/repo --only-verified
trufflehog github --org=your-org --only-verified
```

`--only-verified` is the killer flag — `trufflehog` tries each found candidate against the provider's API and only reports verified-live credentials. Cuts the noise that regex scanners produce.

### `gitleaks`

```bash
go install github.com/gitleaks/gitleaks/v8@latest

gitleaks detect --source . --redact --report-path leaks.json
gitleaks protect --staged                  # pre-commit mode
```

`detect` scans history; `protect` scans the staging area before allowing a commit. Wiring `gitleaks protect` into a `pre-commit` hook stops secrets from ever reaching `main`.

### Pre-commit framework integration

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

Install once with `pre-commit install` and forget about it.

---

## Regexes you can run by hand

When tools aren't available, these regexes cover the most common leakage:

| Pattern | Matches |
|---------|---------|
| `AKIA[0-9A-Z]{16}` | AWS access key ID |
| `(?i)aws(.{0,20})?(secret|access)?(.{0,20})?['"][0-9a-zA-Z/+]{40}['"]` | AWS secret access key |
| `gh[pousr]_[A-Za-z0-9]{36,}` | GitHub PAT / OAuth token |
| `xox[baprs]-[A-Za-z0-9-]{10,}` | Slack tokens |
| `sk_live_[0-9a-zA-Z]{24,}` | Stripe live secret |
| `-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----` | Private key |
| `eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` | JWT |
| `(?i)password\s*=\s*['"][^'"]{4,}['"]` | Generic password assignment |
| `(?i)api[_-]?key\s*=\s*['"][^'"]{8,}['"]` | Generic API key assignment |

```bash
# Quick local scan
grep -rE 'AKIA[0-9A-Z]{16}|gh[pous]_[A-Za-z0-9]{36,}|sk_live_[0-9a-zA-Z]+' . \
  --include='*.{py,js,ts,go,java,yml,yaml,json,env,sh,md}' 2>/dev/null
```

For CTF challenges, the flag itself is the "secret" — `grep -r 'csot26{' .` is the universal hammer.

---

## Removing secrets — the right and wrong ways

### Step 0 — rotate the secret first

This is the only step that matters in the first 60 seconds.

- AWS key → IAM console, deactivate, create replacement, audit `CloudTrail`.
- GitHub PAT → Settings → Developer settings → Personal access tokens → revoke.
- Slack token → App management → reinstall app.
- Database password → admin connection, `ALTER USER ... PASSWORD`.
- Stripe key → dashboard, roll keys.

**Why first:** between the moment the secret was pushed and now, opportunistic scanners may have already pulled it. The clock started ticking the instant the commit hit GitHub. Scrubbing history without rotating is fixing the symptom, not the cause.

### Step 1 — scrub history (with full understanding of what it does)

There are two industry-standard tools:

| Tool | Notes |
|------|-------|
| [`git filter-repo`](https://github.com/newren/git-filter-repo) | Modern, fast, recommended by Git upstream |
| [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) | Slightly older but very ergonomic for "remove this file" |

`git filter-branch` exists in core Git and is **deprecated** — slow and footgun-laden. Use `filter-repo` instead.

```bash
pip install git-filter-repo                # or sudo apt install git-filter-repo

# Remove all instances of a file from every commit
git filter-repo --path config/secrets.env --invert-paths

# Remove specific strings from all blobs
echo 'AKIAIOSFODNN7EXAMPLE==>REMOVED' > replacements.txt
git filter-repo --replace-text replacements.txt
```

After scrubbing:

1. Garbage-collect dangling objects locally: `git reflog expire --expire=now --all && git gc --prune=now --aggressive`.
2. Force-push to the remote: `git push --force-with-lease --all`.
3. Tell every collaborator to re-clone — their local clones still contain the old history, and any push from them will resurrect it.

### Step 2 — accept that the secret is still public

Even after the perfect history rewrite:

- Anyone who cloned/forked the repo before the rewrite has the old history.
- GitHub's caches and any third-party mirrors keep the data.
- The Wayback Machine and code-search engines (GitHub Code Search, [grep.app](https://grep.app/), [sourcegraph](https://sourcegraph.com/search)) often retain content for an extended period.
- Automated secret-mining bots scrape the GitHub events feed within seconds of a public push.

**The secret is burnt the moment it lands in a public repo.** History rewriting is hygiene, not remediation.

> **Gotcha.** If the repo was public and you find a leaked secret, *do not* delete the repo as your first reaction. Deleting removes the public surface but blob data is recoverable from caches/forks/scrapers. Rotate, scrub, audit logs for unauthorized use, then decide what to do about the repo.

---

## Preventing leaks — the developer hygiene checklist

### `.gitignore` and `.env.example`

```bash
# .gitignore
.env
.env.*
!.env.example
*.pem
*.key
id_rsa
id_rsa.pub
.aws/
.npmrc
secrets/
config/local.yml
```

Ship a **`.env.example`** with empty/placeholder values committed:

```ini
# .env.example — copy to .env and fill in
DATABASE_URL=
STRIPE_API_KEY=
SENTRY_DSN=
```

This documents what environment variables exist without leaking values. The real `.env` is `.gitignore`d and never touches version control.

### Global gitignore

Set one once and forget:

```bash
git config --global core.excludesfile ~/.gitignore_global
cat > ~/.gitignore_global <<'EOF'
.env
.env.*
*.pem
*.key
.DS_Store
.idea/
.vscode/
EOF
```

Now even brand-new repos ignore these without you remembering.

### Pre-commit hooks

```bash
pip install pre-commit
cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
EOF
pre-commit install
```

Now any attempt to commit a file with a private key or matching secret regex is blocked locally before it can be pushed.

### Secret managers — what to use instead of `.env` for production

| Tool | Use |
|------|-----|
| **AWS Secrets Manager / SSM Parameter Store** | Cloud-native, IAM-controlled |
| **HashiCorp Vault** | On-prem / multi-cloud |
| **Azure Key Vault**, **GCP Secret Manager** | Cloud-native equivalents |
| **Doppler**, **Infisical**, **1Password Secrets Automation** | Hosted developer-friendly tools |
| **sealed-secrets**, **SOPS** | Encrypted secrets committed to Git (with key escrow) |

For local dev, `.env` is fine — just keep it untracked. For production, fetching secrets at boot from a real manager removes the entire class of "config file with secrets" risk.

### Short-lived credentials

| Long-lived | Short-lived equivalent |
|------------|------------------------|
| AWS access key | IAM role assumption (`sts:AssumeRole`) — minutes-long credentials |
| GitHub PAT | GitHub Actions OIDC token, fine-grained PATs with expiry |
| Database password | IAM database authentication, signed URLs |
| Long JWT signing key | Rotating signing keys (`kid` header), JWKS endpoint |

Short-lived credentials limit the blast radius of leaks: by the time a scanner pulls the key from a public repo, it might already be expired.

---

## CI/CD secret hygiene

CI is where secrets meet developers in interesting ways:

- **Use the platform's native secret store** (GitHub Actions secrets, GitLab CI variables, CircleCI contexts, Vercel project env).
- **Mark sensitive variables as masked** so they get redacted from logs.
- **Avoid `echo`-debugging** anything that contains secrets. `set -x` will print them on the next command.
- **Don't pass secrets via the URL or filename** — they end up in shell history, build caches, audit logs.
- **Audit pull-requests from forks** — forks should not get access to secrets by default. GitHub Actions enforces this; some CIs don't.

### A GitHub Actions example

```yaml
name: deploy
on: { push: { branches: [main] } }
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write       # OIDC, no long-lived secret needed
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/deployer
          aws-region: ap-south-1
      - run: aws s3 sync ./dist s3://example-prod/
```

No `AWS_ACCESS_KEY_ID` anywhere. GitHub mints a short-lived OIDC token, AWS exchanges it for temporary credentials, the job uses those, they expire when the job ends.

---

## A real-world impact checklist

When a leaked secret is found in your repo, this is what an incident-response timeline looks like:

| Time | Action |
|------|--------|
| T+0 | Detect leak (scanner alert, GitHub email, internal find) |
| T+5 min | Rotate the credential at the provider |
| T+10 min | Check provider audit logs for unauthorized use during exposure window |
| T+30 min | Notify affected stakeholders if the secret had production access |
| T+1 hr | Begin history scrubbing in repo + force-push |
| T+2 hr | Notify collaborators to re-clone; audit other repos for the same secret |
| T+1 day | Write postmortem; add gitleaks/trufflehog to CI; add pre-commit hook |
| T+1 week | Tabletop the failure mode in the team; update onboarding to require pre-commit |

In a worst-case AWS-key leak with no rotation, the typical attacker behaviour:

1. Scrape key from the GitHub events feed (seconds).
2. Spin up the largest GPU instances the key allows in every region (minutes).
3. Mine crypto for as long as the key works.
4. You wake up to a multi-thousand-dollar bill.

This has happened to thousands of developers, including very experienced ones. Treat the prevention controls as load-bearing, not optional.

---

## OSINT angle — finding leaks before attackers do

A defender's self-OSINT pass on their own GitHub presence catches many of these:

```bash
# Your own published email — search GitHub for it
gh api -X GET search/code -f q='in:file your@email.com' --paginate

# Trufflehog on every public repo your org owns
trufflehog github --org=your-org --only-verified
```

For CSOT specifically, the [Week 2 OSINT module](../Week-02/osint-techniques.md) covers the broader GitHub-as-OSINT angle. The mental model is the same here: anything *you* can find with public tools, an attacker can find first.

---

## Ethics — same rules as before

| Allowed | Not allowed |
|---------|-------------|
| Scan your own repos | Scanning random people's repos and reporting "findings" without invitation |
| Scan an org you have written authorization for | Joining a bug bounty and exfiltrating data outside the scope |
| Bug bounty within program scope | "I found their key; I'll just look at one S3 bucket" |
| Reporting a leaked secret to the owner via the vendor's security disclosure channel | Using the secret you found, even "just to confirm it works" |

If you find a real leaked secret in a third-party repo: **do not use it**. Report via the vendor's security contact, the repo owner's published security policy, or [GitHub's secret-scanning notification path](https://docs.github.com/en/code-security/secret-scanning).

The IT Act §43 in India treats unauthorized access via a leaked credential the same as unauthorized access via an exploit. Same goes for the CFAA in the US. The credential being on the internet doesn't make using it legal.

---

## Tool / command cheat sheet

```bash
# Local manual hunt
git log --all -S 'AKIA' --source
git show <sha>:path/to/file
git rev-list --all -- path/to/file
git fsck --lost-found

# Pattern matches
grep -rE 'AKIA[0-9A-Z]{16}|gh[pous]_[A-Za-z0-9]{36,}|sk_live_' .

# Automated tools
trufflehog git . --only-verified
gitleaks detect --source . --redact --report-path leaks.json

# Removing
git filter-repo --path secrets.env --invert-paths
git filter-repo --replace-text replacements.txt

# Local hygiene
git config --global core.excludesfile ~/.gitignore_global
pre-commit install
```

---

## Relating this to other modules

| Connection | Where to find it |
|------------|------------------|
| Git-as-forensics archaeology | [digital-forensics.md](digital-forensics.md) — same hunt, same tools, on disk artifacts |
| OSINT-style searching of GitHub for secrets | [Week 2 OSINT module](../Week-02/osint-techniques.md) |
| Why secret hygiene is part of digital safety | [Week 1 — digital-safety.md](../Week-01/digital-safety.md) |
| The CSOT Week 1 git-archaeology lab | [Week 1 CTF — git-forensics-lite](../../CTFs/week-01/git-forensics-lite/) |

The Week 4 CTF doesn't have a dedicated "secrets-in-repo" challenge — the Week 1 git-forensics lab covers that workflow directly, and the other Week 4 challenges (`metadata-leak`, `carved-note`) reuse the same "data was hidden but still recoverable" pattern.

---

## Practice progression

- **Week 1 CTF — [git-forensics-lite](../../CTFs/week-01/git-forensics-lite/)** — practice `git log --all`, `git show`, dangling commits.
- **Set up `pre-commit` + `gitleaks`** on your CSOT repos and your personal projects.
- **Run `trufflehog --only-verified`** on every repo under your GitHub username. Fix anything it finds.
- **TryHackMe** — *git happens*, *github-recon* (community rooms covering secret hunting).
- **HackTheBox / picoCTF** — "search the repo" style challenges in misc/OSINT categories.

---

## Further reading

- [GitHub Docs — Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) — official walkthrough.
- [git-filter-repo manual](https://htmlpreview.github.io/?https://github.com/newren/git-filter-repo/blob/docs/html/git-filter-repo.html) — the canonical scrubbing reference.
- [GitGuardian — State of Secrets Sprawl](https://www.gitguardian.com/state-of-secrets-sprawl-report-2024) — annual report with stats.
- [Truffle Security blog — Anyone can access deleted/private repo data on GitHub](https://trufflesecurity.com/blog/anyone-can-access-deleted-and-private-repo-data-github) — why "force-push" isn't a fix.
- [OWASP — Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) — broader practices.
- [Pre-commit framework docs](https://pre-commit.com/) — language-agnostic hook manager.

---

## Next module

You've reached the last reading module of Week 4. Head back to the [Week 4 README](README.md) for assignments, the weekend CTF table, and links to Week 5.
