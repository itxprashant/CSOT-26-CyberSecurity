# OWASP Top 10

The OWASP Top 10 is the closest thing the web security world has to a shared map. It's a community-curated list of the ten broadest categories of web application risk, refreshed every few years from real-world data. Treat it as the conceptual atlas of bug classes: not exhaustive, not a checklist of every CVE, but a structure that makes every vulnerability you'll ever meet easier to slot into the right bucket.

This module walks each category in the **2021 edition** (which is the current one as of writing) — what the category covers, the simplest possible vulnerable code, the exploitation idea, and what a real fix looks like. Where a category lines up with a CSOT lab challenge or a PortSwigger Academy topic, we'll cross-reference. By the end you should be able to look at any new endpoint and ask, "Which of the ten is this most likely to be?"

> **Editions matter.** The 2021 list reordered, merged, and renamed several 2017 categories. Some courses and certifications still teach 2017. We use 2021 because it's current and because the 2017→2021 differences are organizational, not technical — the underlying bug classes are the same.

---

## The list at a glance

| ID | Category | What it covers | Lab challenge |
|----|----------|----------------|---------------|
| **A01** | Broken Access Control | Vertical/horizontal authz, IDOR, forced browsing | [../../CTFs/week-03/idor-profile/](../../CTFs/week-03/idor-profile/), [../../CTFs/week-03/lfi-page/](../../CTFs/week-03/lfi-page/) |
| **A02** | Cryptographic Failures | Weak/no crypto, exposed secrets, bad hashing | — (touched in Week 4) |
| **A03** | Injection | SQL, NoSQL, OS command, LDAP, template, XSS | [../../CTFs/week-03/sqli-login/](../../CTFs/week-03/sqli-login/), [../../CTFs/week-03/xss-search/](../../CTFs/week-03/xss-search/) |
| **A04** | Insecure Design | Whole-feature flaws (no rate-limit, missing recovery checks) | — (conceptual) |
| **A05** | Security Misconfiguration | Defaults, debug enabled, missing headers | [../../CTFs/week-03/http-headers/](../../CTFs/week-03/http-headers/) |
| **A06** | Vulnerable & Outdated Components | Old libraries, unpatched servers | — |
| **A07** | Identification & Authentication Failures | Weak passwords, no MFA, broken session | [../../CTFs/week-03/session-cookie/](../../CTFs/week-03/session-cookie/) |
| **A08** | Software & Data Integrity Failures | Unsigned updates, insecure deserialization, supply chain | — |
| **A09** | Security Logging & Monitoring Failures | Missing logs, missing alerts, leaking secrets to logs | — |
| **A10** | Server-Side Request Forgery (SSRF) | Server fetches an attacker-controlled URL | — (PortSwigger labs) |

We also cover **CSRF** under this module — OWASP demoted it from a top-10 category but the bug class is still everywhere. The CSOT lab has [../../CTFs/week-03/csrf-transfer/](../../CTFs/week-03/csrf-transfer/) for it.

---

## A01 — Broken Access Control

The #1 most common bug class in 2021 data. "Access control" means *checking* whether a user is allowed to do something. When the server forgets, gets it wrong, or trusts the client, you have a broken access control bug.

Three sub-flavors you'll meet constantly:

| Flavor | Example | Test |
|--------|---------|------|
| **Vertical (privilege escalation)** | A regular user reaches `/admin` | Browse the admin URL as a normal user |
| **Horizontal (IDOR)** | User Alice reads Bob's invoice via `/invoice?id=99` | Change the ID in the URL |
| **Missing function-level check** | `DELETE /api/users/5` works even though only admins should | Try the action as a low-privilege user |

### Vulnerable code

```python
@app.route("/user")
def user():
    uid = request.args.get("id", "1")
    return jsonify(load_profile(uid))   # no check that uid == session.user_id
```

This is exactly the lab's `/user` endpoint. There's no concept of "does the requesting session own this profile?" — the ID is trusted because it came over HTTPS.

### Exploitation

```bash
curl http://127.0.0.1:5000/user?id=1
# {"name":"Alice","note":"public"}

curl http://127.0.0.1:5000/user?id=2
# {"name":"Bob","secret":"csot26{insecure_direct_object_reference}"}
```

### Fix

Server enforces ownership for every request:

```python
@app.route("/user")
@require_login
def user():
    uid = request.args.get("id")
    if int(uid) != session["user_id"] and not session.get("is_admin"):
        abort(403)
    return jsonify(load_profile(uid))
```

For directory traversal / LFI (a sibling of IDOR), the lab's `/page` endpoint also belongs here. Server-side allow-listing of filenames beats blacklisting every time.

