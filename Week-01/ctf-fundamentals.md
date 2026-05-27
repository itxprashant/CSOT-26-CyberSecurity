# CTF fundamentals

## What is a Capture The Flag (CTF)?

A CTF (Capture The Flag) is a cybersecurity competition where participants solve security-related challenges to find hidden strings called **flags**. Each flag proves you successfully completed the challenge — whether that meant exploiting a web vulnerability, decrypting a cipher, reverse-engineering a binary, or finding a hidden file.

Think of it like a puzzle competition, but the puzzles are real-world security scenarios distilled into bite-sized problems.

**CSOT flag format:** `csot26{descriptive_text_here}`

Every flag in this course follows this format. If you find a string matching this pattern, you've solved the challenge. Submit it exactly as found (case-sensitive, including braces).

---

## Why CTFs matter for learning

| Benefit | Explanation |
|---------|-------------|
| **Hands-on practice** | Reading about SQL injection is different from actually exploiting one |
| **Time pressure** | Competitions force you to work efficiently and prioritize |
| **Pattern recognition** | After solving 50 challenges, you start recognizing common vulnerability patterns instantly |
| **Community** | CTF teams share knowledge, writeups, and tools |
| **Portfolio** | Writeups and rankings demonstrate skill to employers |
| **Fun** | Solving a challenge after hours of work is genuinely satisfying |

CTFs are how most professional pentesters and security researchers built their skills. They're also increasingly used in hiring — companies run CTFs to identify talented candidates.

---

## Competition formats

### Jeopardy-style (what CSOT uses)

Independent challenges organized by category and difficulty. Solve them in any order. Points are awarded per challenge (sometimes decreasing as more teams solve it).

```
┌──────────────────────────────────────────────────────┐
│  Web        │  Crypto     │  Forensics  │  Misc      │
│─────────────│─────────────│─────────────│────────────│
│  100 pts ✓  │  100 pts ✓  │  100 pts    │  100 pts ✓ │
│  200 pts    │  200 pts    │  200 pts ✓  │  200 pts   │
│  300 pts    │  300 pts    │  300 pts    │  300 pts   │
│  500 pts    │  500 pts    │  500 pts    │  500 pts   │
└──────────────────────────────────────────────────────┘
```

**Pros:** You can focus on categories you're strong in; no dependency between challenges
**Cons:** Doesn't simulate real-world attack/defense scenarios

### Attack-defense

Teams run vulnerable services and must simultaneously:
- **Patch** their own services to prevent attacks
- **Exploit** other teams' services to steal their flags
- **Maintain availability** (services must stay running)

**Pros:** Realistic; tests both offensive and defensive skills simultaneously
**Cons:** Requires strong fundamentals; chaotic for beginners; needs significant infrastructure

### King of the Hill

A hybrid format where teams compete to gain and maintain access to a shared machine. The team that holds root longest wins points.

### CSOT format

All CSOT weekly CTFs are **jeopardy-style**:
- 8 challenges per week
- 2–3 hour time window
- Individual (except Week 5 which is team-based)
- Challenges stay available after the event for practice

---

## Challenge categories explained

Each category represents a different domain of security knowledge:

### Misc / General Skills

**What it tests:** Linux commands, scripting, logic, encoding, creative thinking

**Example:** "The flag is somewhere in this 10,000-line log file. Find the line that contains an anomalous IP address."

**Skills needed:** grep, awk, sort, uniq, bash scripting, patience

### Cryptography

**What it tests:** Breaking or decoding ciphers, understanding cryptographic primitives

**Example:** "This message was encrypted with a Caesar cipher: `pfbg26{uryyb_jbeyq}`. Decrypt it."

**Skills needed:** Understanding of encoding (Base64, hex), classical ciphers (Caesar, Vigenère, XOR), modern crypto concepts (RSA, AES), mathematical reasoning

**Tools:** CyberChef, Python scripting, hashcat, John the Ripper

### Forensics

**What it tests:** Analyzing digital evidence — files, logs, memory dumps, disk images, network captures

**Example:** "Here's a PCAP file from a network capture. Someone exfiltrated data over DNS. Reconstruct the message."

**Skills needed:** Wireshark, file carving, log analysis, understanding of file formats, metadata extraction

