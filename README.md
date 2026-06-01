# DevClub Cybersecurity Course — CSOT 2026

Welcome to the **Cybersecurity** track of CSOT 2026, led by **DevClub IIT Delhi**.

This is a five-week, hands-on introduction to practical security — covering everything from how attackers think to how defenders respond. You will learn OSINT, web application testing, cryptography, digital forensics, Linux fundamentals, scripting, reverse engineering, and introductory binary exploitation — all tied together with **weekend CTF competitions** that test what you learned each week.

**Register:** [csot.devclub.in/tracks/cybersec/register](https://csot.devclub.in/tracks/cybersec/register) (sign in with your IIT Delhi account)  
**Community:** [CSOT DevClub Cybersecurity WhatsApp group](https://chat.whatsapp.com/BJN7duZuObq1gbGPrped0y)

---

## Why this course?

Software engineers who understand security build better systems. Whether you end up writing production code, auditing infrastructure, or competing in CTFs professionally, this course gives you:

- **Attacker intuition** — understanding how things break helps you build things that don't
- **Practical tooling** — real tools used by professional pentesters (nmap, Burp Suite, Wireshark, hashcat)
- **CTF muscle memory** — solving challenges under time pressure builds pattern recognition
- **A security community** — teammates and mentors you can learn with beyond the 5 weeks

---

## Course overview

| | |
|---|---|
| **Format** | Weekly reading modules → external platform practice → optional assignments → weekend CTF (scored) |
| **Duration** | 5 weeks (Mon–Sun cycles) |
| **Prerequisites** | Basic programming in any language; curiosity about how systems work |
| **Flag format** | `csot26{...}` (all CTF flags follow this format) |
| **Registration** | [Cybersec track registration](https://csot.devclub.in/tracks/cybersec/register) (IIT Delhi account) |
| **Communication** | [Course WhatsApp group](https://chat.whatsapp.com/BJN7duZuObq1gbGPrped0y) — logistics, questions, CTF hints |
| **Submission** | CTF flags submitted via the course CTF platform (assignments are practice only, not scored) |

**Resources:** [RESOURCES.md](RESOURCES.md) — curated links organized by week and difficulty level

---

## Weekly schedule

| Week | Theme | What you'll learn | Start here |
|------|--------|-------------------|------------|
| 1 | Security mindset, digital safety & Linux | Threat modeling, safe lab practices, Linux CLI mastery, bash scripting, your first CTF challenges | [Week-01/](Week-01/) |
| 2 | OSINT & open-source investigation | Google dorking, DNS enumeration, WHOIS, network scanning with nmap, building intelligence from public data | [Week-02/](Week-02/) |
| 3 | Web application security | HTTP internals, OWASP Top 10 vulnerabilities, Burp Suite interception, SQL injection, XSS, API and JWT attacks | [Week-03/](Week-03/) |
| 4 | Cryptography, steganography & forensics | Classical and modern ciphers, hash cracking, hidden data in files, log analysis, PCAP inspection | [Week-04/](Week-04/) |
| 5 | Systems security, RE, PWN & capstone CTF | Privilege escalation, reverse engineering, binary exploitation intro, post-exploitation, IR, team capstone CTF | [Week-05/](Week-05/) |

### Weekly rhythm

| Day | Activity | Details |
|------|----------|---------|
| Mon–Tue | **Study** | Read that week's modules in order; complete any setup tasks; take notes on new concepts |
| Wed–Thu | **External practice** | Work through guided labs on TryHackMe, PortSwigger Academy, picoCTF Gym, or OverTheWire |
| Fri | **Practice & prep** | Optional weekly assignments for hands-on practice; review hints for upcoming CTF; form teams if needed |
| Sat–Sun | **Weekend CTF** | 2–3 hour jeopardy-style competition (8 challenges per week; teams allowed in Week 5) |

### Time commitment

Expect **6–10 hours per week**: ~2 hours reading modules, ~2–3 hours on external platforms, ~1–2 hours on optional practice assignments, and ~2–3 hours on the weekend CTF (the only scored component). You can go deeper — the resources document has advanced material for every topic.

---

## Week 1 — Security mindset, digital safety & Linux

**Goal:** Build the foundational habits and command-line skills that every other week depends on.

You'll learn why security matters, how to protect yourself while doing offensive work, how CTFs are structured, and how to use Linux confidently. By the end of this week you should be comfortable navigating a filesystem, writing bash scripts, and solving basic Linux-themed CTF challenges.

**Key topics:** Threat modeling, phishing detection, CTF categories, Kali/WSL setup, file permissions, pipes and redirection, bash scripting, basic reconnaissance.

→ [Week-01/README.md](Week-01/README.md)

---

## Week 2 — OSINT & open-source investigation

**Goal:** Learn to extract intelligence from publicly available sources — a core skill for both attackers and defenders.

OSINT (Open Source Intelligence) is often the first phase of any security engagement. You'll learn to enumerate DNS records, perform network scans, build profiles from scattered public data, and understand how social engineering leverages OSINT findings.

**Key topics:** Google dorking, WHOIS lookups, DNS zone transfers, nmap scanning, Shodan, social engineering awareness, recon automation with bash.

→ [Week-02/README.md](Week-02/README.md)

---

## Week 3 — Web application security

**Goal:** Understand and exploit the most common vulnerabilities in web applications.

The web is the largest attack surface in modern software. You'll learn how HTTP works under the hood, intercept and modify requests with Burp Suite, and exploit real vulnerabilities from the OWASP Top 10 — including SQL injection, cross-site scripting (XSS), broken authentication, and insecure API design.

**Key topics:** HTTP methods and headers, cookies and sessions, OWASP Top 10, Burp Suite proxy, SQLi, XSS, CSRF, IDOR, JWT manipulation, API testing.

→ [Week-03/README.md](Week-03/README.md)

---

## Week 4 — Cryptography, steganography & forensics

**Goal:** Break ciphers, recover hidden data, and analyze digital evidence.

Cryptography protects data — and when it's implemented poorly, attackers exploit it. You'll learn classical ciphers (Caesar, Vigenère), modern concepts (RSA, hashing), encoding schemes, steganography (data hidden in images/audio), and digital forensics techniques for analyzing logs, disk images, and network captures.

**Key topics:** Base64/hex encoding, XOR, Caesar and Vigenère ciphers, RSA basics, hash cracking with hashcat, steganography with binwalk/steghide, log analysis, PCAP inspection with Wireshark.

→ [Week-04/README.md](Week-04/README.md)

---

## Week 5 — Systems security, reverse engineering, binary exploitation & capstone

**Goal:** Tie everything together with privilege escalation, native-code skills (RE and pwn), automation, defensive IR, and a team-based capstone CTF.

This week covers what happens after initial access — escalating privileges, reversing binaries, introductory stack exploitation, post-exploitation, and how defenders detect these actions. You'll automate common tasks with Python and participate in a team capstone CTF that draws from all 5 weeks.

**Key topics:** Linux privilege escalation (SUID, cron, sudo misconfigs), Ghidra and static RE, buffer overflows and pwntools, post-exploitation, Python scripting for pentesting, Metasploit basics, cloud metadata awareness, incident response lite, team CTF strategy, writeup documentation.

→ [Week-05/README.md](Week-05/README.md) · [Writeup template](Week-05/WRITEUP_TEMPLATE.md)

---

## Rules of engagement

These rules are non-negotiable. Violating them can result in removal from the course and potentially legal consequences:

1. **Authorized targets only** — Only test course infrastructure, your own VMs, and platforms that explicitly allow practice (TryHackMe, Hack The Box, picoCTF, OverTheWire, PortSwigger Academy).
2. **No unauthorized scanning** — Do **not** scan, probe, or attack IIT production systems, campus networks, other students' devices, or any third-party infrastructure without explicit written permission.
3. **No flag leaking** — Do not post live CTF flags publicly before the event ends. After the CTF closes, writeups are encouraged.
4. **Responsible disclosure** — If you accidentally discover a real vulnerability outside course scope, report it responsibly to the system owner. Do not exploit it.
5. **No real-world harm** — Never use course skills to access others' accounts, data, or systems without permission.
6. **Attribution** — Credit tools, writeups, and teammates. Do not share live CTF flags or plagiarize writeups.

---

## Getting help

| Channel | Use for |
|---------|---------|
| [Course WhatsApp group](https://chat.whatsapp.com/BJN7duZuObq1gbGPrped0y) | Logistics, schedule, announcements, module questions, lab issues |
| WhatsApp (CTF weekends) | Nudges during the weekend CTF — coordinators will share hint policy in the group (no spoilers) |
| Coordinators (DM on WhatsApp) | Personal issues, extensions, ethics questions |
| Office hours | Live help with setup or challenging concepts (times announced in the group) |

**Stuck on a challenge?** Before asking for help: (1) re-read the challenge description carefully, (2) Google the error message or technique name, (3) check if a hint is available. If still stuck after 30–45 minutes, ask in the WhatsApp group.

---

## After the course

This course is a launchpad, not a destination. Here's how to keep growing:

- **Compete** — Pick an event on [CTFtime](https://ctftime.org/); start with beginner/university CTFs and work up
- **Specialize** — [RESOURCES.md](RESOURCES.md) has paths for reversing, binary exploitation, bug bounty, and more
- **Certify** — Consider eJPT, CompTIA Security+, or OSCP as next milestones
- **Contribute** — Write CTF challenges, help next year's cohort, or start a security research project
- **Bug bounty** — Platforms like HackerOne and Bugcrowd pay for real vulnerabilities found responsibly

---

## Repository structure

```
CyberSecurity_DevClub/
├── README.md              ← You are here
├── RESOURCES.md           ← Curated links by week and level
├── Week-01/              ← Modules and assignments
├── Week-02/
├── Week-03/
├── Week-04/
└── Week-05/
    └── WRITEUP_TEMPLATE.md
```

Each `Week-XX/` folder contains:
- `README.md` — Overview and learning objectives
- Topic modules (`.md` files) — Read in order
- `assignments/` — Optional practice (not scored; CTF flags are)

Weekend CTF challenges live under `../CTFs/week-XX/` (one folder per week), each with challenge READMEs and supporting files.

---

*DevClub IIT Delhi — CSOT 2026*
