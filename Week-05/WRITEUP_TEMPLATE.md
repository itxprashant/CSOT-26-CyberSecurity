# CTF writeup template

A good writeup is not a transcript. It's the story of how you solved a challenge, written so that **a future you** (or a teammate, or a hiring manager) can learn the lesson in 10 minutes without re-doing the work. The template below mirrors the structure used in industry IR reports — see [incident-response-lite.md](incident-response-lite.md) for the connection — so the habits you build here generalise.

**How to use this file:**

1. Copy this template into your CTF folder (e.g. `writeups/forensics-log.md`).
2. Fill in each section as you solve.
3. Keep notes *as you work*, not after the fact. Stale memory invents wrong details.
4. Submit the filled writeup for the CTF assignment.

The bottom half of this file is a **worked example** so you can see the template applied. Use it as a reference for tone and depth.

---

## Template

```
# <Challenge name>

| | |
|---|---|
| **Event / week**     | <CSOT26 Week 5 capstone>                 |
| **Category**         | <Linux / Web / Crypto / PrivEsc / etc.>  |
| **Points**           | <e.g. 200>                               |
| **Difficulty**       | <Easy / Medium / Hard>                   |
| **Date solved**      | <YYYY-MM-DD>                             |
| **Solver(s)**        | <Your name / team>                       |
| **Time to solve**    | <e.g. 35 min>                            |

---

## Description (verbatim from challenge)

<Paste the README.md or challenge prompt here, unchanged. This anchors the writeup against the
exact wording, which sometimes matters when re-reading later.>

---

## Initial recon

<What you saw the first 60 seconds. Files present, sizes, file types, obvious hints.>

```
$ ls -la
...

$ file <artifact>
...
```

---

## Approach

A numbered list of what you actually tried, in order — including the dead ends.

1. <First thing you tried, with the result.>
2. <Next thing, why you tried it after step 1.>
3. <Continue until the solve.>

Dead ends are useful — they teach you (and future-you) which paths look promising but aren't.

---

## Key insight

The "aha" moment. One paragraph: what fact, when you noticed it, made the rest fall into place.

---

## Solution

The minimum sequence of commands or code that reproduces the solve. Should be runnable as-is.

```bash
# command-line solve
...
```

```python
# code-based solve
...
```

---

## Flag

```
csot26{...}
```

---

## Tools used

A bulleted list. Anything you used; one-line description of what for.

- `grep` — searching the haystack
- `base64 -d` — decoding payload.txt
- `python3 code_examples/port_scanner.py` — port discovery

---

## Lessons learned

What did this teach you? Three useful framings:

- **Technique:** What new skill or trick did you pick up?
- **Gotcha:** What stumbling block will you remember next time?
- **Defender view:** How would a defender prevent or detect this in production?

---

## Remediation (defender's view)

For challenges that mirror real vulnerabilities, write 2–4 lines on the remediation a defender would apply in production. This trains the muscle you'll use in IR work and in writing bug-bounty reports.

---

## References

Any links, docs, blog posts, or HackTricks pages you used.

- <link 1>
- <link 2>
```

---

## Worked example

Below is the template filled in for a hypothetical (fictional, scope-safe) challenge. Use it as the calibration for tone, depth, and length.

---

# Forensics Log

| | |
|---|---|
| **Event / week**     | CSOT26 Week 5 capstone                   |
| **Category**         | Forensics / Linux                        |
| **Points**           | 200                                      |
| **Difficulty**       | Easy                                     |
| **Date solved**      | 2026-05-31                               |
| **Solver(s)**        | Asha (team `null-byte`)                  |
| **Time to solve**    | 6 minutes                                |

---

## Description (verbatim from challenge)

> grep csot26 forensics-log/app.log

The CTF README is a one-liner. The artefact is a single small log file.

---

## Initial recon

```
$ ls -la
-rw-r--r-- 1 user user  56 May 25 23:06 app.log
-rw-r--r-- 1 user user 128 May 25 23:06 README.md

$ file app.log
app.log: ASCII text

$ wc -lc app.log
1  56 app.log
```

One line, 56 bytes. The challenge is a recap of basic `grep`; the file is small enough to `cat` and read by eye.

---

## Approach

1. `cat app.log` — saw the line `ERROR csot26{...} failed login admin` immediately.
2. Confirmed by the literal command from the README: `grep csot26 app.log`.
3. Looked at the context — the flag sits inside an `ERROR ... failed login admin` record, which would make this a real *failed login* incident in a production log. Worth noting in the lessons section.

