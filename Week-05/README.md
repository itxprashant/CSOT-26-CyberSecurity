# Week 5 — Exploitation, post-exploitation & incident response

The capstone. You've spent four weeks building offensive primitives: Linux comfort and scripting (Week 1), recon and network discovery (Week 2), web exploitation (Week 3), and reverse-engineering / forensics fundamentals (Week 4). Week 5 puts it together — what happens *after* you land a shell, how defenders see the same activity, and how to write up everything you did. The weekend CTF is a 10-challenge capstone that recaps every prior week and adds a final boss.

---

## Why this week matters

The first four weeks teach you how to break in. This week teaches the harder half: what to do once you have. Real engagements aren't won by popping a shell — they're won by what happens in the next eight hours. Privilege escalation, post-exploitation enumeration, lateral movement, and persistent footholds are the techniques that turn "I have a shell" into "I have the engagement objectives," and every one of them is also a defender's hunting opportunity.

Week 5 deliberately covers offensive *and* defensive lenses on the same activity. You'll write exploitation steps and detection signatures for the same actions. That's not pedagogical neatness — that's how seniors at every security organisation think. The best red-teamers know what they're tripping; the best blue-teamers know what they're missing. By the end of the week you should be able to switch between both perspectives in the same conversation.

This is also the most **dangerous-if-misused** content in CSOT. The skills here — Metasploit handlers, privilege-escalation toolkits, persistence techniques — are immediately impactful and immediately illegal off-scope. Every module has heavy ethics framing for that reason. Internalise it.

---

## Learning objectives

By the end of this week, you should be able to:

- [ ] Use Metasploit (msfconsole, msfvenom, multi/handler) to deliver payloads against authorized lab targets
- [ ] Enumerate a Linux box for common privesc paths (sudo, SUID, capabilities, cron, group abuse)
- [ ] Recognise and exploit at least four privilege-escalation classes (`sudo -l`, SUID + GTFOBins, cron hijack, writable system file)
- [ ] Upgrade an unstable shell to a full PTY with the `python pty + stty raw -echo` trick
- [ ] Pivot through a compromised host using SSH `-L`/`-D` or chisel
- [ ] Identify where credentials live on a Linux host and reuse them for lateral movement
- [ ] Write a small Python port-scanner with banner grabbing and proper ethics gating
- [ ] Explain the cloud metadata attack class (IMDSv1 vs v2) and the Capital One incident
- [ ] Name the MITRE ATT&CK tactic and at least three sub-techniques for each Week-5 module
- [ ] Walk through the PICERL incident-response lifecycle and the artefacts collected at each phase
- [ ] Triage a suspicious Linux host with a first-pass evidence script
- [ ] Write a polished CTF / IR writeup using `WRITEUP_TEMPLATE.md`
- [ ] Articulate the legal lines (IT Act 2000 §43, §66, §66F) for every offensive technique in the week

---

## Modules (read in order)

Each module ends with a `Next module` link, so you can read them as a path or jump around. The order below introduces the framework first, then the post-foothold work, then the defender's seat.

| # | Module | What you'll learn | Time |
|---|--------|-------------------|------|
| 1 | [metasploit-basics.md](metasploit-basics.md) | Framework architecture, module types, msfconsole workflow, msfvenom, sessions, db_nmap | 60 min |
| 2 | [privilege-escalation.md](privilege-escalation.md) | Linux enumeration, sudo + SUID + capabilities + cron + groups + LD_PRELOAD + kernel; brief Windows section | 75 min |
| 3 | [post-exploitation.md](post-exploitation.md) | Situational awareness, stable shells, credential harvesting, pivoting, persistence concepts, MITRE ATT&CK mapping | 60 min |
| 4 | [python-pentesting.md](python-pentesting.md) | When to write your own tooling, `socket` + `requests` + `argparse`, threading vs asyncio, banner-grabbing scanner extension | 50 min |
| 5 | [cloud-metadata-awareness.md](cloud-metadata-awareness.md) | IMDS endpoints per cloud, SSRF → metadata chain, IMDSv1 vs v2, Capital One case study, defences | 45 min |
| 6 | [detection-evasion-awareness.md](detection-evasion-awareness.md) | Log layers, noise level of Week 5 tools, AV vs EDR, obfuscation reality check, ATT&CK Defense Evasion | 45 min |
| 7 | [incident-response-lite.md](incident-response-lite.md) | PICERL lifecycle, junior responder toolkit, Linux + Windows triage, chain of custody, when to escalate | 60 min |
| 8 | [WRITEUP_TEMPLATE.md](WRITEUP_TEMPLATE.md) | Polished CTF / IR writeup template, with a worked example | 15 min |

