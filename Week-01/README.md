# Week 1 — Security mindset, digital safety & Linux toolbox

Build safe habits and the command-line skills used in every CTF category. This is the foundation week — everything you learn here (navigating Linux, writing scripts, thinking about threats) carries forward into every subsequent week.

---

## Why this week matters

Every security tool runs on Linux. Every CTF challenge requires reading files, piping output, and scripting repetitive tasks. Before you can exploit a web app or crack a cipher, you need to be comfortable in a terminal. This week also establishes the **safety mindset**: offensive security work is only legal and ethical within carefully defined boundaries, and protecting your own accounts and devices is the first step.

---

## Learning objectives

By the end of this week, you should be able to:

- [ ] Explain the CIA triad and basic threat modeling for your personal setup
- [ ] Identify common phishing indicators (domain tricks, header mismatches, suspicious OAuth scopes)
- [ ] Describe CTF competition formats and the major challenge categories
- [ ] Set up a working Linux environment (Kali via WSL2, VirtualBox, or native)
- [ ] Navigate the filesystem, manage files, and understand permission bits
- [ ] Use pipes, redirection, and `grep`/`find` to extract information from files
- [ ] Write bash scripts with variables, loops, conditionals, and functions
- [ ] Perform basic local reconnaissance (network info, listening ports, running processes)
- [ ] Solve the Week 1 CTF challenges using only Linux CLI skills

---

## Modules (read in order)

Each module builds on the previous one. Start with the conceptual material, then move to hands-on tooling.

| # | Module | What you'll learn | Time estimate |
|---|--------|-------------------|---------------|
| 1 | [introduction-to-cybersecurity.md](introduction-to-cybersecurity.md) | What cybersecurity is, red/blue/purple team roles, career paths, legal boundaries | 20 min |
| 2 | [digital-safety.md](digital-safety.md) | Threat modeling, phishing detection, credential hygiene, lab safety practices | 30 min |
| 3 | [ctf-fundamentals.md](ctf-fundamentals.md) | CTF formats, challenge categories, competition mindset, tool starter pack | 20 min |
| 4 | [ctf-category-roadmap.md](ctf-category-roadmap.md) | How CSOT maps to CTF categories, choosing external CTFs, progression advice | 15 min |
| 5 | [kali-setup.md](kali-setup.md) | Installing Kali Linux (WSL2 / VirtualBox / native), verifying tools work | 30–60 min |
| 6 | [linux-cli.md](linux-cli.md) | Filesystem navigation, file operations, search, permissions, pipes, archives | 45 min |
| 7 | [bash-scripting.md](bash-scripting.md) | Variables, conditionals, loops, functions, practical CTF scripting patterns | 45 min |
| 8 | [basic-recon-commands.md](basic-recon-commands.md) | System info, network enumeration, DNS, filesystem hunting, process inspection | 30 min |

**Total reading time:** ~4 hours (spread across Mon–Tue)

---

## Recommended workflow

```
Day 1 (Mon):  Modules 1–4 (concepts) + set up Kali/WSL (Module 5)
Day 2 (Tue):  Modules 6–8 (hands-on) + try commands on your own system
Day 3 (Wed):  OverTheWire Bandit levels 0–10 + TryHackMe Linux rooms
Day 4 (Thu):  Bandit levels 11–15 + TryHackMe Cyber Security 101
Day 5 (Fri):  Complete assignments + review CTF hints
Day 6–7:      Weekend CTF (8 challenges, 2–3 hours)
```

---

## External practice platforms

These reinforce what you read in the modules. Do them on Wed–Thu.