**Tools:** Wireshark, Autopsy, `strings`, `binwalk`, `foremost`, `volatility`

### Steganography

**What it tests:** Finding data hidden within other data (images, audio, text)

**Example:** "This PNG image looks normal, but there's a flag hidden in it."

**Skills needed:** Understanding LSB (least significant bit) encoding, file format internals, metadata

**Tools:** `steghide`, `stegsolve`, `binwalk`, `exiftool`, `zsteg`

### Web

**What it tests:** Exploiting vulnerabilities in web applications

**Example:** "This login page is vulnerable to SQL injection. Get the admin password from the database."

**Skills needed:** HTTP protocol, cookies/sessions, SQL, JavaScript, server-side logic

**Tools:** Burp Suite, browser DevTools, `curl`, `sqlmap`, `dirbuster`

### OSINT (Open Source Intelligence)

**What it tests:** Finding information using publicly available sources

**Example:** "This photo was taken somewhere in Delhi. Identify the exact location using clues in the image."

**Skills needed:** Google dorking, image reverse search, WHOIS, social media analysis, geolocation

**Tools:** Google, `exiftool`, Maltego, Shodan, social media platforms

### Pwn / Binary Exploitation

**What it tests:** Exploiting compiled programs (buffer overflows, format strings, ROP chains)

**Example:** "This C program has a buffer overflow. Exploit it to spawn a shell."

**Skills needed:** Assembly language, memory layout, calling conventions, exploit development

**Tools:** `gdb`, `pwntools`, `checksec`, `ROPgadget`

**Note:** This is advanced. CSOT doesn't cover binary exploitation in depth, but Week 5 gives you a taste. See [RESOURCES.md](../RESOURCES.md) for self-study paths.

### Reverse Engineering

**What it tests:** Understanding how a program works without source code

**Example:** "This program checks a license key. Figure out what key it accepts."

**Skills needed:** Assembly reading, decompiler usage, understanding control flow, recognizing algorithms

**Tools:** Ghidra, IDA Free, `objdump`, `ltrace`, `strace`

**Note:** Also advanced and mostly post-course. CSOT introduces basic concepts in Week 5.

---

## The CTF mindset

Solving CTF challenges is different from homework — there's no single method that always works. Develop these habits:

### 1. Read the challenge description carefully

Titles, descriptions, and even author names often contain hints. A challenge called "Shift Happens" is probably about a Caesar/shift cipher. A challenge tagged "easy" that nobody has solved might have an unusual twist.

### 2. Enumerate before you exploit

Don't jump to complex attacks. Start with:
- What files are provided? Run `file` on each one.
- What does `strings` reveal?
- Is there a web page? View source.
- What are the permissions? What user am I?

### 3. Google everything

Someone has seen this pattern before. Search for:
- Error messages (exact, in quotes)
- Tool names + "CTF writeup"
- File format + "hidden data"
- The challenge title itself (for past similar challenges)

### 4. Take structured notes

```markdown
## Challenge: XYZ (200pts, Web)
### Observations
- Login page at /login
- Cookie contains base64-encoded JSON
- Source reveals commented-out admin endpoint

### Attempts
- Tried default creds admin:admin → failed
- Decoded cookie: {"role": "user", "id": 5}
- Changed role to "admin" → FLAG FOUND

### Flag: csot26{cookie_monster_strikes}
```

### 5. Know when to move on

If you've spent 45 minutes on a challenge with zero progress:
- Ask for a hint (if available)
- Switch to a different challenge and come back later
- Fresh eyes often see what tired ones miss

### 6. Write writeups

After the CTF ends, write up your solutions. This:
- Solidifies your understanding
- Helps teammates who didn't solve it
- Builds a personal reference for future similar challenges
- Contributes to the community (post on your blog or CTFtime)

---

## Platforms to join this week

Create accounts on all of these. You'll use them throughout the course.

