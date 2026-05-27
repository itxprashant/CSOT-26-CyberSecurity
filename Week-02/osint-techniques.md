# OSINT techniques

**OSINT** — *Open Source Intelligence* — is the discipline of collecting, correlating, and analyzing information from **public** sources. There's no hacking, no exploitation, no unauthorized access. Just searching, reading, and connecting dots that the target has already left in the open.

That sounds gentle until you see what's actually out there. A LinkedIn page tells an attacker who handles billing. A GitHub commit history reveals an AWS key that was reverted six commits ago. A photo's EXIF data exposes the office's exact GPS coordinates. A web archive shows a now-deleted job posting that named the firewall vendor.

This module covers the techniques, the tooling, and — just as important — the ethical and legal lines you should never cross.

---

## Why OSINT matters

OSINT is the first phase of every realistic attack and the first phase of every legitimate red-team engagement. Before you touch a target's infrastructure, you build a **picture** of it:

- Who works there? What do they do? What do they like and dislike?
- What technology stack do they use? Which vendors? Which versions?
- What's their public footprint — domains, IPs, GitHub orgs, paste sites, code archives?
- What did they look like 6 months, 2 years, 10 years ago?

Once you have that picture, every later step (phishing, vuln research, credential stuffing) becomes far more targeted. **Defenders** care about exactly the same picture — because anything *you* can find, an attacker can too. OSINT is a two-way mirror.

You'll also use OSINT-style thinking in CTFs constantly: "Search for the flag format on the public internet" or "Find the conference video that contains the password" are real challenge categories.

---

## The OSINT mindset

Three habits separate effective OSINT from random Googling:

1. **Iterate** — every finding spawns three new queries. Treat each fact as a node in a graph and follow edges.
2. **Pivot** — the same person has different identities on different platforms. A username on Reddit may unlock an email pattern; an email may unlock GitHub commits; commits may unlock company affiliations.
3. **Verify** — anything public can be staged or stale. Cross-check across at least two independent sources before claiming a fact.

A useful loop:

```
Question → Search → Capture → Pivot to new question → Search → ...
                       │
                       └─ Save raw evidence (URL + screenshot + timestamp)
```

You will *forget* what you saw last Tuesday. Save evidence as you go.

---

## Source categories

Every OSINT investigation pulls from some combination of these:

| Source | Examples | Typical findings |
|--------|----------|------------------|
| Search engines | Google, Bing, DuckDuckGo, Yandex | Cached pages, dorks, public docs |
| Domain & DNS | crt.sh, SecurityTrails, DNSdumpster | Subdomains, infrastructure |
| Internet scans | Shodan, Censys, ZoomEye, FOFA | Exposed services, banners, certs |
| Code | GitHub, GitLab, Bitbucket, paste sites | Leaked keys, internal code |
| Social | LinkedIn, X/Twitter, Instagram, Facebook | Employees, org chart, lifestyle |
| Archives | Wayback Machine, Google cache, Common Crawl | History, deleted content |
| Public records | WHOIS, SEC EDGAR, court records | Ownership, finances |
| Media metadata | EXIF, PDF authors, Office authors | Author names, GPS, software versions |
| Specialty | HaveIBeenPwned, breach data, pastebin | Credential exposure |

