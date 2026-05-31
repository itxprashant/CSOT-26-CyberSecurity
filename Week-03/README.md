# Week 3 — Web application security

Last week you mapped networks from the outside: ports, banners, DNS, OSINT. This week the target narrows to a single port — usually 80 or 443 — and you go *inside* the web app that lives behind it. You'll learn to read HTTP fluently, intercept traffic with Burp, recognize the OWASP Top 10 bug classes when you see them, drive a manual testing methodology end to end, run automated scanners responsibly, and treat JSON APIs and JWTs as their own attack surface.

---

## Why this week matters

Web apps are where most security work actually happens. Every company has a website; almost every company has bugs in it. The OWASP Top 10 categories you'll meet this week — broken access control, injection, broken auth — drive a majority of real-world breaches. Pentesters, bug bounty hunters, AppSec engineers, and red-team operators all spend more time in Burp Suite than in any other tool.

There's also a craft dimension: web security teaches you to **read a request as data**, to predict what the server will do with each byte, and to spot the gap between "what the developer intended" and "what the code actually allows." That mental model — *server can never trust the client* — is the single most useful frame in all of application security, and it applies far beyond the web.

Finally, this is the week where the recon results from Week 2 become *exploits*. The subdomains, ports, banners, and OSINT you collected feed directly into the targets you fuzz, the headers you probe, and the cookies you tamper with. The mental model from Week 2 ("what's out there?") becomes "what's broken in there?"

---

## Learning objectives

By the end of this week, you should be able to:

- [ ] Read and write a raw HTTP request and response from memory
- [ ] Explain the security-relevant Set-Cookie attributes (`HttpOnly`, `Secure`, `SameSite`) and when each matters
- [ ] Install Burp Community, set up the CA, and route a browser through the proxy
- [ ] Use Burp Repeater, Intruder, Decoder, and Match-and-Replace to drive a test session
- [ ] Recognize each OWASP Top 10 (2021) category from a vulnerable code snippet
- [ ] Identify SQL injection, reflected XSS, IDOR, LFI, CSRF, and broken access control in a real app
- [ ] Run `ffuf`, `nuclei`, `sqlmap`, and `nikto` and tell signal from noise in their output
- [ ] Walk an app through the four-phase manual testing methodology (scope → map → test → report)
- [ ] Test a REST API for BOLA, mass assignment, and broken function-level authorization
- [ ] Decode a JWT by hand, identify weak algorithms, and forge an `alg:none` token
- [ ] Distinguish API key vs session vs JWT and pick the right one for a given use case
- [ ] Articulate the legal/ethical line between authorized testing and unauthorized access
- [ ] Complete the Week 3 CTF challenges in a single afternoon

---

## Modules (read in order)

Each module builds on the previous one. Start with the protocol, then the tool, then the bug map, then the methodology and tools that apply it.

| # | Module | What you'll learn | Time estimate |
|---|--------|-------------------|---------------|
| 1 | [http-fundamentals.md](http-fundamentals.md) | HTTP request/response anatomy, methods, status codes, security headers, cookies, redirects, TLS, body formats | 50 min |
| 2 | [burp-suite.md](burp-suite.md) | What Burp is, installing the CA, browser setup, Proxy / Repeater / Intruder workflow, scope, match-and-replace, extensions | 45 min |
| 3 | [owasp-top10.md](owasp-top10.md) | All ten 2021 categories with vulnerable code, exploitation idea, and fixes; CSRF as a bonus | 55 min |
| 4 | [manual-testing.md](manual-testing.md) | Four-phase methodology: scope, map, test each input class, record findings; payload starter list | 45 min |
| 5 | [web-scanning-auditors.md](web-scanning-auditors.md) | `ffuf`/`gobuster`/`feroxbuster`/Nikto/Nuclei/sqlmap/WPScan/ZAP; routing through Burp; ethics of scale | 40 min |
| 6 | [api-security.md](api-security.md) | REST vs GraphQL vs gRPC; OWASP API Top 10 (2023); recon via JS/OpenAPI/mobile; Burp for APIs | 45 min |
| 7 | [jwt-and-apis.md](jwt-and-apis.md) | JWT structure, algorithms, `alg:none`, RS256→HS256 confusion, HMAC brute force, OAuth/OIDC, defenses | 40 min |

