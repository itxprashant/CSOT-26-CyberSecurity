# Web scanning and auditors

You can't manually click through 10,000 paths or hand-craft 5,000 SQL payloads. Automation exists because some of the work is mechanical, repetitive, and benefits from raw throughput. The pitfall is treating scanners like answers instead of leads — a scanner says "this might be vulnerable" and a human confirms (or refutes) every finding. This module covers the tools that complement the manual workflow from the previous module, what each one is good for, the ethical guardrails that come with running them at scale, and how to bolt their output back into your evidence trail.

The single biggest mental shift this module asks for: a scanner is **noise generation**. It hits the target hundreds or thousands of times per second, fills logs, triggers alerts, and pays no attention to whether the target is your authorized lab or someone's production payment system. The legal and operational responsibility for that noise sits with the person who ran the tool.

> **Hard rule.** Every command in this module is fine against `127.0.0.1:5000` (the CSOT lab), TryHackMe/HackTheBox boxes you're connected to, and PortSwigger Academy instances. Every command is illegal against anything else without **written** authorization. The IT Act §43/§66 makes no distinction between manual unauthorized testing and automated unauthorized testing.

---

## The scanner taxonomy

| Class | Examples | What they do |
|-------|----------|--------------|
| **Directory / content discovery** | `ffuf`, `gobuster`, `feroxbuster`, `dirsearch` | Brute-force paths and files from a wordlist |
| **General vulnerability scanner** | Nikto, OWASP ZAP, Nuclei | Probe for known classes of bugs and misconfigurations |
| **CMS / framework specific** | WPScan, JoomScan, droopescan | Deep enumeration of a specific platform |
| **Targeted exploit tools** | sqlmap, XSStrike, Commix | Confirm and weaponize a specific vuln class |
| **Recon assemblers** | ProjectDiscovery suite (`subfinder`, `httpx`, `katana`), Amass | Combine many sources into an attack-surface map |
| **Header / TLS auditors** | `testssl.sh`, `sslyze`, `securityheaders.com` | Score the deployment posture |

You won't use every tool in every engagement. Build a small kit you understand well; reach for new ones when the kit doesn't fit.

---

## Directory and content discovery

The first automation you'll run on any web target. Every URL you didn't see in the link graph could be admin, debug, or legacy code.

### `ffuf` — the fastest, most flexible

```bash
ffuf -u http://127.0.0.1:5000/FUZZ \
     -w /usr/share/seclists/Discovery/Web-Content/common.txt \
     -mc 200,301,302,401,403 \
     -fs 0 \
     -t 40
```

| Flag | Meaning |
|------|---------|
| `-u` | URL with `FUZZ` marker (can be anywhere — path, query, header, body) |
| `-w` | Wordlist |
| `-mc` | Match these status codes |
| `-ms` | Match these response sizes |
| `-fc` | Filter out these status codes |
| `-fs` | Filter out these response sizes (kill the 404 default page) |
| `-fw` | Filter by word count |
| `-t` | Threads (default 40; back off on production) |
| `-recursion` | Recurse into discovered directories |
| `-recursion-depth` | Limit recursion |
| `-o file.json -of json` | Save results for later |

The most common ffuf pattern: figure out the 404 length, then `-fs` it so only "real" hits show up.

```bash
curl -so /dev/null -w '%{size_download}\n' http://127.0.0.1:5000/__nonexistent__
# → 232      (the 404 page is 232 bytes)

ffuf -u http://127.0.0.1:5000/FUZZ \
     -w common.txt \
     -fs 232
```

ffuf can also fuzz parameters, headers, and request bodies. Same `FUZZ` keyword:

```bash
ffuf -u http://127.0.0.1:5000/user?FUZZ=1 \
     -w params.txt -fs 232           # find hidden GET params

ffuf -u http://127.0.0.1:5000/api/notes \
     -X POST -H 'Content-Type: application/json' \
     -d '{"title":"x","FUZZ":"admin"}' \
     -w json-keys.txt -fc 200        # find unexpected accepted keys
```

### `gobuster` — simpler, less flexible

```bash
gobuster dir -u http://127.0.0.1:5000 \
             -w /usr/share/wordlists/dirb/common.txt \
             -t 40 \
             -x php,html,txt
```

`gobuster` is friendlier on the CLI but slower than `ffuf` and lacks ffuf's recursion controls. Good when ffuf's flag jungle feels heavy.

### `feroxbuster` — recursive by default

```bash
feroxbuster -u http://127.0.0.1:5000 -w common.txt -t 40
```

Recursion is built in and on by default. Add `--no-recursion` if you want a single-level scan. Excellent ergonomics for "scan everything you find."

### `dirsearch` — older, still widely cited