No dead ends — the challenge is intentionally simple as a Week-1 recap. The exercise is in *how* you write up the trivial case, not the solve itself.

---

## Key insight

`grep` is a power tool for log triage, and the flag-format prefix `csot26{...}` is the cheapest possible anchor to search for. In real IR work you'd search for IOC patterns the same way — IP addresses, suspicious user agents, command-and-control domain fragments. Same skill, same syntax.

---

## Solution

```bash
grep -E 'csot26\{[^}]+\}' app.log
```

Output:

```
ERROR csot26{capstone_log_forensics} failed login admin
```

Or, equivalently, using the [`code_examples/log_parser.py`](code_examples/log_parser.py) helper:

```bash
python3 ../../code_examples/log_parser.py app.log 'csot26\{[^}]+\}'
```

---

## Flag

```
csot26{capstone_log_forensics}
```

---

## Tools used

- `cat`, `wc`, `file` — initial recon
- `grep -E` — extracting the flag with an extended regex anchor
- `code_examples/log_parser.py` — the Week-5 Python helper, same job

---

## Lessons learned

- **Technique:** Even on a one-line log, run `wc -l` and `file` first. Habit is cheap; surprise is expensive when the artefact is multi-GB.
- **Gotcha:** `grep csot26` matches the flag fine here, but in a noisier log you'd want `grep -oE 'csot26\{[^}]+\}'` (the `-o` prints only the match) to pull just the flag out. Worth using by default once the log is bigger.
- **Defender view:** The flag is wedged into an `ERROR ... failed login admin` record. In production, the *real* signal would be the surrounding "failed login admin" pattern — anything that looks like a brute-force burst followed by a success line is the highest-fidelity SSH/web-auth alert.

---

## Remediation (defender's view)

If this were a real environment:

1. Move plaintext credentials out of log lines. Even the *absence* of password content here is good; many sloppy apps log the attempted password.
2. Rate-limit failed logins per source IP at the app or WAF layer.
3. Forward auth events to a SIEM with a rule for "≥10 failed logins followed by success in 60 seconds."
4. Run [`grep`-style](https://github.com/SigmaHQ/sigma) detections on the central log stream, not on individual hosts — attackers tamper with local logs first.

---

## References

- [`code_examples/log_parser.py`](code_examples/log_parser.py) — the helper script
- [HackTricks — Linux forensics](https://book.hacktricks.xyz/forensics/basic-forensic-methodology/linux-forensics)
- [`grep` POSIX manual](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/grep.html)

---

## How long should writeups be?

| Challenge difficulty | Reasonable length |
|----------------------|-------------------|
| Easy (≤200 pts)      | 1–2 pages         |
| Medium (200–400 pts) | 2–4 pages         |
| Hard (≥400 pts)      | 3–6 pages         |
| Capstone / Final boss| As long as it deserves |

Padding hurts the writeup. Cut anything that doesn't earn its line. A 1-page writeup that's *useful* beats a 5-page one that's a transcript.

---

## What makes a strong writeup

Use this checklist when documenting CTF solves (for your portfolio or if coordinators request writeups after an event). **Writeups are not separately scored unless announced on Discord** — the CTF platform scores flags only.

| Criterion | Why it matters |
|-----------|----------------|
| Reproducible solution (commands runnable as-is) | Others (and future you) can follow the path |
| Clear explanation of the approach (including dead ends) | Shows reasoning, not just the answer |
| Key insight identified and explained | Proves you understood the bug, not just the flag |
| Defender-side remediation noted | Connects offense to how you'd fix it |
| Formatting, references, tools section complete | Makes the writeup usable as a reference |

---

## A few more practical tips

- **Keep a `notes.md` open from the start.** Paste commands and outputs into it as you go. Convert into the writeup at the end.
- **Screenshot only when text won't do.** A Burp window, an unusual font rendering, an actual desktop UI — fine. Terminal output should be text.
- **Redact sparingly.** For CSOT, full flags are OK in writeups *after the event ends*. During an active event, leave them out.
- **Use code fences (`bash`, `python`, etc.) for tool output.** It renders predictably on GitHub and inside Notion.
- **Link to the artefact** under `../CTFs/week-XX/<challenge>/` if you discuss it — makes the writeup re-runnable.
- **Always end with a "lessons learned."** That's the section future you will actually re-read.