**CTF tip:** in any web challenge, look for numeric IDs in URLs or JSON bodies. Increment, decrement, swap with `0`, swap with negative numbers, swap with strings — almost any tampering experiment uncovers something.

---

## A02 — Cryptographic Failures

Renamed from 2017's "Sensitive Data Exposure". The category covers everything cryptographic that goes wrong: choosing weak primitives, not using crypto where you should, exposing keys, mishandling salts.

| Bug | Example |
|-----|---------|
| No TLS / mixed content | Login form posts over HTTP |
| Outdated TLS | TLS 1.0/1.1, RC4, NULL ciphers |
| Hard-coded keys | `SECRET = "hunter2"` in source |
| Weak password hashing | `md5(password)` or unsalted `sha1` |
| Predictable randomness | Session IDs from `random.random()` instead of `secrets` |
| Storing passwords reversibly | "We can email you your password" |

### Vulnerable code

```python
import hashlib

def store_pw(pw):
    return hashlib.md5(pw.encode()).hexdigest()
```

MD5 is fast (good for legitimate hashing), unsalted (every "password" maps to the same hash), and computationally cheap (1 billion guesses/sec on a single GPU). A 6-character lowercase password is cracked in under a second.

### Fix

Use a slow, salted, memory-hard hash:

```python
import bcrypt

def store_pw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12))

def verify(pw, stored):
    return bcrypt.checkpw(pw.encode(), stored)
```

Modern alternatives in roughly increasing strength: **bcrypt** → **scrypt** → **argon2id**. Pick one, use the library default cost, never write your own.

For randomness, in Python: `secrets.token_urlsafe(32)` for session tokens, never `random.choice`.

---

## A03 — Injection

Untrusted input ends up in an interpreter as part of a command. The classic OWASP entry. Includes SQL, NoSQL, OS command, LDAP, template, XPath, expression-language, and XSS (which 2021 folded into A03).

### SQL injection — the lab

```python
query = f"SELECT user FROM users WHERE user='{u}' AND pass='{p}'"
row = conn.execute(query).fetchone()
```

Submit `u=admin'-- ` (with a trailing space) and the query becomes:

```sql
SELECT user FROM users WHERE user='admin'-- ' AND pass='whatever'
```

The `--` comments out the rest. You authenticate as admin without knowing the password.

```bash
curl -X POST http://127.0.0.1:5000/login \
  --data-urlencode "u=admin'-- " \
  --data-urlencode "p=anything"
# Welcome admin! csot26{sql_injection_basics}
```

Other payloads worth knowing:

```sql
' OR '1'='1' --                   # universal "true"
' UNION SELECT username, password FROM users--   # data exfil if columns match
'; DROP TABLE users; --           # destructive; do not run on anything real
admin' /*                          # MySQL comment variant
```

### Fix — parameterized queries

```python
row = conn.execute(
    "SELECT user FROM users WHERE user = ? AND pass = ?",
    (u, p),
).fetchone()
```

The driver sends the SQL template and the values separately. No amount of quoting can escape the parameter into the SQL.

### Cross-site scripting (XSS) — also A03

The server reflects an attacker's payload into HTML without escaping.

```python
@app.route("/search")
def search():
    q = request.args.get("q", "")
    return render_template_string(f"<p>Results for: {q}</p>")
```

User-supplied `q` is interpolated into a template *and* the template is **re-rendered server-side** (`render_template_string` is meant for trusted templates only). Submit `q=<script>alert(1)</script>` and the browser runs your script.

```
http://127.0.0.1:5000/search?q=<script>alert(1)</script>
→ csot26{reflected_xss_alert}
```

| Type | Where the payload lives | Persistence |
|------|-------------------------|-------------|
| **Reflected** | URL or POST body, echoed in same response | One-shot per victim click |
| **Stored** | Saved in DB, served to every viewer | Worm potential |
| **DOM-based** | Client-side JS reads `location.hash` and writes it to the DOM | Server never sees it |

Other A03 family members:

- **OS command injection** — `os.system("ping " + user_input)`. Fix: `subprocess.run(["ping", user_input])` with `shell=False`.
- **NoSQL injection** — `User.find({"name": user_input})` where `user_input` is a dict like `{"$ne": null}`. Validate types.
- **Server-side template injection (SSTI)** — Jinja `{{ 7*7 }}` reflects `49`; then you're one step from `__globals__` and RCE.
- **LDAP/XPath/header injection** — same root cause: concatenating untrusted input into a query language.