| Platform | What to do | Link |
|----------|------------|------|
| OverTheWire Bandit | Levels 0–15 (SSH, file reading, permissions, grep, sort, base64) | [overthewire.org/wargames/bandit/](https://overthewire.org/wargames/bandit/) |
| TryHackMe | "Linux Fundamentals Part 1, 2, 3" rooms | [tryhackme.com](https://tryhackme.com/) |
| TryHackMe | "Cyber Security 101" path (first few modules) | [tryhackme.com](https://tryhackme.com/) |
| picoCTF Gym | General Skills category (beginner challenges) | [play.picoctf.org/practice](https://play.picoctf.org/practice) |
| Linux Journey | Interactive Linux tutorial (grasshopper level) | [linuxjourney.com](https://linuxjourney.com/) |

---

## Assignments

Due by Friday before the CTF. These are graded.

1. **Scavenger hunt** — Extract the [scavenger_hunt.tar.xz](../../CTFs/week-01/scavenger_hunt.tar.xz) archive and follow the trail of clues across nested directories. Requires: `tar`, `find`, `grep`, `cat`, reading hidden files.

2. **Bash scripts** — Three scripting tasks of increasing complexity. See [assignments/README.md](assignments/README.md) for full specifications, examples, and rubric.

3. **Account setup** — Create accounts on all four platforms below and bookmark three upcoming CTFs from CTFtime:
   - [Hack The Box](https://www.hackthebox.com/)
   - [TryHackMe](https://tryhackme.com/)
   - [PortSwigger Academy](https://portswigger.net/web-security)
   - [CTFtime](https://ctftime.org/)

---

## Weekend CTF

**Location:** [../../CTFs/week-01/](../../CTFs/week-01/)  
**Challenges:** 8 (Linux, scripting, git, containers)  
**Duration:** 2–3 hours  
**Format:** Jeopardy-style, individual

| Challenge | Category | Difficulty | Skills tested |
|-----------|----------|------------|---------------|
| welcome-agent | Warmup | Easy | Docker, reading stdout |
| path-navigator | Linux | Easy | Filesystem navigation, hidden files |
| log-parser | Linux | Easy | grep, awk, log analysis |
| binary-permissions | Linux | Medium | File permissions, SUID concepts |
| archive-archaeology | Linux | Medium | Nested archives, tar/gzip/xz |
| git-forensics-lite | Git | Medium | Git log, diff, deleted commits |
| process-hunter | Linux | Medium | /proc filesystem, environment variables |
| script-me | Scripting | Medium | Debugging broken bash scripts |

**Tips for success:**
- Read each challenge's `README.md` carefully — titles and descriptions contain hints
- Use `file` command on unknown files to identify their type
- Check hidden files (`.filename`) and hidden directories
- Look at file permissions with `ls -la`
- Remember: the flag format is always `csot26{...}`

---

## Key concepts to remember

| Concept | Why it matters this week |
|---------|-------------------------|
| CIA triad | Framework for thinking about what you're protecting |
| Threat model | Identifies what could go wrong before it does |
| Least privilege | Don't run everything as root; limit access to what's needed |
| File permissions | CTF challenges often hide flags behind permission gates |
| Pipes | Chaining commands (`grep | sort | uniq -c`) is how you analyze data efficiently |
| `/proc` filesystem | Linux exposes process information as files — useful for forensics |
| `.gitignore` and `.env` | Secrets should never be committed; labs teach you why |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| WSL won't install | Run PowerShell as Administrator; ensure virtualization is enabled in BIOS |
| `permission denied` on a script | `chmod +x script.sh` to make it executable |
| Can't find a file | `find / -name "filename" 2>/dev/null` — the `2>/dev/null` suppresses permission errors |
| Docker not working | Ensure Docker Desktop is running; try `sudo` on Linux |
| Command not found | Install with `sudo apt install <package-name>` |
| Bandit SSH won't connect | Check port: `ssh -p 2220 bandit0@bandit.labs.overthewire.org` |

---

## Advanced Reading

For those who want to go deeper this week:

### Books

- *The Linux Command Line* — William Shotts — [linuxcommand.org](https://linuxcommand.org/tlcl.php) (free PDF)
- *Linux Basics for Hackers* — OccupyTheWeb — Kali-focused practical skills

### Online courses / paths

- [TryHackMe — Complete Beginner](https://tryhackme.com/path/outline/presecurity) — structured onboarding
- [HackTheBox — Starting Point](https://www.hackthebox.com/) — guided machines after invite challenge
- [W3Schools Cybersecurity](https://www.w3schools.com/cybersecurity/) — concise concept overviews

### Tools to explore

- [tmux](https://github.com/tmux/tmux/wiki) — terminal multiplexer for CTF sessions
- [ExplainShell](https://explainshell.com/) — decode complex one-liners
- [CyberChef](https://gchq.github.io/CyberChef/) — encodings preview for later weeks

### Challenge platforms

- [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) — levels 16–34 after finishing 0–15
- [cmdchallenge](https://cmdchallenge.com/) — quick CLI puzzles
- [picoCTF Gym — General Skills](https://play.picoctf.org/practice)

### Videos / creators

- [NetworkChuck](https://www.youtube.com/c/NetworkChuck) — Linux and cybersecurity fundamentals
- [John Hammond](https://www.youtube.com/c/JohnHammond010) — beginner CTF walkthroughs
- [IppSec](https://www.youtube.com/c/ippsec) — HackTheBox machines (attempt first, then watch)

---

## What's next

Week 2 takes the reconnaissance commands you learned here and applies them to real-world information gathering — DNS enumeration, network scanning with nmap, and open-source intelligence (OSINT). The bash skills you built will be used to automate recon tasks.

**Next:** [Week 2 — OSINT & open-source investigation](../Week-02/)