**Total reading time:** ~5 hours (spread across Mon–Wed)

---

## Recommended workflow

```
Day 1 (Mon):  Modules 1–2 (HTTP + Burp setup)
              Spin up the lab, confirm Burp intercepts /login traffic
Day 2 (Tue):  Module 3 (OWASP Top 10) — read each category, do the lab endpoint that matches
Day 3 (Wed):  Modules 4–5 (manual testing + scanners)
              Run ffuf + nuclei + sqlmap against 127.0.0.1:5000 through Burp
Day 4 (Thu):  Modules 6–7 (APIs + JWT) + PortSwigger JWT track
Day 5 (Fri):  Polish assignments; PortSwigger Academy labs in remaining gaps
Day 6–7:      Weekend CTF (8 web challenges, 2–3 hours)
```

---

## External practice platforms

PortSwigger Web Security Academy is the single most important external resource for this week. Their labs are free, hand-built, and walked through exactly the way Burp expects you to drive them. If you only do one thing on the side, do PortSwigger.

| Platform | What to do | Link |
|----------|------------|------|
| **PortSwigger Web Security Academy** | Top priority — start with Apprentice paths on SQLi, XSS, Access Control, CSRF, JWT | [portswigger.net/web-security](https://portswigger.net/web-security) |
| TryHackMe | "OWASP Top 10 (2021)" room — companion to module 3 | [tryhackme.com/r/room/owasptop102021](https://tryhackme.com/) |
| TryHackMe | "Web Fundamentals" path — gentler intro for module 1 | [tryhackme.com](https://tryhackme.com/) |
| TryHackMe | "Burp Suite: The Basics" / "Burp Suite: Repeater" / "Burp Suite: Intruder" | [tryhackme.com](https://tryhackme.com/) |
| HackTheBox | Starting Point Tier 0–1, then easy "Web" machines | [hackthebox.com](https://www.hackthebox.com/) |
| picoCTF Gym | "Web Exploitation" category | [play.picoctf.org/practice](https://play.picoctf.org/practice) |
| OWASP Juice Shop | Self-hosted vulnerable shop — runs anywhere Docker runs | [owasp.org/www-project-juice-shop](https://owasp.org/www-project-juice-shop/) |
| Google Gruyere | Classic Google-hosted vulnerable web app | [google-gruyere.appspot.com](https://google-gruyere.appspot.com/) |
| Hack The Box Academy | Free modules in the "Bug Bounty Hunter" path | [academy.hackthebox.com](https://academy.hackthebox.com/) |

---

## Lab network

A small Flask app provides every endpoint you need to practice this week. It binds only to `127.0.0.1`, so you can attack it freely from your own machine.

```bash
cd CTFs/week-03/_infra
sudo docker compose up -d --build
```

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) — you'll see a list of vulnerable endpoints.

| Service | URL | Used by |
|---------|-----|---------|
| `webapp` (intentionally vulnerable Flask app) | `http://127.0.0.1:5000` | Every CTF challenge this week |

Endpoints exposed (each maps to a CTF):

| Endpoint | Bug class | Challenge |
|----------|-----------|-----------|
| `GET /` | (warmup, headers) | [../../CTFs/week-03/http-headers/](../../CTFs/week-03/http-headers/) |
| `POST /login` | SQL injection | [../../CTFs/week-03/sqli-login/](../../CTFs/week-03/sqli-login/) |
| `GET /search?q=` | Reflected XSS | [../../CTFs/week-03/xss-search/](../../CTFs/week-03/xss-search/) |
| `GET /user?id=` | IDOR / Broken access control | [../../CTFs/week-03/idor-profile/](../../CTFs/week-03/idor-profile/) |
| `GET /page?name=` | Path traversal / LFI | [../../CTFs/week-03/lfi-page/](../../CTFs/week-03/lfi-page/) |
| `GET /setrole?role=` | Weak session cookie | [../../CTFs/week-03/session-cookie/](../../CTFs/week-03/session-cookie/) |
| `POST /transfer` | CSRF | [../../CTFs/week-03/csrf-transfer/](../../CTFs/week-03/csrf-transfer/) |
| `POST /api/notes` | API JSON injection / mass assignment | [../../CTFs/week-03/api-notes/](../../CTFs/week-03/api-notes/) |

Stop the lab when you're done:

```bash
sudo docker compose down
```

**Important:** the lab binds only to loopback. You can attack it from your own machine all day. Do not point any of these techniques at anything else without written authorization.

---

## Assignments (practice — not scored)

Complete these to reinforce the modules before the weekend CTF. **Only CTF flags are scored.**

1. **Burp environment ready.** Take a screenshot of Burp's HTTP history showing at least 10 requests against `http://127.0.0.1:5000` with the Burp CA installed (no HTTPS cert warnings on your browser when intercepting). Confirm the proxy works for both `curl --proxy http://127.0.0.1:8080` and your browser.

2. **OWASP Top 10 mini-writeups.** Pick **five** of the OWASP 2021 categories. For each, write 4–6 sentences covering: (a) what the bug is, (b) a vulnerable code snippet, (c) the lab endpoint or PortSwigger lab that demonstrates it, and (d) the one-line fix. Submit as `owasp-writeups.md`.

3. **PortSwigger Academy track.** Complete **at least 5** Apprentice-level labs across SQL injection, XSS, Access Control, CSRF, and JWT (one per category). Submit a short table: lab name, technique used, payload, response excerpt that proved success.

4. **Manual testing report on the CSOT lab.** Apply the four-phase methodology from [manual-testing.md](manual-testing.md) to `127.0.0.1:5000`. Submit a one-page Markdown report containing at least three confirmed findings with Title, Endpoint, Repro (curl + Burp request), Impact, Fix. The eight CTF flags are evidence you found the bugs — but the report must explain each finding, not just list flags.

---

## Weekend CTF

**Location:** [../../CTFs/week-03/](../../CTFs/week-03/)  
**Challenges:** 8 (all web)  
**Duration:** 2–3 hours  
**Format:** Jeopardy-style, individual  
**Lab:** docker-compose at [../../CTFs/week-03/_infra/](../../CTFs/week-03/_infra/) — `http://127.0.0.1:5000`

| Challenge | Category | Points | Skills tested |
|-----------|----------|--------|---------------|
| [http-headers](../../CTFs/week-03/http-headers/) | Web / Recon | 100 | `curl -I`, reading response headers |
| [csrf-transfer](../../CTFs/week-03/csrf-transfer/) | Web | 150 | POST without CSRF token, replay with curl |
| [idor-profile](../../CTFs/week-03/idor-profile/) | Web / Access control | 200 | Increment `id=` parameter, Burp Repeater |
| [xss-search](../../CTFs/week-03/xss-search/) | Web / Injection | 200 | Reflected XSS payload in `?q=` |
| [session-cookie](../../CTFs/week-03/session-cookie/) | Web / Auth | 200 | Tamper `role` cookie / hit `/setrole?role=admin` |
| [api-notes](../../CTFs/week-03/api-notes/) | Web / API | 250 | JSON mass assignment, unexpected keys |
| [lfi-page](../../CTFs/week-03/lfi-page/) | Web / Access control | 250 | Special-case file via `/page?name=` |
| [sqli-login](../../CTFs/week-03/sqli-login/) | Web / Injection | 250 | Authentication bypass via SQL comment |

**Total available:** 1600 points

**Tips for success:**

- Read each challenge's `README.md` for description and hints.
- Start the lab once (`docker compose up -d --build`) and leave it running for the whole CTF.
- Default flag format is `csot26{...}`. Submit exactly what the response gives you.
- Most challenges are one-or-two-line `curl` or one-click-in-Burp. If you find yourself writing a long script, you're probably overcomplicating.
- Capture every successful request in Burp HTTP history — you'll need it for the assignment report.
- The eight challenges cover the eight bugs in the lab app, in roughly increasing difficulty.

---

## Key concepts to remember

| Concept | Why it matters this week |
|---------|-------------------------|
| Server can never trust the client | The single most important sentence in web security |
| Cookie attributes (`HttpOnly`, `Secure`, `SameSite`) | Set them and most XSS/CSRF damage disappears |
| Parameterized queries | The fix for ~all SQL injection, in one line |
| Output encoding by context | HTML, JS, URL, attribute — each needs a different escape |
| BOLA (per-object authz) | Owns the API security top spot, easy to find by hand |
| `alg:none` | First thing to try on any JWT |
| Allow-list, never deny-list | Path traversal, SSRF, file upload — same lesson |
| `set -euo pipefail` for scripts | Carryover habit from Week 2 |
| Authorization first | Every command in this week is fine on `127.0.0.1:5000` and illegal on anything else |
| Verify before reporting | A scanner finding is a lead, not a bug |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Burp shows "Your connection is not private" | Install Burp's CA: browse to `http://burp` while proxied, import `cacert.der` into Firefox/Chromium/OS trust store |
| `curl: (60) SSL certificate problem` through Burp | Pass `-k` to ignore the cert (only safe for local lab) |
| `curl` doesn't follow a redirect | Add `-L`; check what's in `Location:` first if the redirect looks suspicious |
| Browser proxied through Burp, nothing in history | Scope likely set to a different host; widen scope or disable the filter |
| `docker compose up` fails with "port already in use" | Something else is on 5000; `sudo lsof -i :5000` to find it, or edit the compose file |
| Intercept ON, browser stuck | You're blocking your own traffic — switch Intercept OFF and use HTTP history |
| Intruder painfully slow | Community Edition is throttled; use `ffuf` for raw speed and Intruder for surgical fuzz |
| Encoding issues (`%`, `+`, `&` getting eaten) | Use `curl --data-urlencode` instead of `-d` for tricky payloads |
| JWT base64 won't decode | Add `==` padding back, swap `-_` for `+/` first |
| sqlmap "the back-end DBMS is …" then nothing | Increase `--level` and `--risk` (with permission), or you've already confirmed and need to add `--dump` |
| Lab page shows but `/api/notes` returns the SQLite error | The Flask app sometimes needs `init_db()`; restart the container |

---

## Advanced Reading

For those who want to go deeper this week:

### Books

- *The Web Application Hacker's Handbook* — Stuttard & Pinto — classic web security reference
- *Bug Bounty Bootcamp* — Vickie Li — practical web finding and reporting
- *Real-World Bug Hunting* — Peter Yaworski — case studies from HackerOne

### Online courses / paths

- [PortSwigger Web Security Academy](https://portswigger.net/web-security) — complete all Apprentice and Practitioner labs
- [HackTheBox Academy — Bug Bounty Hunter](https://academy.hackthebox.com/)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

### Tools to explore

- [ffuf](https://github.com/ffuf/ffuf) · [nuclei](https://github.com/projectdiscovery/nuclei) — fast fuzzing and templated scanning
- [Caido](https://caido.io/) · [mitmproxy](https://mitmproxy.org/) — alternative intercept proxies
- [sqlmap](https://sqlmap.org/) — automated SQLi (authorized targets only)

### Challenge platforms

- [Google Gruyere](https://google-gruyere.appspot.com/)
- [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/)
- [HackTheBox — Web category](https://www.hackthebox.com/) easy machines

### Videos / creators

- [STÖK](https://www.youtube.com/c/STOKfredrik) — bug bounty methodology
- [PwnFunction](https://www.youtube.com/c/PwnFunction) — animated web vuln explanations

### Certifications (optional)

- **PortSwigger certifications** (BSCP path) — web-focused, hands-on
- **eWPT** — web penetration testing entry credential

---

## What's next

Week 4 takes the **trust questions** that JWTs raised — "what does it mean for something to be signed?" — and goes deep on the mathematics underneath. You'll cover hashing, symmetric/asymmetric encryption, real-world weak crypto patterns, and then forensics: recovering data and reconstructing timelines after an incident has already happened.

**Next:** [Week 4 — Cryptography & forensics](../Week-04/)
