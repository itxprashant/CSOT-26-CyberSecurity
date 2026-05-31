# Week 2 — Reconnaissance, OSINT & network discovery

Last week you built the foundation: Linux comfort, scripting, and the safety mindset. This week you point those skills outward. **Reconnaissance** is the first phase of every attack and every defense — before you can break or protect a system, you need to know what's there. By the end of the week you'll be able to map a domain's infrastructure, scan a host for open services, gather a dossier from public sources, and automate the whole pipeline into a one-command report.

---

## Why this week matters

A surprising amount of real-world security work is recon. Pentesters spend a third of their engagement collecting information. SOC analysts triage alerts by enriching them with WHOIS and passive DNS. Bug-bounty hunters live on subdomain enumeration. Defenders run the *same* tools against their own assets to find what's exposed before someone else does.

Recon is also the part of security with the trickiest ethics: most of these tools are legal to point at your own assets, illegal to point at someone else's, and the difference comes down to authorization rather than the command you typed. Getting comfortable with the boundary is half the lesson.

Everything you learn this week — packets, ports, DNS, OSINT, automation — is reused every subsequent week. Week 3's web attacks start with port 80/443 from your scan. Week 5's forensics work analyzes the same protocol layers. The mental model you build now pays compounding interest.

---

## Learning objectives

By the end of this week, you should be able to:

- [ ] Explain the TCP/IP layered model and identify which protocol lives at which layer
- [ ] Distinguish TCP vs UDP and describe the 3-way handshake
- [ ] Recognize at least 20 common port numbers and the services behind them
- [ ] Query DNS for any record type with `dig` and read the response sections
- [ ] Enumerate subdomains using both passive (CT logs, crt.sh) and active (wordlist) methods
- [ ] Run `nmap` with appropriate flags for discovery, port scanning, and service detection
- [ ] Interpret `open` / `closed` / `filtered` results without fooling yourself
- [ ] Use `nc` (netcat) to grab banners and probe arbitrary TCP services
- [ ] Build an OSINT dossier from search engines, GitHub, crt.sh, Wayback, and metadata
- [ ] Identify common social-engineering patterns and the psychological levers they exploit
- [ ] Write bash and Python scripts that orchestrate `nmap`, `dig`, `curl`, and friends
- [ ] Parse structured tool output (nmap XML, JSON) into a report
- [ ] Articulate the legal and ethical boundaries of authorized vs unauthorized recon

---

## Modules (read in order)

Each module builds on the previous one. Start with the conceptual networking material, layer on recon techniques, finish with automation.

| # | Module | What you'll learn | Time estimate |
|---|--------|-------------------|---------------|
| 1 | [networking-fundamentals.md](networking-fundamentals.md) | TCP/IP layers, IP addressing, ports, TCP vs UDP, DNS and HTTP at a glance | 40 min |
| 2 | [network-scanning.md](network-scanning.md) | Host discovery, nmap scan types, NSE scripts, banner grabbing with netcat | 50 min |
| 3 | [dns-enumeration.md](dns-enumeration.md) | DNS architecture, record types, `dig` mastery, WHOIS, subdomain discovery, zone transfers | 45 min |
| 4 | [osint-techniques.md](osint-techniques.md) | Search dorking, certificate transparency, Shodan, GitHub leaks, metadata, archives, dossiers | 50 min |
| 5 | [social-engineering-awareness.md](social-engineering-awareness.md) | Attack types, Cialdini levers, phishing telltales, defensive habits, legal lines | 35 min |
| 6 | [recon-automation.md](recon-automation.md) | Bash + Python pipelines, parsing nmap XML, `jq` on JSON, report generation | 45 min |

**Total reading time:** ~4–4.5 hours (spread across Mon–Wed)

---

## Recommended workflow

```
Day 1 (Mon):  Modules 1–2 (networking fundamentals + nmap)
              + spin up the Week 2 lab (docker compose) and scan it
Day 2 (Tue):  Modules 3–4 (DNS + OSINT)
              + TryHackMe Nmap / Network Services rooms
Day 3 (Wed):  Modules 5–6 (social engineering + automation)
              + TryHackMe OhSINT, Searchlight
Day 4 (Thu):  Write your recon.sh script; produce a Markdown report on the lab
              + experiment with crt.sh, Shodan, exiftool against synthetic targets
Day 5 (Fri):  Polish the report, review CTF hints, fill in any gaps
Day 6–7:      Weekend CTF (8 challenges, 2–3 hours)
```

---

## External practice platforms

Do these in parallel with the reading. They reinforce exactly what each module covers.