**Recon pattern:** for every input field, try in order: a single quote `'`, a double quote `"`, a backtick, a backslash, `<script>`, `${7*7}`, `{{7*7}}`. Note which produce errors, syntax shifts, or reflected output. That tells you which interpreter you've reached.

---

## A04 — Insecure Design

This is a whole-feature category, not a coding bug. It covers vulnerabilities that exist because the design itself didn't anticipate misuse — even if every line of code does what it's supposed to.

Examples:

| Feature | Insecure design |
|---------|-----------------|
| Password reset by emailed link | Link never expires, so a leaked email reveals an active reset forever |
| Bulk discount code | No rate limit; attacker tries 1,000,000 codes in an hour |
| Shopping cart | Price field stored in cookie and trusted server-side |
| Login | No lockout, no rate limit, no MFA option |
| Money transfer | No second-channel confirmation for large amounts |

You can't grep for these. You find them by **threat modeling**: walk a feature and ask "What if I use it backwards? What if I use it 1000× a second? What if I'm a different user than expected?"

### A famous real-world example

Snapchat once let you query "is this phone number registered?" by querying an API endpoint with no rate limit. Attackers harvested half the user base's phone numbers — the code worked exactly as designed.

The fix is design-level: don't let unauthenticated callers enumerate, add per-IP and per-account rate limits, add CAPTCHAs to anti-enumeration endpoints, log and alert on anomalous behavior.

---

## A05 — Security Misconfiguration

Boring, common, devastating. The infrastructure or framework is left in an insecure state.

| Misconfiguration | Risk |
|------------------|------|
| Debug mode in production | Stack traces, source code, sometimes RCE |
| Default credentials | `admin:admin` on a router, Jenkins, MongoDB |
| Verbose errors | Stack traces leak DB schema, file paths, framework version |
| Missing security headers | XSS easier; clickjacking; cookies leaked |
| Open cloud storage | S3 bucket, GCS bucket, Azure blob set to public |
| Unused features enabled | Test endpoints, sample apps, admin panels left exposed |
| Directory listing | `/uploads/` returns an HTML index of every file |

### Vulnerable example

The lab's `/login` handler returns the SQLite error verbatim:

```python
except sqlite3.Error as e:
    return f"SQL error: {e}", 500
```

Submit `u=admin'` and you get back:

```
SQL error: unrecognized token: "'"
```

That single character of feedback is enough for an attacker to confirm the injection point.

### Fix

- Catch and log errors server-side.
- Return a generic message to the client (`Something went wrong, code 12345`).
- Disable debug mode.
- Run a header audit (`securityheaders.com` or `curl -I`) and add `CSP`, `HSTS`, `X-Frame-Options`, `Referrer-Policy`.

The lab's [../../CTFs/week-03/http-headers/](../../CTFs/week-03/http-headers/) is a warm-up that asks you to read the headers it returns.

---

## A06 — Vulnerable & Outdated Components

You ship a library with a known CVE. Or you ship a kernel with a known CVE. Or you depend on a transitive package that was unmaintained for three years and just got hijacked.

| Source of risk | What to do |
|----------------|------------|
| Direct dependencies | `pip-audit`, `npm audit`, `cargo audit`, `bundler-audit` weekly |
| Transitive dependencies | The same tools cover these; lockfiles are required |
| Web server / runtime | Subscribe to CVE feeds, keep Docker images current |
| Frontend libraries served from CDNs | Pin to integrity hash (SRI) |

### Real impact

- **Log4Shell (CVE-2021-44228)** — RCE in a logging library, exploited in the wild within hours of public disclosure.
- **Equifax 2017** — Apache Struts CVE-2017-5638, two months unpatched, 147 million records.
- **MOVEit 2023** — SQLi in a file-transfer product, ransomware groups exploited it on 2,000+ orgs.

You don't write the exploit; you inherit it.

### Detection

```bash
pip-audit                              # Python
npm audit                              # Node
trivy fs .                             # multi-language SCA scanner
docker scout cves my-image:latest      # container CVE check
nuclei -t ~/nuclei-templates/cves/     # template-based CVE probes
```

---

## A07 — Identification & Authentication Failures

Renamed from 2017's "Broken Authentication". Covers login, session lifecycle, and identity verification.

| Bug | Example |
|-----|---------|
| No rate limit on login | Hydra runs unimpeded |
| Weak passwords accepted | `"123456"` passes the validator |
| Sessions don't expire | A stolen cookie works forever |
| Session ID predictable | Sequential `session=1`, `session=2`, … |
| MFA bypass | "Forgot device" path skips the second factor |
| Password reset abuse | Reset link reused, never expires, sent to old email |
| Account enumeration | "User not found" vs "Wrong password" reveals which usernames exist |