Some of these are **passive** (they query an aggregator, never touching the target). Some are **active** (they make the target's server respond — log entries appear). For initial recon, keep it passive.

---

## Search engines — dorking properly

Google is still the single most powerful OSINT tool. The trick is using its operators, not its keywords.

### Operators you should memorize

| Operator | Meaning | Example |
|----------|---------|---------|
| `site:` | Restrict to one domain | `site:example.com` |
| `-site:` | Exclude a domain | `-site:facebook.com` |
| `inurl:` | Word in URL | `inurl:admin` |
| `intitle:` | Word in page `<title>` | `intitle:"index of"` |
| `intext:` | Word in body | `intext:"internal use only"` |
| `filetype:` | Restrict by extension | `filetype:pdf` |
| `ext:` | Same as filetype | `ext:env` |
| `"exact phrase"` | Match the phrase verbatim | `"confidential"` |
| `*` | Wildcard within a phrase | `"company * roadmap"` |
| `OR` / `\|` | Either | `salary OR compensation` |
| `cache:` | Google's cached copy | `cache:example.com/page` |
| `related:` | Sites similar to | `related:example.com` |
| `before:` / `after:` | Date filter | `after:2023-01-01` |

### Classic Google dorks

These are valid public-information queries. Use them only against **lab targets or your own assets**:

```text
site:example.com filetype:pdf "internal"
site:example.com inurl:wp-content/uploads
site:example.com (filetype:env OR filetype:cfg OR filetype:ini)
site:edu.in filetype:pdf "syllabus"
intitle:"index of" "parent directory" "backup"
intitle:"index of" "*.sql"
intext:"BEGIN RSA PRIVATE KEY" site:github.com
"password" filetype:log
```

The Google Hacking Database catalogs thousands more: [exploit-db.com/google-hacking-database](https://www.exploit-db.com/google-hacking-database).

### Anti-pattern: don't dork live targets you don't own

A Google dork that *finds* a leaked file is fine — Google has already indexed it. The moment you *download* the file from the target site, you've made an unauthorized request. Stick to lab and synthetic targets in CSOT.

---

## Domain, DNS, and certificate intelligence

This overlaps heavily with [dns-enumeration.md](dns-enumeration.md), but for the OSINT angle:

| Service | Tells you |
|---------|-----------|
| [crt.sh](https://crt.sh/) | Every TLS cert ever issued to the domain (subdomains forever) |
| [SecurityTrails](https://securitytrails.com/) | Historical DNS — IPs the domain used in the past |
| [VirusTotal](https://www.virustotal.com/) | Passive DNS, file submissions, URL history |
| [DNSdumpster](https://dnsdumpster.com/) | Quick visual map of a domain's records |
| WHOIS / RDAP | Registration data |
| [BGP.HE.NET](https://bgp.he.net/) | What IP ranges belong to which ASN |

These are all **passive** — they look up data the third party already collected. You're not touching the target.

---

## Internet-scanning search engines

Shodan, Censys, and friends continuously scan the internet and let you search their results. You can search by service, banner, ASN, location, certificate, and a thousand other facets.

### Shodan

[shodan.io](https://www.shodan.io/) — the original.

Useful filters:

| Filter | Example |
|--------|---------|
| `org:` | `org:"Example Corp"` |
| `port:` | `port:22` |
| `country:` | `country:IN` |
| `city:` | `city:"Mumbai"` |
| `product:` | `product:nginx` |
| `version:` | `version:"1.18.0"` |
| `ssl.cert.subject.cn:` | `ssl.cert.subject.cn:*.example.com` |
| `http.title:` | `http.title:"Welcome to nginx!"` |
| `vuln:` | `vuln:CVE-2021-44228` (paid feature) |

### Censys

[search.censys.io](https://search.censys.io/) — similar idea, very strong certificate search.

### Critical rule

These tools let you find *exposed* systems. **Looking at the index entry is OSINT. Connecting to the system from the index is active recon and requires authorization.** Treat Shodan like a phone book: it's fine to look up someone's number, not fine to call random people at 3am.

---

## Code repositories — GitHub, GitLab, paste sites

Developers leak secrets. Constantly. Every major breach in the last decade has, at some point, involved an exposed key in a public repo.

What to search:

- Hard-coded credentials: `AKIA...` (AWS), `ghp_...` (GitHub PAT), `xoxb-...` (Slack bot token).
- Configuration with hostnames, internal API endpoints, database DSNs.
- Old commits — deleted but still reachable by SHA.
- Forks and personal accounts of employees.

GitHub search operators:

```text
"AKIA" org:example-corp
filename:.env "DB_PASSWORD"
filename:id_rsa
"BEGIN RSA PRIVATE KEY"
extension:pem
"api.example.com" "token"
```

Tools that automate this responsibly (for **your own** repos or authorized targets):

| Tool | What it does |
|------|--------------|
| [trufflehog](https://github.com/trufflesecurity/trufflehog) | Scans repos for secrets with entropy + regex |
| [gitleaks](https://github.com/gitleaks/gitleaks) | Pre-commit + repo scanner for secrets |
| [github-dorks](https://github.com/techgaun/github-dorks) | Curated GitHub dork list |

```bash
trufflehog git https://github.com/example/repo
gitleaks detect --source . --report-path leaks.json
```

If you find a real secret in a third-party repo, **don't use it**. Report it via the vendor's security disclosure channel.

Paste sites (Pastebin, Gist, paste.ee) and Discord exports also leak credentials and internal docs — search engines and dedicated monitors index them.

---

## Wayback Machine and other archives

The [Wayback Machine](https://web.archive.org/) periodically snapshots most of the web. Use cases:

- A page now hidden behind login was once public.
- Old job postings revealed exact technology versions.
- A previous version of `robots.txt` listed admin paths.
- A press release mentioned a vendor that was later replaced.

Tools:

```bash
# waybackurls — pull all URLs ever recorded for a domain
echo example.com | waybackurls | sort -u > wayback.txt

# gau — same idea, multiple sources
echo example.com | gau | sort -u > gau.txt
```

Install via Go:

```bash
go install github.com/tomnomnom/waybackurls@latest
go install github.com/lc/gau/v2/cmd/gau@latest
```

Other archives worth knowing: [archive.today](https://archive.today/), [Common Crawl](https://commoncrawl.org/), Google cache (rapidly being deprecated, but still occasionally useful).

---

## Metadata — the data hidden in files

Every photo, document, and PDF carries **metadata** the creator usually forgot existed. Standard targets:

### EXIF (images)

JPEGs from phones embed GPS coordinates, camera model, software version, original timestamp.

```bash
exiftool photo.jpg
# Look for:
#   GPS Position
#   Camera Model Name
#   Software
#   Create Date
#   Author / Copyright
```

If a target posts photos on social media that aren't stripped (Instagram strips, some forums don't), you get free location data.

### Office / PDF metadata

Word docs and PDFs embed author name, organization, software, edit history:

```bash
exiftool report.pdf
exiftool quarterly.docx
pdfinfo report.pdf
```

Author names of internal documents are gold for crafting phishing pretexts.

### Strip your own metadata

```bash
exiftool -all= -overwrite_original photo.jpg
# Or use mat2 for thorough scrubbing
mat2 photo.jpg
```

---

## People and account hunting

A real investigation often pivots on **identity** — connecting a username on one site to an email or another username elsewhere.

| Tool | What it does |
|------|--------------|
| [Sherlock](https://github.com/sherlock-project/sherlock) | Checks ~400 sites for a username |
| [WhatsMyName](https://whatsmyname.app/) | Browser-friendly equivalent |
| [Maigret](https://github.com/soxoj/maigret) | Sherlock fork with more sources & metadata |
| [holehe](https://github.com/megadose/holehe) | Tests if an email is registered on common sites |
| [HaveIBeenPwned](https://haveibeenpwned.com/) | Tells you if an email is in known breaches |
| [Hunter.io](https://hunter.io/) | Guesses corporate email patterns |

Install Sherlock:

```bash
pipx install sherlock-project
sherlock johndoe
```

**Lab-only rule for CSOT:** apply these tools to synthetic personas in the course's `osint-dossier` challenge, not to real students, faculty, or classmates. Even when something is publicly available, aggregating it without consent is creepy and may be illegal under privacy laws.

---

## Framework: where to start when you're staring at a target

When you don't know where to begin, walk through [osintframework.com](https://osintframework.com/). It's a categorized tree of every OSINT resource — username search, social network analysis, document search, dark web, geolocation, etc. Bookmark it.

For people-search specifically: [IntelTechniques tools](https://inteltechniques.com/tools/) (Michael Bazzell).

---

## Geolocation OSINT (briefly)

Given a photo or video, can you place where it was taken?

- **Direct**: EXIF GPS (when not stripped).
- **Indirect**: visible street signs, building shapes, vegetation, sun direction, license-plate formats.

The community game **GeoGuessr** is essentially geolocation-OSINT practice. For serious investigations, [Bellingcat](https://www.bellingcat.com/) publishes step-by-step write-ups.

---

## Synthesizing findings — the dossier

The output of OSINT work is a **dossier**: a structured document that lays out everything you found, with sources. A useful template:

```
Target:      <name / domain>
Date:        <when you collected>

Domains
  example.com    A 93.184.216.34   nginx 1.18 (crt.sh, scan 2024-…)
  api.example.com  CNAME elb-...    AWS

Employees
  Alice Patel — CEO — LinkedIn /alice — emails @example.com
  Bob Singh   — Eng — GitHub /bsingh — committed to public/example-config

Technology stack
  Email — Google Workspace (SPF: include:_spf.google.com)
  CRM — Salesforce (CNAME crm. → *.force.com)
  Code — GitHub Enterprise (DNS, badges on website)

Exposed assets
  staging.example.com  — http 200, dev banner
  ftp.example.com:21   — open, anonymous login allowed (Shodan)

Notes / pivots
  Old job posting (Wayback 2022-04): mentions "managing Splunk pipelines"
  → assume Splunk is in scope for future enumeration
```

Always keep raw evidence (URLs, screenshots, query timestamps) separate from your interpretations.

The lab challenge [../../CTFs/week-02/osint-dossier/](../../CTFs/week-02/osint-dossier/) gives you a synthetic dossier folder (`company/about.md`) where you combine clues into a flag — the same workflow scaled down to a single page.

---

## Defensive OSINT — auditing yourself

The exact same techniques are how you check **your own** exposure. Run a self-OSINT pass every six months:

- Search your name + your email on Google (use `"quotes"` around them).
- Check [haveibeenpwned.com](https://haveibeenpwned.com/) for breaches.
- Search GitHub for your email — any commits with sensitive data?
- Check [google.com/maps/timeline](https://www.google.com/maps/timeline) if you've shared photos that may carry EXIF.
- Search your username with Sherlock-style tools to see what cross-account links exist.

Treat any unexpected hits as something to clean up.

---

## Ethics, law, and the not-creepy rule

OSINT is legal where collecting public data is legal — which is *most* of the time, but not always. Things that can cross legal or ethical lines even with public data:

| Behavior | Why it's a problem |
|----------|--------------------|
| Aggregating personal data into a profile of a real individual without consent | May violate privacy laws (GDPR, DPDP Act in India) |
| Using OSINT to harass, stalk, or dox someone | Criminal in most jurisdictions, and obviously wrong |
| Downloading dumps of breached credentials | Possession can be illegal; using them is definitely illegal |
| Scraping a site against its ToS at scale | Civil and sometimes criminal exposure (LinkedIn vs hiQ saga) |
| Pretending to be someone else online to extract info | Impersonation laws + fraud |

**The not-creepy rule:** if you wouldn't be comfortable telling the person to their face exactly what you did and why, don't do it.

CSOT labs use **synthetic personas** for this reason — fictional companies, fake names, generated photos. You get the technique without the harm.

---

## Practice (synthetic targets only)

- **Week 2 lab** — [../../CTFs/week-02/osint-dossier/](../../CTFs/week-02/osint-dossier/): combine clues from `company/about.md` into a flag.
- **TryHackMe** rooms: *OhSINT*, *Searchlight - IMINT*, *WebOSINT*, *Sakura* — all designed for OSINT practice on synthetic targets.
- **Bellingcat Online Investigation Toolkit** — read a couple of their case write-ups to see how professionals chain sources.

---

## Further reading

- [OSINT Framework](https://osintframework.com/) — categorized tool index.
- [Michael Bazzell — OSINT Techniques](https://inteltechniques.com/book1.html) — comprehensive book; library copy if possible.
- [Bellingcat](https://www.bellingcat.com/) — investigative journalism that's essentially applied OSINT.
- [TraceLabs OSINT guide](https://www.tracelabs.org/initiatives/osint-guide) — community-built guide.
- [`exiftool` documentation](https://exiftool.org/exiftool_pod.html) — vastly more options than the basic commands here.

---

## Next module

[social-engineering-awareness.md](social-engineering-awareness.md) — OSINT becomes social engineering when the picture you built is turned into a phishing email or a phone call. The next module covers both the attack patterns and how to recognize them.