```bash
dirsearch -u http://127.0.0.1:5000 -e php,html,txt -t 40
```

Same job. `dirsearch` is Python-based and integrates well into older toolchains; the new mainstream is ffuf and feroxbuster.

### Wordlists matter more than the tool

The single biggest determinant of results is your wordlist. Standard sources:

- [SecLists](https://github.com/danielmiessler/SecLists) — `Discovery/Web-Content/`. Pre-built lists for common stacks (PHP, IIS, AWS, Spring Boot).
- [Assetnote wordlists](https://wordlists.assetnote.io/) — keyword-mined from real-world data.
- [Jhaddix all.txt](https://gist.github.com/jhaddix/) — long-time bug-bounty favorite for content discovery.

Pick a list for the target's stack. A wordlist of Java endpoints against a Rails app is wasted time.

---

## Subdomain and vhost enumeration

Same idea as directory brute-force, applied to DNS or the `Host:` header.

```bash
# Subdomain DNS brute-force
ffuf -u http://FUZZ.example.com -w subdomains.txt -mc 200,301,302 -fs 0

# Vhost brute-force (same IP, different Host header)
ffuf -u http://target -H 'Host: FUZZ.example.com' \
     -w subdomains.txt -fs 232 -mc all
```

Pair with passive sources from Week 2 — `subfinder`, `crt.sh`, `amass`. The passive sources give breadth; the active brute force fills in what wasn't logged anywhere.

---

## Nikto — the venerable misconfig finder

Nikto is old, slow, and chatty, but it remains a useful baseline scanner for "what dumb stuff is on this server?"

```bash
nikto -h http://127.0.0.1:5000/

# Through Burp so you can inspect the requests
nikto -h http://127.0.0.1:5000/ -useproxy http://127.0.0.1:8080
```

What it finds: outdated server versions, missing security headers, default CGI scripts, debug endpoints, common admin URLs. What it doesn't find: anything modern or business-logic-aware. Treat Nikto's output as a starting point — almost every finding needs manual verification, and false positives are common.

---

## Nuclei — template-based scanning

Nuclei is the modern successor to Nikto. Instead of a hard-coded test suite, it has thousands of community-maintained YAML templates: "if you see X, report Y."

```bash
nuclei -u http://127.0.0.1:5000/ \
       -t ~/nuclei-templates/ \
       -severity medium,high,critical
```

| Flag | Meaning |
|------|---------|
| `-u` | Single URL |
| `-l urls.txt` | Multiple URLs |
| `-t path/` | Template directory |
| `-tags cve,exposure` | Only templates with these tags |
| `-severity` | Filter |
| `-rl 50` | Rate limit (rps) |
| `-proxy http://127.0.0.1:8080` | Route via Burp |
| `-o results.txt` | Save results |

The template repo at [github.com/projectdiscovery/nuclei-templates](https://github.com/projectdiscovery/nuclei-templates) ships ~6,000+ checks across CVEs, misconfigurations, exposed panels, default credentials, technology detection, and weak crypto. It's the closest thing the open-source world has to a curated, modern scanner.

Templates are YAML — you can write your own:

```yaml
id: csot-debug-endpoint
info:
  name: CSOT debug endpoint
  author: you
  severity: high
http:
  - method: GET
    path:
      - "{{BaseURL}}/__debug__"
    matchers:
      - type: word
        words:
          - "Werkzeug"
          - "Traceback"
      - type: status
        status: [200]
```

The "yaml-not-code" model means new CVE checks ship within hours of disclosure.

---

## sqlmap — confirm and exploit SQLi

`sqlmap` is the most powerful, and most easily-misused, web exploitation tool. Use only on targets you have **explicit** authorization for. It will hammer the database with thousands of payloads and is loud enough to wake up any half-alert defender.

```bash
# Confirm injection only (no exploit)
sqlmap -u "http://127.0.0.1:5000/login" --data="u=admin&p=test" \
       --batch --level=2 --risk=1 \
       --proxy=http://127.0.0.1:8080

# Once confirmed: enumerate
sqlmap -u "..." --data="..." --dbs                  # list databases
sqlmap -u "..." --data="..." -D users --tables       # tables in users db
sqlmap -u "..." --data="..." -D users -T accounts --dump   # dump table

# Test a captured Burp request from a file
sqlmap -r request.txt --batch
```

| Flag | Meaning |
|------|---------|
| `-u`, `--data`, `--cookie` | Where to inject |
| `-r request.txt` | Use a saved Burp request as the template |
| `--batch` | Non-interactive (accept defaults) |
| `--level` | Test depth (1–5) |
| `--risk` | Riskier payloads (1–3); 3 includes UPDATEs |
| `--dbs`, `--tables`, `--dump` | Progressive enumeration |
| `--proxy` | Log through Burp |
| `--tamper=between,space2comment,…` | WAF-evasion payload mangling |

**Strong warning:** even on authorized targets, `--risk=3` can include `UPDATE`/`DELETE` payloads. Default is fine for confirmation. Read what each flag does before you turn it up.

The CSOT lab's `/login` is the canonical confirmed-injection target. Run sqlmap against it once to see the dance: blind boolean confirm → time-based confirm → enumeration. Then read [HackTricks' SQLi page](https://book.hacktricks.xyz/pentesting-web/sql-injection) to understand what sqlmap is doing under the hood.

---

## wfuzz — the older fuzzer

`wfuzz` predates `ffuf` and has very similar syntax. Many tutorials still reference it.

```bash
wfuzz -w wordlist.txt -u http://target/FUZZ
wfuzz -c -z file,users.txt -z file,passwords.txt \
      -d "user=FUZZ&pass=FUZ2Z" --hc 401 http://target/login
```

Capabilities mostly overlap with ffuf; ffuf is faster and the docs are clearer. Knowing `wfuzz` exists is useful for reading older write-ups.

---

## WPScan — WordPress-specific

About 40% of the public web runs WordPress. A WPScan run is mandatory if you find one in scope.

```bash
wpscan --url http://target --enumerate u,p,t        # users, plugins, themes
wpscan --url http://target --enumerate vp           # vulnerable plugins only
wpscan --url http://target --usernames admin --passwords rockyou.txt   # brute force
```

WPScan needs an [API token](https://wpscan.com/api) for full CVE data — free tier is enough for personal use.

---

## OWASP ZAP — the open-source alternative to Burp

ZAP is what you reach for when you want an open-source alternative to Burp or you need an automatable scanner.

```bash
# Quick passive baseline
zap-baseline.py -t http://127.0.0.1:5000/ -r baseline.html

# Full active scan (loud)
zap-full-scan.py -t http://127.0.0.1:5000/ -r full.html

# As an interactive proxy GUI
zaproxy &
```

ZAP's active scanner is genuinely free (Burp's is Pro-only) and runs as a daemon you can drive from CI. The UI is bulkier than Burp's, but for headless automation ZAP wins.

---

## Routing scanners through Burp

One pattern that pays off every time: point your scanner at Burp's proxy. Every request the scanner sends, you see in Burp's HTTP history, ready to replay or pivot from.

```bash
# Convention: Burp listens on 127.0.0.1:8080
ffuf      ...  -x http://127.0.0.1:8080
nuclei    ...  -proxy http://127.0.0.1:8080
sqlmap    ...  --proxy=http://127.0.0.1:8080
nikto     ...  -useproxy http://127.0.0.1:8080
gobuster  ...  --proxy http://127.0.0.1:8080

# curl too — works for any HTTPS target if you trust Burp's CA
curl --proxy http://127.0.0.1:8080 -k https://target/path
```

When the scanner reports something interesting, you don't have to rerun the scanner to investigate — the request is already in your Burp history, ready to throw to Repeater.

---

## Cost-of-scanning math

Automation amplifies whatever you do. A scanner with 40 threads firing at 50 rps does 2000 requests/sec. That's:

- **120,000 requests/minute** — most production WAFs alert at much less.
- A few thousand log lines per second filling someone's disk.
- Visible spikes in CPU and bandwidth graphs.
- Often triggers anti-bot platforms (Cloudflare, Akamai) into challenge or block.
- Frequently violates the target's ToS even when "scanning" itself would be legal.

**Default behavior should be slow.**

| Tool | Default rate limit | Suggested ceiling |
|------|--------------------|-------------------|
| `ffuf` | 40 threads (~200rps) | `-t 10 -p 0.2` (rate-limit with delay) on shared targets |
| `nuclei` | 150 templates × concurrency | `-rl 50 -c 25` |
| `sqlmap` | Several req/s during enumeration | `--delay=1 --threads=1` |
| `nikto` | Sequential, slow | Already polite |
| `gobuster` | 10 threads | Lower for production |

If the target has a stated rate limit (often in `/robots.txt` comments, bug-bounty policy, or terms of service), honor it.

---

## Reading scanner output without lying to yourself

A scanner produces three kinds of findings:

| Class | Example | Action |
|-------|---------|--------|
| **True positive** | "SQL syntax error" returned by `'` injection | Manually confirm and exploit |
| **False positive** | "Reflected XSS" because the scanner saw its payload echoed in a search log nobody renders | Discard with reasoning written down |
| **Information leak** | "Server: nginx 1.18.0" header | Note, but rarely a finding on its own |

**Verify everything before reporting.** Two reasons:

1. **Credibility** — one false positive in a real client report destroys trust in the rest of it.
2. **Liability** — telling a company "you have a critical SQL injection in /search" when you don't is the kind of thing that ends consulting relationships.

A useful habit: write the manual repro into your notes *before* you trust the scanner result. If you can't reproduce by hand, the finding isn't real (or your tool is doing something the docs don't say).

---

## Connecting scanner output to manual investigation

Scanners are at their best when they hand you 5 leads and you spend 50 minutes per lead. Workflow:

```
1. Run a directory brute force.
2. Pick the 3 most interesting paths (admin, debug, backup).
3. Browse each one manually in Burp's browser.
4. Send the most promising request to Repeater.
5. Apply the manual-testing methodology to that endpoint.
6. Go back to the scanner output and pick the next lead.
```

You'll use Nuclei/sqlmap/ZAP in the same way: find candidates, verify by hand, exploit by hand or with the tool's exploit mode under supervision.

---

## A reproducible scan workflow on the lab

```bash
# Start the lab
cd CTFs/week-03/_infra
sudo docker compose up -d --build

# Tab 1: Burp running on 127.0.0.1:8080

# Tab 2: directory brute force via Burp
ffuf -u http://127.0.0.1:5000/FUZZ \
     -w /usr/share/seclists/Discovery/Web-Content/common.txt \
     -mc 200,301,302,401,403 -fs 0 \
     -x http://127.0.0.1:8080 \
     -o ffuf.json -of json

# Tab 3: Nuclei baseline
nuclei -u http://127.0.0.1:5000/ \
       -t ~/nuclei-templates/ \
       -severity medium,high,critical \
       -proxy http://127.0.0.1:8080 \
       -o nuclei.txt

# Tab 4: Nikto for misconfig sanity
nikto -h http://127.0.0.1:5000/ -useproxy http://127.0.0.1:8080 -output nikto.txt

# Tab 5: confirmed-SQLi exploit walkthrough
sqlmap -u "http://127.0.0.1:5000/login" \
       --data="u=admin&p=test" \
       --batch --level=2 --risk=1 \
       --proxy=http://127.0.0.1:8080
```

Save artifacts the same way you saved nmap output last week. The recon-automation directory layout from Week 2 generalizes directly — `01-ffuf/`, `02-nuclei/`, `03-sqlmap/`.

```bash
sudo docker compose down
```

---

## Defenders run the same tools

Everything in this module is also a blue-team tool. Defensive use looks identical to offensive use, just inside your own perimeter and on a schedule:

- **Nuclei** in CI on every staging deploy with the `cves` and `default-logins` tags.
- **ZAP baseline scan** as a GitHub Action against PR previews.
- **WPScan** scheduled weekly against any WordPress you operate.
- **`testssl.sh`** in monitoring to alert on cert expiry and downgraded TLS.
- **Nikto/Nuclei** post-deploy smoke tests catching "we forgot to disable debug mode."

The same Nuclei template that confirms a CVE for an attacker confirms the patch for the defender. Tools are neutral; intent and authorization are not.

---

## Ethics, one more time

Read this section twice if you skipped the introductions.

- A scanner does not "ask permission". It hits whatever you point it at. **You** are responsible.
- Bug bounty programs often have explicit rules: no automated scanners, or scanners with a specific UA, or a rate cap. Read the policy.
- Even "passive" tools like Wappalyzer make HTTP requests. Passive in the recon sense is not the same as zero-impact.
- A "noisy" scan from a corporate network can earn your **employer** a complaint or an outage call. Run from a lab box you own, not the office network, when not strictly required.
- Identifying yourself in the User-Agent is friendlier than not. `csot-scanner/1.0 (student-tester; rate-limited)` makes the admin who notices your traffic email you instead of paging your ISP.

Your scanner doesn't decide if the test is legal. You do.

---

## Further reading

- [SecLists](https://github.com/danielmiessler/SecLists) — the wordlist repo.
- [Nuclei templates](https://github.com/projectdiscovery/nuclei-templates) — read the YAML to learn how to write your own.
- [sqlmap official wiki](https://github.com/sqlmapproject/sqlmap/wiki) — flag reference and tamper docs.
- [OWASP ZAP docs](https://www.zaproxy.org/docs/) — for the open-source alternative.
- [PortSwigger Web Security Academy — Burp Scanner labs](https://portswigger.net/web-security/all-topics) — many labs require careful manual + scanner work.
- [HackTricks — Web Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web) — encyclopedia of "what to do after you find this."

---

## Next module

[api-security.md](api-security.md) — APIs are their own attack surface with their own Top 10. The proxies and scanners you just learned apply, but the patterns shift: no HTML, lots of JSON, very different recon, and the per-object access-control bugs (BOLA) dominate.