### Lab example — session cookie

The `/setrole?role=admin` endpoint sets `Cookie: role=admin` with `HttpOnly=false`. JavaScript can read the cookie, so any XSS instantly steals the session. And the role is *just a string in the cookie*, trusted by every subsequent request.

```bash
curl -i "http://127.0.0.1:5000/setrole?role=admin"
# Set-Cookie: role=admin; Path=/
# Role set to admin csot26{weak_session_cookie}
```

### Fix

- Server-side sessions: cookie is an opaque random ID; the role lives in Redis.
- All session cookies: `HttpOnly`, `Secure`, `SameSite=Lax` or `Strict`.
- Session ID at least 128 bits, generated with `secrets.token_urlsafe`.
- Login rate limit (5/min/user, 20/hour/IP) and lockout after N failures.
- Generic error messages (`"Login failed"`, never `"User not found"`).
- MFA available for everyone; required for admins.

---

## A08 — Software & Data Integrity Failures

Untrusted code or data is loaded and executed without integrity checks.

| Bug | Example |
|-----|---------|
| Auto-update without signature check | Attacker MITMs the update channel, ships a backdoor |
| Insecure deserialization | App calls `pickle.loads(user_input)`; attacker sends gadget chain → RCE |
| Unsigned firmware | Hardware accepts any blob with the right size |
| Supply-chain attack | Malicious commit lands in a dependency you pin |

### Vulnerable code

```python
import pickle, base64
@app.route("/restore")
def restore():
    data = base64.b64decode(request.args.get("state"))
    return pickle.loads(data)              # any class with __reduce__ → RCE
```

Pickle, Java serialization (`ObjectInputStream`), and PHP `unserialize()` are the historical landmines. Attacker sends a serialized object whose constructor runs arbitrary code.

### Fix

- Never deserialize untrusted data with format-equals-code formats. Use JSON.
- Sign your auto-update artifacts; verify the signature before installing.
- Use lockfiles and verify package hashes (`pip install --require-hashes`).
- For CI/CD: SLSA framework, signed builds (`cosign`), provenance attestations.

---

## A09 — Security Logging & Monitoring Failures

The bug is the absence of evidence. You can't respond to a breach you can't see.

| Bug | Example |
|-----|---------|
| Login attempts not logged | Brute force succeeds unobserved |
| Logs not centralized | Each server's logs lost when the server dies |
| No alerts | A noisy attacker rings no bells |
| Sensitive data **in** logs | Passwords, tokens, PII end up in plaintext on disk |
| Tamperable logs | Local attacker can `echo > /var/log/auth.log` |

### What good looks like

- Auth events (login success/failure, MFA, password change) logged with user ID, IP, UA, timestamp, correlation ID.
- Logs shipped to a central system (ELK, Loki, CloudWatch, Splunk).
- Anomaly alerts: 100 login failures from one IP in 60s, or successful login from a new country.
- Personal data redacted before logging (tokens, passwords, card numbers).
- Logs are append-only (or signed) and retained per the regulator's requirement.

This is a defender's category, but as a tester you should look for "what would I leave in the logs if I attacked this?" — a thoughtful design preserves that evidence.

---

## A10 — Server-Side Request Forgery (SSRF)

A server fetches a URL controlled by an attacker. The dangerous thing is that the **server** is doing the fetching, so it has access to internal networks the attacker doesn't.

### Vulnerable code

```python
@app.route("/fetch")
def fetch():
    url = request.args.get("url")
    return requests.get(url).text          # no validation of url
```

### Exploitation

```bash
# Probe internal services
curl "http://target/fetch?url=http://127.0.0.1:5000/admin"
curl "http://target/fetch?url=http://192.168.0.1/"

# AWS metadata (catastrophic — gives IAM creds on EC2)
curl "http://target/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/"

# GCP metadata
curl "http://target/fetch?url=http://metadata.google.internal/computeMetadata/v1/" \
     # GCP also requires a header, which SSRF often doesn't let you set

# Bypass naive blacklist
curl "http://target/fetch?url=http://127.0.0.1.nip.io/"        # DNS rebinding
curl "http://target/fetch?url=http://[::1]/"                    # IPv6 loopback
curl "http://target/fetch?url=http://0x7f000001/"               # hex IP
```

The Capital One 2019 breach (106 million records) was an SSRF against `169.254.169.254` from a misconfigured WAF. SSRF is *the* cloud-era bug.

### Fix