| Platform | What to do | Link |
|----------|------------|------|
| TryHackMe | "Nmap" room — every flag from `network-scanning.md` walked through | [tryhackme.com](https://tryhackme.com/room/furthernmap) |
| TryHackMe | "Introductory Networking" | [tryhackme.com](https://tryhackme.com/) |
| TryHackMe | "Network Services" + "Network Services 2" — enumerate FTP/SMB/SSH/Telnet | [tryhackme.com](https://tryhackme.com/) |
| TryHackMe | "OhSINT" — beginner OSINT puzzle | [tryhackme.com](https://tryhackme.com/room/ohsint) |
| TryHackMe | "Searchlight — IMINT" and "WebOSINT" | [tryhackme.com](https://tryhackme.com/) |
| TryHackMe | "Phishing Emails 1–5" — read real headers | [tryhackme.com](https://tryhackme.com/) |
| HackTheBox | Starting Point Tier 0 — every box starts with nmap | [hackthebox.com](https://www.hackthebox.com/) |
| picoCTF Gym | "Forensics" and "General Skills" categories — light OSINT-style puzzles | [play.picoctf.org/practice](https://play.picoctf.org/practice) |
| OSINT Framework | Browse the tree to know what exists | [osintframework.com](https://osintframework.com/) |
| Bellingcat | Read 1–2 published investigations to see professional OSINT | [bellingcat.com](https://www.bellingcat.com/) |

---

## Lab network

A small docker-compose stack provides two authorized scan targets bound to `127.0.0.1` only.

```bash
cd CTFs/week-02/_infra
sudo docker compose up -d
```

| Service | Port | Used by |
|---------|------|---------|
| `nc-service` (custom TCP echo + greeting) | `127.0.0.1:9001` | `../../CTFs/week-02/netcat-handshake/` |
| `http-banner` (nginx with custom banner) | `127.0.0.1:8080` | `../../CTFs/week-02/banner-guess/` |

Stop the lab when you're done:

```bash
sudo docker compose down
```

**Important:** the lab only listens on loopback. You can scan it freely from your own machine. Do not scan anything else — that's not in scope.

---

## Assignments (practice — not scored)

Work through these before the weekend CTF. **Only CTF flags are scored.**

1. **Recon report on the lab network.** Run your own pipeline (bash, Python, or both — see [recon-automation.md](recon-automation.md)) against `127.0.0.1` while the docker-compose lab is up. Produce a one-page Markdown report listing open ports, services, versions, banners, and any anomalies. Include the script(s) you used.

2. **Self-OSINT audit.** Run a passive OSINT pass on **yourself** (one search engine pass, [haveibeenpwned.com](https://haveibeenpwned.com/), one Sherlock-style username check on yourself, GitHub history for your email). Keep a short write-up of what you found and what you'll clean up. *Do this on yourself only — do not audit classmates.*

3. **Phishing red-flag walkthrough.** Pick any phishing email you've personally received (or one from the [APWG archive](https://apwg.org/phishing-archive/)). Walk through the red flags from [social-engineering-awareness.md](social-engineering-awareness.md): sender domain, link target, urgency, authentication headers if you have access. One page.

4. **Tooling check.** Confirm these are installed and working on your Kali / WSL / VM:

   - `nmap`, `dig`, `whois`, `nc`, `curl`, `jq`
   - `python3` with `requests` and a recent `lxml`/`ElementTree`
   - Optionally: `ffuf`, `subfinder`, `amass`, `exiftool`, `gobuster`

   `apt install -y nmap dnsutils whois ncat curl jq exiftool ffuf` covers most.

---

## Weekend CTF

**Location:** [../../CTFs/week-02/](../../CTFs/week-02/)
**Challenges:** 8 — recon, OSINT, DNS, banner grabbing, log parsing
**Duration:** 2–3 hours
**Format:** Jeopardy-style, individual

| Challenge | Category | Points | Skills tested |
|-----------|----------|--------|---------------|
| [port-logic](../../CTFs/week-02/port-logic/) | Networking | 100 | Recall the well-known ports table |
| [banner-guess](../../CTFs/week-02/banner-guess/) | Recon | 150 | Read an HTTP/service banner, identify the service |
| [pcap-dns](../../CTFs/week-02/pcap-dns/) | DNS / forensics | 200 | `grep` a DNS query log |
| [dns-txt-flag](../../CTFs/week-02/dns-txt-flag/) | DNS | 200 | Parse a zone file for a TXT record |
| [scan-report](../../CTFs/week-02/scan-report/) | Recon | 200 | Find a flag embedded as a comment in nmap output |
| [osint-dossier](../../CTFs/week-02/osint-dossier/) | OSINT | 200 | Combine clues (CEO pet name + project codename) from a synthetic company page |
| [netcat-handshake](../../CTFs/week-02/netcat-handshake/) | Networking | 250 | Send the right greeting to a TCP service with `nc` |
| [parse-scan-json](../../CTFs/week-02/parse-scan-json/) | Automation | 250 | Use `jq` or Python to extract a field from JSON output |

**Total available:** 1550 points

**Tips for success:**
- Read each challenge's `README.md` carefully — descriptions contain hints.
- Bring up the lab (`docker compose up -d`) for `netcat-handshake` and `banner-guess`.
- Default flag format remains `csot26{...}` — search for it with `grep -r 'csot26{' .` if you're stuck.
- Most challenges reward reading the file with the right tool. `cat`, `grep`, `dig`, `jq`, `nc` are all you need.

---

## Key concepts to remember

| Concept | Why it matters this week |
|---------|-------------------------|
| TCP 3-way handshake | Basis for every TCP port-scan technique |
| Open / closed / filtered | Don't confuse "no response" with "not running" |
| `Pn`, `sS`, `sV`, `sC`, `oA` | The five nmap flags you'll use most |
| `dig +short` | The fast form for scripting DNS into other tools |
| Certificate transparency | Subdomains live forever in `crt.sh` |
| Look-alike domains | First defense against phishing is reading the full address |
| Cialdini's six levers | Authority/urgency/scarcity/reciprocity/liking/social-proof — name the lever in any phish |
| Passive vs active recon | Different legal exposure; default to passive |
| Idempotent automation | Every stage should be cheap and safe to rerun |
| Authorization first | Every command in this week is fine on lab targets and illegal on others |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `nmap` says host is down, but you can `ping` it | Add `-Pn` to skip host discovery |
| Lab containers won't start | `sudo docker compose down && up -d`; check `docker ps` and `docker logs <name>` |
| `dig: command not found` | `sudo apt install dnsutils` |
| `nc` flags behave oddly | You likely have `ncat` (nmap variant); read `man ncat` and `man nc` |
| `Permission denied` on raw scans (`-sS`) | Either run with `sudo` or use `-sT` (TCP connect, no root needed) |
| Subfinder/amass return nothing | They use third-party APIs that need keys (`~/.config/subfinder/provider-config.yaml`); passive-only sources still work without keys |
| `jq` errors with `parse error` | Input isn't valid JSON; check with `jq . file.json` first or pipe through `python3 -m json.tool` |
| Browser blocks `crt.sh` JSON | Use `curl -s "https://crt.sh/?q=%25.example.com&output=json"`; some browsers expect HTML |
| Scans on TryHackMe time out | You may not be on their VPN; check with `ip addr | grep tun0` |

---

## Advanced Reading

For those who want to go deeper this week:

### Books

- *Open Source Intelligence Techniques* — Michael Bazzell — professional OSINT methodology
- *Nmap Network Scanning* — Gordon Lyon — definitive guide to nmap

### Online courses / paths

- [TryHackMe — OSINT](https://tryhackme.com/) — OhSINT, Searchlight, WebOSINT rooms
- [SANS SEC487](https://www.sans.org/cyber-security-courses/open-source-intelligence-gathering/) — OSINT certification track (overview)
- [Bellingcat](https://www.bellingcat.com/) — published investigations as case studies

### Tools to explore

- [Maltego](https://www.maltego.com/) — link analysis (community edition)
- [theHarvester](https://github.com/laramies/theHarvester) — email and subdomain harvesting
- [SpiderFoot](https://www.spiderfoot.net/) — automated OSINT orchestration
- [Recon-ng](https://github.com/lanmaster53/recon-ng) — modular recon framework

### Challenge platforms

- [Trace Labs](https://www.tracelabs.org/) — OSINT-for-good CTF events
- [HackTheBox — Starting Point](https://www.hackthebox.com/) — every box begins with nmap
- [contactrika OSINT puzzles](https://contactrika.github.io/)

### Videos / creators

- [The Cyber Mentor](https://www.youtube.com/c/TheCyberMentor) — recon and enumeration walkthroughs
- [NahamSec](https://www.youtube.com/c/Nahamsec) — recon for bug bounty

---

## What's next

Week 3 takes the **port 80 / 443** entries from your scan reports and turns them into actual web-application attack surface. You'll fuzz directories, discover endpoints, and exploit OWASP Top-10 classes like SQL injection, XSS, IDOR, and command injection. The subdomain and recon-automation work from this week directly feeds Week 3's target lists.

**Next:** [Week 3 — Web security](../Week-03/)
