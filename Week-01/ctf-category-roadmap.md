# CTF category roadmap

This module maps the CSOT curriculum to standard CTF categories, helps you understand how the weeks build on each other, and guides you toward external practice that matches your current skill level.

Based on [TryHackMe's category guide](https://tryhackme.com/resources/blog/ctf-deep-dive-how-to-choose-the-right-category-for-your-skill-level) and [Snyk's CTF types](https://snyk.io/articles/ctf/ctf-types/).

---

## CSOT progression map

Each week maps to specific CTF categories. The course is designed so earlier weeks provide the foundation for later ones:

```
Week 1           Week 2            Week 3             Week 4              Week 5
Linux/Safety     OSINT/Recon       Web Security       Crypto/DFIR         Systems + Capstone
    │                │                  │                  │                   │
    ▼                ▼                  ▼                  ▼                   ▼
 Misc/General     OSINT            Web               Crypto              Pwn (intro)
 Linux skills     Recon            Web               Forensics           Misc (advanced)
 Scripting        Networking       API hacking       Steganography       All categories
```

**Why this order?**
1. **Week 1 (Linux)** — You need shell skills for everything else
2. **Week 2 (OSINT/Recon)** — Reconnaissance comes before exploitation in any real engagement
3. **Week 3 (Web)** — Web is the most common category and the largest attack surface in modern software
4. **Week 4 (Crypto/Forensics)** — Requires comfortable scripting and understanding of data formats
5. **Week 5 (Systems)** — Ties everything together; assumes you can script, understand networks, and exploit web apps

---

## Category difficulty and accessibility

| Category | CSOT week | Beginner-friendly? | Prerequisites | Primary tools |
|----------|-----------|-------------------|---------------|---------------|
| **Misc / Linux** | 1, 5 | Very | None | bash, grep, find, git |
| **OSINT** | 2 | Yes | Google skills, patience | Google dorks, exiftool, WHOIS, Sherlock |
| **Web** | 3 | Yes (for basics) | HTTP knowledge, HTML/JS awareness | Burp Suite, browser DevTools, curl |
| **Crypto** | 4 | Easy challenges yes; hard ones require math | Number theory for RSA; programming for automation | CyberChef, Python, hashcat, SageMath |
| **Forensics / Stego** | 4 | Yes for file analysis; harder for memory forensics | File format knowledge, networking basics | Wireshark, binwalk, strings, Autopsy |
| **Reversing** | Post-course | No | Assembly language, C programming | Ghidra, IDA, gdb, radare2 |
| **Pwn** | Post-course | No | C, assembly, OS internals, exploit dev concepts | gdb, pwntools, checksec, ROPgadget |

### Interpreting this table

- **"Very beginner-friendly"** means you can start solving challenges with just the module content
- **"Post-course"** categories require significant self-study beyond CSOT; see [RESOURCES.md](../RESOURCES.md)
- Most CTFs weight web and crypto heavily, so Weeks 3 and 4 prepare you for the majority of real competition challenges

---

## Jeopardy vs attack-defense (deeper look)

### Jeopardy format

- All CSOT weekly CTFs use this format
- Challenges are independent — solving one doesn't help with another
- You can skip hard ones and focus on what you know
- **Strategy:** Solve easy challenges first for guaranteed points, then invest time in harder ones

### Attack-defense format

- Both teams run identical vulnerable services
- Flags rotate every few minutes (you must maintain access)
- Patching your own services is as important as attacking others
- **Strategy:** Defense first (patch obvious bugs), then attack teams that haven't patched yet

### When to try attack-defense

After completing CSOT (or at least through Week 3), you'll have enough skill for beginner attack-defense events. Look for:
- University-level competitions on CTFtime
- Events labeled "beginner-friendly" or "educational"
- Team events where experienced members can mentor newer players

---

## Choosing external CTFs

### Step 1: Filter by difficulty

On [CTFtime](https://ctftime.org/), look for:
- **Weight < 30** — Generally easier / educational events
- **"Beginner"** or **"University"** in the title
- Events with 500+ registered teams (more likely to have easy challenges)

### Step 2: Match to your current week

| Your progress | Recommended external practice |
|---------------|-------------------------------|
| Completing Week 1 | picoCTF Gym (General Skills), OverTheWire Bandit |
| Completing Week 2 | TryHackMe OSINT rooms, Geoguessr, OSINT Dojo |
| Completing Week 3 | PortSwigger Academy labs, TryHackMe web rooms, OWASP WebGoat |
| Completing Week 4 | CryptoHack, picoCTF (Crypto + Forensics categories) |
| Completing Week 5 | Any beginner jeopardy CTF; team up for 24–48h events |

### Step 3: Start with always-available platforms

Live CTFs have time pressure. Build skills first on platforms that are always available:

| Platform | Best for | Difficulty range |
|----------|----------|-----------------|
| [picoCTF Gym](https://picoctf.org/) | First-ever flags; builds confidence | Very easy → Medium |
| [TryHackMe](https://tryhackme.com/) | Guided learning paths with explanations | Easy → Medium |
| [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) | Linux skills (parallel to Week 1) | Easy → Medium |
| [CryptoHack](https://cryptohack.org/) | Interactive crypto (parallel to Week 4) | Easy → Hard |
| [PortSwigger Academy](https://portswigger.net/web-security) | Best web security labs available | Easy → Expert |
| [Hack The Box](https://www.hackthebox.com/) | Realistic full machines | Medium → Expert |
| [VulnHub](https://www.vulnhub.com/) | Downloadable vulnerable VMs | Medium → Hard |

### Step 4: Graduate to live events

After you're comfortable with platform challenges:

1. Find a team (or form one from CSOT classmates)
2. Pick a 24–48 hour weekend CTF on CTFtime
3. Set realistic goals ("solve 5 challenges" not "win")
4. Assign categories to team members based on strengths
5. Write up your solutions afterward (even partial attempts)

---

## Building your specialization

After the course, you'll naturally gravitate toward certain categories. Here's how to go deeper:

### Web specialist path

```
PortSwigger Academy (all labs) → Hack The Box web challenges
→ Bug bounty programs → OSWE certification
```

### Crypto specialist path

```
CryptoHack (all challenges) → picoCTF crypto → Cryptopals challenges
→ Academic crypto courses → CTF crypto at advanced level
```

### Forensics/DFIR specialist path

```
TryHackMe DFIR rooms → Autopsy/Volatility practice
→ SANS DFIR challenges → real incident response work
```

### Binary/Pwn specialist path (advanced)

```
pwnable.kr → ROP Emporium → Nightmare (binary exploitation course)
→ Hack The Box pwn challenges → advanced CTF teams
```

### OSINT specialist path

```
TryHackMe OSINT rooms → Trace Labs Search Party CTFs
→ Bellingcat workshops → OSINT investigations
```

---

## Recommended platforms summary (from your bookmarks)

| Platform | Best for | Start when |
|----------|----------|------------|
| [picoCTF](https://picoctf.org/) | First flags, confidence building | Week 1 |
| [TryHackMe](https://tryhackme.com/) | Guided learning with structure | Week 1 |
| [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) | Linux CLI mastery | Week 1 |
| [PortSwigger Academy](https://portswigger.net/web-security) | Web vulnerabilities | Week 3 |
| [CryptoHack](https://cryptohack.org/) | Cryptography | Week 4 |
| [Hack The Box](https://www.hackthebox.com/) | Realistic machines | Week 5+ |
| [CTFtime](https://ctftime.org/) | Finding live competitions | Week 5+ |

---

## Advanced resources (after this course)

For when you've completed CSOT and want to go further:

| Resource | Category | Difficulty |
|----------|----------|------------|
| [pwnable.kr](http://pwnable.kr/) | Binary exploitation | Hard |
| [ROP Emporium](https://ropemporium.com/) | Return-oriented programming | Hard |
| [SmashTheStack](http://www.smashthestack.org/) | Wargames (exploit dev) | Hard |
| [Nightmare](https://guyinatuxedo.github.io/) | Binary exploitation course | Hard |
| [Cryptopals](https://cryptopals.com/) | Applied cryptography | Medium–Hard |
| [SANS Holiday Hack](https://www.holidayhackchallenge.com/) | All categories | Medium |

See [RESOURCES.md](../RESOURCES.md) for the full collection.

---

## Next module

[kali-setup.md](kali-setup.md) — Setting up your Linux environment so you can start practicing the commands in the following modules.