- Allow-list of destination hosts. **Never** blacklist.
- Resolve the user-supplied URL yourself and refuse private IP ranges (`10/8`, `172.16/12`, `192.168/16`, `127/8`, `169.254/16`, link-local, etc.).
- Disable HTTP redirects in your fetch client (or re-validate after each redirect).
- For cloud metadata: use IMDSv2 (token-required) on AWS, set the platform's recommended hardening on GCP/Azure.

---

## Bonus — CSRF (Cross-Site Request Forgery)

CSRF was a top-10 category until 2017, when framework-level defenses (anti-CSRF tokens) became table stakes and OWASP rolled it into "Broken Access Control". The bug class is still everywhere on legacy apps.

### The setup

You're logged into bank.com (session cookie set). You then visit evil.com, which contains:

```html
<form action="https://bank.com/transfer" method="POST">
  <input name="amt" value="10000">
  <input name="to"  value="attacker">
</form>
<script>document.forms[0].submit();</script>
```

The browser sends the request to bank.com **with your cookie** because cookies follow the destination, not the origin. The bank sees an authenticated POST from you and transfers the money.

### Lab example

The CSOT `/transfer` endpoint has no CSRF token:

```python
@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if request.method == "GET":
        return '<form method=post action=/transfer>…'
    return f"Transferred! {FLAGS['csrf']}"        # no token check
```

```bash
curl -X POST http://127.0.0.1:5000/transfer -d "amt=100"
# Transferred! csot26{csrf_token_missing}
```

### Fix

| Defense | How it works |
|---------|--------------|
| **CSRF token** | Server generates a random token, embeds in form, checks on POST |
| **SameSite cookie** | `SameSite=Lax` blocks cross-site POSTs by default |
| **Custom request header** | API requires `X-Requested-With: XMLHttpRequest` (only XHR can set it cross-origin if CORS allows) |
| **Origin/Referer check** | Server compares `Origin:` header to its own host |

Modern frameworks (Django, Rails, Flask-WTF) include CSRF tokens by default. Turn them off and you're back in 2008.

---

## Cross-references to the lab

Pin this mental map. When you sit down for the weekend CTF, you'll work through it.

| Bug class | Endpoint | Challenge |
|-----------|----------|-----------|
| SQL injection (A03) | `/login` | [../../CTFs/week-03/sqli-login/](../../CTFs/week-03/sqli-login/) |
| Reflected XSS (A03) | `/search` | [../../CTFs/week-03/xss-search/](../../CTFs/week-03/xss-search/) |
| IDOR / Access control (A01) | `/user?id=` | [../../CTFs/week-03/idor-profile/](../../CTFs/week-03/idor-profile/) |
| Path traversal / LFI (A01) | `/page?name=` | [../../CTFs/week-03/lfi-page/](../../CTFs/week-03/lfi-page/) |
| Weak session cookie (A07) | `/setrole?role=` | [../../CTFs/week-03/session-cookie/](../../CTFs/week-03/session-cookie/) |
| CSRF (A01-bonus) | `/transfer` | [../../CTFs/week-03/csrf-transfer/](../../CTFs/week-03/csrf-transfer/) |
| API injection (A03) | `/api/notes` | [../../CTFs/week-03/api-notes/](../../CTFs/week-03/api-notes/) |
| Header recon (A05) | `/` | [../../CTFs/week-03/http-headers/](../../CTFs/week-03/http-headers/) |

Every one of these maps onto a real-world incident you can search for. The point of the CTF is to make the textbook category feel like a thing you can poke.

---

## How to study this material

1. Read the section. Re-read the vulnerable-code snippet until you can predict the response.
2. Open the lab. Reproduce the exploit with `curl` and again with Burp Repeater.
3. Write the fix yourself — in your head or in a scratch file — and explain why it stops the attack.
4. Look up one CVE that matches the category (e.g., search "CVE SSRF AWS" or "CVE SQL injection Equifax"). Read the postmortem.
5. Move on.

Don't just memorize the list. Memorize the **shape** of each bug — what the code looks like, what the attack looks like, what the fix looks like.

---

## Further reading

- [OWASP Top 10 (2021)](https://owasp.org/Top10/) — official.
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) — defensive references for each category.
- [PortSwigger Web Security Academy](https://portswigger.net/web-security) — guided labs per topic.
- [CWE Top 25](https://cwe.mitre.org/top25/) — Mitre's complementary list, more code-level.
- [HackTricks — Web Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web) — exhaustive offensive playbook.

---

## Next module

[manual-testing.md](manual-testing.md) — translate the bug-class theory into a repeatable, end-to-end methodology for testing a real web app by hand.