**Total reading time:** ~6.5 hours (spread across Mon–Wed).

---

## Recommended workflow

```
Day 1 (Mon):  Modules 1–2 (metasploit + privesc)
              + spin up Metasploitable 2 on a host-only VirtualBox network
              + try sudo -l / SUID / cron paths against it
Day 2 (Tue):  Modules 3–4 (post-ex + python)
              + TryHackMe "Linux PrivEsc" room + extend the port scanner
Day 3 (Wed):  Modules 5–6 (cloud metadata + detection/evasion)
              + read 2-3 entries from the DFIR Report; map them to ATT&CK
Day 4 (Thu):  Module 7 (IR) + start drafting capstone writeup
              + TryHackMe "SOC Level 1" first few rooms
Day 5 (Fri):  Polish writeups, run triage script against your own VMs, pre-CTF practice
Day 6–7:      Weekend capstone CTF (10 challenges, 4–6 hours)
              + final writeup using WRITEUP_TEMPLATE.md
```

---

## External practice platforms

Critical for Week 5 — most of the muscle memory comes from real boxes, not reading. Do these in parallel with the modules.

| Platform | What to do | Link |
|----------|------------|------|
| HackTheBox Starting Point | All of Tier 0; pick 2-3 from Tier 1 — each gives you a full nmap → exploit → privesc loop | [hackthebox.com](https://www.hackthebox.com/) |
| HackTheBox — easy Linux boxes | "Lame," "Shocker," "Beep," "Sense," "Bashed," "Nibbles" — classic walkthroughs everywhere | [hackthebox.com](https://www.hackthebox.com/) |
| TryHackMe — Junior Pentester path | The single best free curriculum mapping to Week 5 | [tryhackme.com](https://tryhackme.com/path/outline/jrpenetrationtester) |
| TryHackMe — Offensive Pentesting path | More advanced, OSCP-aligned | [tryhackme.com](https://tryhackme.com/path/outline/pentesting) |
| TryHackMe — SOC Level 1 path | The blue-team counterpart; necessary for [incident-response-lite.md](incident-response-lite.md) | [tryhackme.com](https://tryhackme.com/path-action/soc-level-1) |
| TryHackMe — Linux PrivEsc / Windows PrivEsc | Direct mapping to [privilege-escalation.md](privilege-escalation.md) | [tryhackme.com](https://tryhackme.com/room/linuxprivesc) |
| TryHackMe — Metasploit Intro / Exploitation / Meterpreter | Direct mapping to [metasploit-basics.md](metasploit-basics.md) | [tryhackme.com](https://tryhackme.com/) |
| OverTheWire — Maze | After Bandit, this is the next-level OTW wargame | [overthewire.org/wargames/maze](https://overthewire.org/wargames/maze/) |
| OverTheWire — Behemoth | Local privilege-escalation puzzles | [overthewire.org/wargames/behemoth](https://overthewire.org/wargames/behemoth/) |
| VulnHub | Offline downloadable VMs (Metasploitable 2 & 3, Mr. Robot, Kioptrix) | [vulnhub.com](https://www.vulnhub.com/) |
| PortSwigger Web Security Academy | If Week 3 web didn't stick — the SSRF chapter ties into Week 5's cloud module | [portswigger.net](https://portswigger.net/web-security) |
| The DFIR Report | Read 3 case studies; map each one to ATT&CK | [thedfirreport.com](https://thedfirreport.com/) |
| CTFtime | Find an upcoming weekend CTF to play with your team after capstone | [ctftime.org](https://ctftime.org/) |

---

## Lab setup

Unlike Week 2 and Week 3, **Week 5 does not ship its own docker-compose lab.** Privilege escalation, post-exploitation, and IR all require a full operating system (kernel, users, services, persistent state) rather than the isolated services a Docker container provides. Practice happens on:

1. **TryHackMe / HackTheBox** boxes while on their VPN (authorised by the platform).
2. **Metasploitable 2 / 3** on a host-only VirtualBox network you control.
3. **Your own Kali / Ubuntu VMs** for triage script practice.
4. **The artefacts in [`../../CTFs/week-05/`](../../CTFs/week-05/)** for the weekend capstone — files only, no networked services.
5. **[`code_examples/`](code_examples/)** for the Python tooling — runs locally against `127.0.0.1`.

Verify:

```bash
ls Week-05/
# code_examples  cloud-metadata-awareness.md  detection-evasion-awareness.md
# incident-response-lite.md  metasploit-basics.md  post-exploitation.md
# privilege-escalation.md  python-pentesting.md  README.md  WRITEUP_TEMPLATE.md
```

No `docker-compose.yml`, no `_infra/` — by design.

---

## Assignments

Due by Friday before the capstone CTF. These are graded.

1. **Privesc lab on Metasploitable 2.** Stand up Metasploitable 2 on host-only networking. From a low-privilege foothold (the `msfadmin` user, or via the vsftpd backdoor), identify and document **two distinct** privilege-escalation paths to root. Each path: enumeration command, exploit command, resulting `id` output, and the technique class from [privilege-escalation.md](privilege-escalation.md). One page total.

2. **Extend the Python port scanner.** Take [`code_examples/port_scanner.py`](code_examples/port_scanner.py) and add: argparse-driven CLI, `--confirm-authorized` gate, banner grabbing per port, threaded scanning, and graceful handling of `Ctrl+C`. Submit the modified script (do **not** modify the original) and a short README explaining what changed and why.

3. **Triage script + IR writeup.** Run the `triage.sh` script from [incident-response-lite.md](incident-response-lite.md) against your own Kali / Ubuntu VM. Write a one-page IR-style report on what's *normal* on that host: running services, listening ports, persistence locations, recently-modified files. This is your baseline — defenders can't recognise anomalies without one.

4. **Capstone writeup.** Solve **at least three** of the weekend CTF challenges and write up each using [WRITEUP_TEMPLATE.md](WRITEUP_TEMPLATE.md). Filling the template for one challenge is the mandatory minimum; three is the assignment grade target. The final-boss challenge counts as one of the three if attempted.

---

## Weekend capstone CTF

**Location:** [../../CTFs/week-05/](../../CTFs/week-05/)
**Challenges:** 10 — recap of Weeks 1–4 plus Week-5-specific content
**Duration:** 4–6 hours
**Format:** Jeopardy-style, **teams of 2–4** (the capstone is team-based, unlike previous weeks)

| Challenge | Category | Points | Skills tested | Reference module |
|-----------|----------|--------|---------------|------------------|
| [recap-linux](../../CTFs/week-05/recap-linux/) | Recap / Linux | 100 | `cat`, file reading, Linux fundamentals | Week 1 — [linux-cli](../Week-01/linux-cli.md) |
| [grep-challenge](../../CTFs/week-05/grep-challenge/) | Linux | 150 | `grep` against noisy input | Week 1 — [basic-recon-commands](../Week-01/basic-recon-commands.md) |
| [recap-crypto-base64](../../CTFs/week-05/recap-crypto-base64/) | Recap / Crypto | 150 | `base64 -d`, encoding chains | Week 4 |
| [recap-net-port](../../CTFs/week-05/recap-net-port/) | Recap / Networking | 150 | Reading scan output, port → service mapping | Week 2 — [network-scanning](../Week-02/network-scanning.md) |
| [recap-web-cookie](../../CTFs/week-05/recap-web-cookie/) | Recap / Web | 150 | Parsing `Set-Cookie` headers | Week 3 |
| [cron-hint](../../CTFs/week-05/cron-hint/) | Linux / PrivEsc | 200 | Reading a crontab entry; cron-as-root pattern | [privilege-escalation.md](privilege-escalation.md) |
| [forensics-log](../../CTFs/week-05/forensics-log/) | Forensics | 200 | Log triage with `grep` | [incident-response-lite.md](incident-response-lite.md) |
| [python-port-scan](../../CTFs/week-05/python-port-scan/) | Python / Networking | 250 | Using the bundled port scanner; extending it | [python-pentesting.md](python-pentesting.md) |
| [privesc-suid](../../CTFs/week-05/privesc-suid/) | PrivEsc | 300 | SUID-style escalation; sudo execution | [privilege-escalation.md](privilege-escalation.md) |
| [final-boss](../../CTFs/week-05/final-boss/) | Capstone | 500 | Combining category recall; cross-category synthesis | All of Weeks 1–5 |

**Total available:** 2150 points.

Categorisation notes:

- The five **recap-\*** challenges (recap-linux, recap-crypto-base64, recap-net-port, recap-web-cookie, plus grep-challenge as a Linux recap) deliberately re-test cumulative Weeks 1–4 muscle memory. Easy wins if you stayed sharp.
- The three **Week-5-specific** challenges (cron-hint, forensics-log, python-port-scan, privesc-suid) test material from this week's modules directly.
- The **final-boss** challenge is the cross-category capstone — it expects you to have solved earlier challenges and synthesise across categories. Worth nearly a quarter of the total points.

**Tips for success:**

- Read each `README.md` carefully — the descriptions are terse but accurate.
- Open the artefact files alongside the README. The flag is almost always in the artefact.
- Use the [`code_examples/`](code_examples/) helpers — `port_scanner.py` and `log_parser.py` solve two challenges directly.
- Default flag format remains `csot26{...}` — `grep -r 'csot26{' ../../CTFs/week-05/` works in a pinch.
- Solve the recaps first to bank points, then tackle the Week-5-specific challenges, then the final boss.
- Pair up early — two pairs of eyes catch hint-shaped clues that one set misses.

---

## Key concepts to remember

| Concept | Why it matters this week |
|---------|--------------------------|
| `sudo -l` and GTFOBins | Solve more boxes than every other technique combined |
| SUID + `find / -perm -4000` | The first 30 seconds of every privesc enumeration |
| Python pty + `stty raw -echo` | The single most important shell-upgrade trick |
| ATT&CK Tactics (TA0007 Discovery, TA0005 Defense Evasion, TA0008 Lateral Movement) | Shared vocabulary across the industry |
| IMDSv1 → IMDSv2 | The standard mitigation; know what changed and why |
| Capital One 2019 | The canonical SSRF → metadata → S3 case study |
| PICERL lifecycle | NIST SP 800-61's six-phase model — used in every modern IR plan |
| Order of volatility (RFC 3227) | Capture memory before pulling power |
| Chain of custody | Evidence has to stand up later |
| LOLBins / GTFOBins | Living off the land — the modern attacker's default |
| Authorization first | Every Week 5 technique is illegal off-scope (IT Act 2000 §43, §66, §66F) |
| Default tools are loud | "Evasion" is a delay, not invisibility — assume EDR sees you |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `msfconsole` fails to start | `sudo msfdb init` once; ensure Postgres is running; `apt update && apt install metasploit-framework` |
| `msfvenom` payload caught by your own Defender on Windows VM | Disable Defender on the lab VM (Settings → Virus & threat protection) — this is a *lab* VM only |
| `python pty + stty raw -echo` trick gives garbled output | Check `TERM` is set (`export TERM=xterm`); some shells need `reset` first |
| `linpeas.sh` exits immediately | Probably running on `dash`, not `bash` — call as `bash ./linpeas.sh` |
| `ssh -D 9050` works but `proxychains` doesn't tunnel | Edit `/etc/proxychains.conf` — `socks5 127.0.0.1 9050` and disable `proxy_dns` for nmap |
| Metasploitable 2 won't boot in VirtualBox | "VT-x is disabled" — enable virtualization extensions in BIOS |
| HackTheBox VPN connects but `nmap` says target is down | Add `-Pn` — HTB filters ICMP on most boxes |
| TryHackMe room shows IP but `ping` fails | Same — `-Pn`, or just `curl` the IP |
| Triage script outputs nothing | Run as root; some `/proc` paths and journal entries require it |
| `chisel` connects but no SOCKS proxy on attacker side | Use `-R socks` from client; `--reverse` on server |
| Capstone CTF flag rejected | Whitespace or wrong braces — flags are exactly `csot26{...}` with no spaces |

---

## What's next — this is the final week

You finish the course here. The next step is yours to choose. Concretely:

### Pick a specialisation

| Track | Build on |
|-------|----------|
| **Web AppSec** | Week 3 + PortSwigger Web Security Academy in full → eventually CBBH / OSWE / [Bug Bounty Bootcamp](https://nostarch.com/bug-bounty-bootcamp) |
| **Red team / pentesting** | Week 5 + HackTheBox + TryHackMe Offensive path → eJPT → OSCP (PEN-200) → OSWP / OSEP |
| **Forensics / DFIR** | Week 5 IR module + TryHackMe SOC L1 → BTL1 (Blue Team Level 1) → SANS GIAC tracks |
| **Blue team / detection engineering** | Week 5 detection module + Sigma rules + Atomic Red Team → BTL1 → SC-200 / GIAC GCDA |
| **Crypto** | Cryptohack + cryptopals → academic study (PRPs, ZK, lattice attacks) |
| **Cloud security** | Week 5 cloud module + CloudGoat + LocalStack → AWS Security Specialty → Azure SC-100 |
| **Mobile / OS internals** | Pwntools + binary exploitation → ROP school → pwn.college |

You don't have to pick now — most CSOT graduates explore two or three of the above for six months before committing. But pick *something*; depth beats breadth in the second year.

### Keep playing CTFs

- Pick one weekend CTF a month from [CTFtime](https://ctftime.org/).
- Aim for **mid-tier** events first — large public events (HackTheCon, picoCTF) have beginner-friendly tracks. Big ones (Google CTF, PlaidCTF) are for after a year.
- Compete as a team. Track ratings on CTFtime.
- After every CTF, write up the challenges you solved using [WRITEUP_TEMPLATE.md](WRITEUP_TEMPLATE.md). The compound effect is enormous.

### Consider a certification

| Cert | Audience | Cost (approx.) |
|------|----------|---------------|
| **HTB CPTS** (Certified Penetration Testing Specialist) | Hands-on, pentest-focused | ~USD 200 |
| **eJPTv2** | Junior pentester; achievable in ~1 month after Week 5 | ~USD 200 |
| **TryHackMe — Junior Penetration Tester path** + free certs | Quick, free, resume-acceptable | Free |
| **CompTIA Security+** | Broad, employer-recognised, lots of theory | ~USD 400 |
| **OSCP (PEN-200)** | The gold standard for offensive roles; expect 6 months of prep | ~USD 1500 |
| **BTL1 (Blue Team Level 1)** | DFIR/SOC, hands-on | ~USD 400 |

CSOT doesn't endorse a specific cert. Pick what aligns with the specialisation above. eJPTv2 and HTB CPTS are the most CSOT-adjacent next steps if you want a hands-on credential within months.

### Apply learnings — *within scope*

- **Bug bounty programs:** Once Week 3 + Week 5 are solid, start on programs with **clear in-scope rules**. Read scope twice; ask the program owner once; document everything; never deviate. HackerOne, Bugcrowd, Intigriti are the well-known platforms.
- **Open-source security audits:** Pick a small project you use, read its security policy, report findings responsibly.
- **CTF challenge authoring:** Submit challenges to next year's CSOT. Authors learn more than solvers.

### Recommended further reading

- [PEN-200 Course Guide / OSCP curriculum](https://www.offsec.com/courses/pen-200/) — the closest thing to "what you should know after Week 5"
- [HackTricks](https://book.hacktricks.xyz/) — encyclopedia; the most-used reference in the industry
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) — payload library per attack class
- [The DFIR Report](https://thedfirreport.com/) — public IR writeups; read 5+ over the year
- [MITRE ATT&CK matrix](https://attack.mitre.org/) — the framework everyone references
- [Awesome Pentest](https://github.com/enaqx/awesome-pentest) — curated tool list
- *The Hacker Playbook 3* — Peter Kim — practical red-team workflows
- *Red Team Field Manual* — short, dense reference card
- *Blue Team Field Manual* — the defender counterpart

---

## Acknowledgements

Five weeks of CSOT, from "what's Linux?" to "I just popped Metasploitable and wrote the IR report." If you got here, you have the foundation. The journey from foundation to professional security work is years; the foundation is the hard part. Welcome to security.

**Previous:** [Week 4 — Crypto, forensics & binary basics](../Week-04/)
**Next:** Pick a specialisation. Play a CTF this weekend. Welcome to the rest of your security career.