| Platform | URL | Why | Priority |
|----------|-----|-----|----------|
| CTFtime | https://ctftime.org/ | Find live competitions, track your rating, read writeups | Required |
| TryHackMe | https://tryhackme.com/ | Guided rooms with step-by-step instructions | Required |
| Hack The Box | https://www.hackthebox.com/ | Realistic machines and challenges (harder) | Required |
| picoCTF Gym | https://play.picoctf.org/practice | Beginner-friendly, always-available challenges | Required |
| PortSwigger Academy | https://portswigger.net/web-security | Best free web security labs (for Week 3) | Required |
| OverTheWire | https://overthewire.org/wargames/ | SSH-based wargames; Bandit teaches Linux | Recommended |
| CryptoHack | https://cryptohack.org/ | Interactive crypto challenges (for Week 4) | Recommended |

---

## Tool starter pack

These are the minimum tools you need for Week 1. Each week adds more.

### Already on your system (if you set up Kali/Linux)

| Tool | Purpose | Example use |
|------|---------|-------------|
| `bash` | Shell and scripting | Everything |
| `grep` | Search text with patterns | `grep -r "csot26{" .` |
| `find` | Locate files | `find / -name "*.flag" 2>/dev/null` |
| `file` | Identify file types | `file mystery_document` |
| `strings` | Extract readable text from binaries | `strings suspicious.bin \| grep csot` |
| `base64` | Encode/decode Base64 | `echo "aGVsbG8=" \| base64 -d` |
| `xxd` | Hex dump | `xxd file.bin \| head` |
| `wget` / `curl` | Download files | `wget http://challenge-url/file` |
| `tar` / `gzip` / `xz` | Archive extraction | `tar -xJf archive.tar.xz` |
| `git` | Version control and forensics | `git log --all --oneline` |

### Browser-based tools

| Tool | Purpose | URL |
|------|---------|-----|
| CyberChef | Swiss army knife for encodings, ciphers, data transforms | https://gchq.github.io/CyberChef/ |
| Browser DevTools | Inspect HTTP, JavaScript, cookies, network requests | F12 in any browser |
| ExplainShell | Understand complex commands by breaking them apart | https://explainshell.com/ |

### Install later (by Week 3–4)

- **Burp Suite Community** — HTTP proxy and web testing toolkit
- **Wireshark** — Network packet analyzer
- **hashcat** / **John the Ripper** — Password hash crackers
- **binwalk** — Firmware/file analysis and extraction
- **exiftool** — Image/document metadata reader

---

## How scoring typically works

### Fixed points

Each challenge has a set point value based on estimated difficulty:

| Points | Difficulty | Expected solve rate |
|--------|-----------|---------------------|
| 100 | Easy | 80%+ of participants |
| 200 | Medium | 40–60% |
| 300 | Hard | 15–30% |
| 500 | Expert | < 10% |

### Dynamic scoring (used by some CTFs)

Points decrease as more teams solve the challenge. A challenge starting at 500 points might drop to 200 after 50 solves. This rewards teams that solve hard challenges early.

CSOT uses **fixed scoring** for simplicity.

---

## Common mistakes beginners make

| Mistake | Fix |
|---------|-----|
| Overthinking easy challenges | Start with the simplest explanation; "easy" means easy |
| Not reading the challenge fully | Re-read the title, description, and hints before trying complex attacks |
| Forgetting to check file metadata | Always run `file`, `strings`, `exiftool` on provided files |
| Not looking at source code | `view-source:` in browser, or Ctrl+U on web challenges |
| Skipping hidden files | `ls -la` shows dotfiles; check `.hidden`, `.git/`, etc. |
| Not URL-decoding | Copy the URL carefully; `%20` is space, `%7B` is `{` |
| Submitting modified flags | Submit exactly as found — case, braces, and spacing all matter |

---

## Recommended reading

- [What are CTFs? (GeeksforGeeks)](https://www.geeksforgeeks.org/ethical-hacking/what-is-ctfs-capture-the-flag/)
- [TryHackMe — CTF deep dive](https://tryhackme.com/resources/blog/ctf-deep-dive-how-to-choose-the-right-category-for-your-skill-level)
- [Snyk — CTF types](https://snyk.io/articles/ctf/ctf-types/)
- [CTF Sites collection](https://ctfsites.github.io/)
- [CTF Wiki](https://ctf-wiki.org/en/) — Comprehensive reference for all categories
- [CTF 101](https://ctf101.org/) — Quick category overviews with examples

---

## Next module

[ctf-category-roadmap.md](ctf-category-roadmap.md) — How this course maps to CTF categories and how to choose what to practice externally.
