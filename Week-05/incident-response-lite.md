# Incident response lite

Every offensive module in Week 5 has a defender's counterpart. **Incident response** (IR) is that counterpart in its institutional form: the structured way an organisation handles an active intrusion from the moment an alert fires to the moment the post-mortem is filed. This module is the "lite" version — what a junior responder, a SOC L1 analyst, or a developer on call would actually do for the first 24 hours of an incident.

Even if you never work as a responder, two things make this knowledge load-bearing:

1. **Bug bounty / pentest reports become readable.** Half the value of a security finding is in the remediation guidance, and remediation lives in IR vocabulary.
2. **You can write your own engagement reports in a recognisable shape.** Your CTF writeups using [WRITEUP_TEMPLATE.md](WRITEUP_TEMPLATE.md) are mini-IR reports.

This module is the one that ties the whole week together: every "the defender sees X" note in [post-exploitation.md](post-exploitation.md), [privilege-escalation.md](privilege-escalation.md), and [detection-evasion-awareness.md](detection-evasion-awareness.md) feeds into the analyst workflow here.

> **Authorized targets only — even for IR practice.** Doing live IR on a friend's compromised machine without their explicit authorization is not "helping," it's unauthorized access. IT Act 2000 §43 applies regardless of intent. Practice IR on: your own VMs that you deliberately compromised, TryHackMe / HackTheBox forensics rooms, public datasets (DFIR.training, MalwareBazaar, BlueTeamLabsOnline), and CSOT's [../../CTFs/week-05/forensics-log/](../../CTFs/week-05/forensics-log/) artefact.

---

## The PICERL lifecycle

The industry-standard incident response model — codified in NIST SP 800-61 — has six phases. The acronym is **PICERL**.

```
┌─────────────────┐
│  P repare       │   Before any incident: contacts, tools, baselines, IR plan
└─────────────────┘
        ↓
┌─────────────────┐
│  I dentify      │   "Is this real?" — triage, scope, severity
└─────────────────┘
        ↓
┌─────────────────┐
│  C ontain       │   Stop the bleeding — isolate hosts, kill sessions, block accounts
└─────────────────┘
        ↓
┌─────────────────┐
│  E radicate     │   Remove the attacker — close vulns, remove persistence, rotate creds
└─────────────────┘
        ↓
┌─────────────────┐
│  R ecover       │   Bring systems back to known-good — restore, monitor, validate
└─────────────────┘
        ↓
┌─────────────────┐
│  L essons       │   Post-mortem, remediation roadmap, detection improvements
└─────────────────┘
```

Each phase has its own outputs. Skipping a phase — usually "just contain it and move on" — is how breaches turn into re-breaches.

### Phase 1 — Prepare

Done before the incident. Easy to neglect. The phase you'll be **most grateful for** during the panic of an active incident.

| Asset | Why it matters |
|-------|----------------|
| **IR plan** | Written runbook with phases, roles, escalation contacts |
| **Asset inventory** | "What's on the network?" answered in advance |
| **Contact list** | Security lead, IT, legal, comms, external IR retainer |
| **Logging in place** | Centralised, redundant, tamper-resistant (`auth.log`, journald, app logs, NetFlow, EDR) |
| **Backups, tested** | Untested backups are not backups |
| **Baselines** | What does normal look like? You can't recognise "weird" without one |
| **Forensic-grade tools** | `dd`, FTK Imager, KAPE, Velociraptor, memory dumpers — staged and ready |

A junior responder typically inherits this state, doesn't build it. But the first incident you walk into often reveals which preparation pieces are missing.

### Phase 2 — Identify

An alert just fired. Three questions in this order:

1. **Is it real?** (true positive vs false positive)
2. **What's the scope?** (one host, ten hosts, the whole estate)
3. **How severe?** (production data exposure? auth compromise? unauthorized but contained code execution?)

A junior responder's job during identification is mostly enrichment — pulling context around the alert so the senior responder/IR manager can decide how to act.

#### Triaging a single alert

Imagine your SIEM fires:

```
[ALERT] sshd: Multiple failed logins for 'root' from 203.0.113.42, then success 11:24:13
```

The L1 workflow:

```bash
# 1. Get the source IP into context
whois 203.0.113.42                         # who owns it
# (might be a VPN provider, residential ISP, a TOR exit, an internal misconfigured app)

# 2. Look for similar events
grep '203.0.113.42' /var/log/auth.log
# how many other accounts has this IP tried?

# 3. Look at what the session did after success
last -i -F | head -20
journalctl _COMM=sshd | grep -A 20 '11:24'

# 4. Find the session's child processes (audit/EDR)
journalctl _SYSTEMD_UNIT=sshd.service --since='11:24'

# 5. Check user's baseline — does this account ever SSH in?
last -F username | head -5
```

If steps 2–5 turn up nothing scary, it's likely a brute-force probe that got lucky (or a forgotten dev key with a weak password). If they turn up *anything* (sudo commands, new files in `/tmp`, outbound connections you don't recognise), you're in an incident and escalate immediately.

#### Initial scoping questions

The L1 should have answers to these within 15 minutes of escalating:

- Which host(s) does the alert involve?
- Which user account(s)?
- Which time window?
- What other alerts fired in the same window?
- What does the affected host *do*? (web tier? domain controller? lab box?)
- Is the host in production?
- Who owns the host? (call them, in parallel with the investigation)

### Phase 3 — Contain

Stop the bleeding. Two flavours:

**Short-term containment** — fast, possibly imperfect:
- Block the source IP at the firewall
- Disable the affected account
- Pull the host's network cable (literally) or detach from VPC
- Kill the suspicious process

**Long-term containment** — careful, reversible:
- Rebuild the host from a known-good image
- Rotate all credentials accessible from the host
- Tighten WAF rules
- Patch the exploited vulnerability network-wide

Always preserve **evidence first**. A junior responder's instinct is "pull the plug" — but pulling power destroys memory, which often contains the malware's secrets, decryption keys, and IOCs. The rule:

> **Capture volatile evidence before non-volatile.**

The order of volatility (RFC 3227):

1. CPU registers, cache
2. Memory (RAM)
3. Running processes
4. Network state (connections, ARP table)
5. Temporary files
6. Disk
7. Remote logs
8. Physical media (USB sticks, backup tapes)

For a junior responder this maps to a simple ordering:

```bash
# 1. dump RAM first if you have the tools
sudo lime-forensics /tmp/mem.lime          # Linux memory acquisition
# or
sudo dd if=/dev/mem of=/mnt/usb/mem.raw    # crude but works on older kernels

# 2. capture process and network state
ps auxf > /tmp/ps.txt
ss -tupn > /tmp/ss.txt
ss -anp > /tmp/conn.txt
lsof -n > /tmp/lsof.txt
netstat -i > /tmp/netif.txt

# 3. copy critical logs *off* the host before any tampering
scp /var/log/auth.log /var/log/syslog /var/log/audit/audit.log responder@evidence:./
journalctl --since "24 hours ago" > /tmp/journal_24h.txt

# 4. now isolate
sudo iptables -A INPUT -j DROP   # crude — or pull from VPC, more controlled
```

Then, and only then, escalate to full disk imaging or rebuild.

### Phase 4 — Eradicate

Now the attacker is contained; remove their access fully.

| Action | Why |
|--------|-----|
| Remove all backdoors / web shells / cron persistence | Map every persistence technique from [post-exploitation.md](post-exploitation.md) |
| Rotate every credential the host could read | Database creds, API keys, SSH keys, service tokens |
| Reset all user passwords that authenticated to the host | Especially privileged accounts |
| Revoke all OAuth grants associated with compromised accounts | Often missed; attackers add their own |
| Patch the exploited vulnerability | And every other instance of the same vuln in the estate |
| Rebuild the host (don't trust a forensically-imaged disk) | If feasible — a "cleaned" host is rarely as clean as a fresh one |

Common mistake: focusing on the initial vector and ignoring lateral movement. The attacker who popped a public-facing web server probably used that foothold to grab credentials and move to *other* hosts. Eradication on the entry point alone leaves footholds elsewhere.

### Phase 5 — Recover

Bring affected services back. Validate they're clean. Watch closely.

| Step | Why |
|------|-----|
| Restore from known-good backups (predating compromise) | Anything from after intrusion start might be tainted |
| Monitor restored systems intensively | If the attacker had a foothold elsewhere, they'll be back |
| Maintain heightened logging for at least 30 days | Catches re-entry attempts |
| Validate end-to-end functionality | The host works; the auth chain works; the data is intact |
| Reset any users who were locked out as part of containment | Communicate clearly with end users |

### Phase 6 — Lessons learned

The post-mortem, written within a week. Three sections, every time:

| Section | Content |
|---------|---------|
| **Timeline** | Minute-by-minute (or hour-by-hour) of attacker actions and our response |
| **Root cause(s)** | The technical vulnerability *and* the process gap that let it through |
| **Action items** | Specific, owned, dated — what changes to prevent recurrence |

A good post-mortem is **blameless**. The goal is system improvement, not finger-pointing. ("How did we let an outdated WordPress plugin reach production?" not "Who deployed the outdated plugin?")

---

## The junior responder's Linux toolkit

When a host you can SSH to is suspicious, these commands answer most first-pass questions. Memorise them.

### Identity and access

```bash
who                          # who is currently logged in
w                            # same, plus what they're doing
last -i -n 30                # last 30 logins with source IP
lastb -i -n 30               # failed logins (requires root)
cat /etc/passwd              # users — anything UID 0 besides root?
cat /etc/shadow              # users with passwords (vs ! for "no password")
grep -E ':0:[0-9]+:' /etc/passwd   # users with UID 0 explicitly
getent group sudo            # who can use sudo
```

A second UID 0 user other than `root` is a high-confidence sign of compromise.

### Running processes

```bash
ps auxf                      # process tree
ps -ef --forest              # alternative tree view
pstree -p                    # cleaner tree
ps auxf | awk '$11 ~ "/tmp"' # processes running out of /tmp (always suspicious)
ls -la /proc/<PID>/exe       # what executable is this PID running
ls -la /proc/<PID>/cwd       # working directory
cat /proc/<PID>/cmdline | tr '\0' ' '   # exact command line
cat /proc/<PID>/environ | tr '\0' '\n'  # env vars (often have IOCs)
```

### Network connections

```bash
ss -tupn                     # connections + listening with PIDs (replaces netstat)
ss -tn state established     # only established TCP
lsof -i                      # files-over-network — connections per process
ss -p | sort -u              # unique connections
arp -an                      # ARP table — neighbours
ip route                     # routing table
```

An established connection from a server to a random internet IP on port 443 is *usually* benign (an SDK or update). One on port 4444 or to an unusual ASN is not.

### File-system timeline

```bash
# what's been modified in the last hour
find / -mmin -60 -type f 2>/dev/null | grep -v '/proc\|/sys\|/run'

# what's been modified in the last day
find / -mtime -1 -type f 2>/dev/null | grep -v '/proc\|/sys\|/run'

# new SUID/SGID binaries (compare to your baseline)
find / -perm -4000 -type f 2>/dev/null > /tmp/suid_now.txt
diff /tmp/suid_baseline.txt /tmp/suid_now.txt

# files in /tmp that shouldn't be there
ls -la /tmp /var/tmp /dev/shm

# unusual modification times — files dated in the future, or all dated identically
stat /usr/bin/* | grep Modify | sort -u | head
```

### Persistence enumeration

```bash
# cron at every level
cat /etc/crontab
ls -la /etc/cron.{hourly,daily,weekly,monthly,d}
for u in $(cut -d: -f1 /etc/passwd); do
  c=$(sudo crontab -u "$u" -l 2>/dev/null)
  [ -n "$c" ] && echo "=== $u ===" && echo "$c"
done
systemctl list-timers --all

# new services
systemctl list-unit-files --type=service --state=enabled
ls -la /etc/systemd/system/ /lib/systemd/system/ ~/.config/systemd/user/

# shell profile hooks
grep -l . /etc/profile /etc/profile.d/* /etc/bash.bashrc 2>/dev/null
for u in $(cut -d: -f6 /etc/passwd | grep ^/home); do
  ls -la "$u"/.bashrc "$u"/.profile "$u"/.bash_profile 2>/dev/null
done

# new SSH authorized keys
find /home /root -name authorized_keys -exec ls -la {} \; 2>/dev/null
for f in $(find /home /root -name authorized_keys 2>/dev/null); do
  echo "=== $f ==="
  cat "$f"
done
```

### Logs to triage first

```bash
# authentication
tail -n 200 /var/log/auth.log
journalctl _COMM=sshd --since '2 hours ago'

# sudo activity
journalctl _COMM=sudo --since 'today'

# kernel — for kernel exploit traces
dmesg | tail -50

# package activity
tail -n 100 /var/log/dpkg.log         # Debian/Ubuntu
tail -n 100 /var/log/yum.log          # RHEL/CentOS

# web (path varies)
tail -n 200 /var/log/nginx/access.log
tail -n 200 /var/log/apache2/access.log
tail -n 200 /var/log/nginx/error.log

# generic
journalctl --since 'today' -p err
```

### A first-pass triage script

The whole sequence collapsed into something you'd run from a USB or a known-good copy of `/bin/bash`:

```bash
#!/bin/bash
# triage.sh — first 5 minutes on a possibly-compromised Linux host
# Run as root; outputs to /tmp/triage-$(hostname)-$(date +%s)/

set -u
OUT="/tmp/triage-$(hostname)-$(date +%s)"
mkdir -p "$OUT"

echo "== identity =="                       | tee "$OUT/00_identity.txt"
{ whoami; id; hostname; uname -a; date; }   | tee -a "$OUT/00_identity.txt"

ps auxf                  > "$OUT/01_ps.txt"
ss -tupn                 > "$OUT/02_net.txt"
last -F -n 50            > "$OUT/03_logins.txt" 2>/dev/null
lastb -F -n 50           > "$OUT/04_failed_logins.txt" 2>/dev/null
who                      > "$OUT/05_who.txt"

find / -mmin -60 -type f 2>/dev/null  | grep -v '/proc\|/sys\|/run' > "$OUT/10_recent_60min.txt"
find / -perm -4000 -type f 2>/dev/null > "$OUT/11_suid.txt"
ls -la /tmp /var/tmp /dev/shm 2>/dev/null > "$OUT/12_tmp.txt"

cat /etc/crontab /etc/cron.d/* 2>/dev/null > "$OUT/20_cron_system.txt"
for u in $(cut -d: -f1 /etc/passwd); do
  c=$(crontab -u "$u" -l 2>/dev/null) && [ -n "$c" ] && echo "=== $u ===" >> "$OUT/21_cron_users.txt" && echo "$c" >> "$OUT/21_cron_users.txt"
done

for f in /home/*/.ssh/authorized_keys /root/.ssh/authorized_keys; do
  [ -f "$f" ] && { echo "=== $f ==="; cat "$f"; } >> "$OUT/22_ssh_keys.txt"
done

cp /var/log/auth.log "$OUT/30_auth.log" 2>/dev/null
journalctl --since '24 hours ago' > "$OUT/31_journal_24h.txt" 2>/dev/null

tar czf "/tmp/$(basename "$OUT").tgz" -C /tmp "$(basename "$OUT")"
echo "evidence bundle: /tmp/$(basename "$OUT").tgz"
```

That script collects enough evidence to escalate confidently — and the bundle is portable, so a senior responder can inspect it from elsewhere.

---

## The Windows side, briefly

A junior responder on Windows reaches for:

| Tool | What it does |
|------|--------------|
| `Get-EventLog Security -Newest 200` | Recent security events (4624 logon, 4625 fail, 4688 process) |
| `Get-CimInstance Win32_Process` | Process tree with command line |
| `Get-Service \| Where-Object Status -eq Running` | Active services |
| `Get-ScheduledTask \| Where-Object State -eq Ready` | Scheduled tasks |
| `Get-LocalUser`, `Get-LocalGroupMember Administrators` | Local accounts |
| `autoruns` (Sysinternals) | Persistence locations, all categories |
| `procexp` (Sysinternals) | Process explorer with signature info |
| `Tcpview` | Network connections per process |
| `eventvwr` (GUI) | Event Viewer |
| `KAPE` | Forensic artefact collector |
| `Velociraptor` | Endpoint visibility / live forensics framework |

The MITRE ATT&CK to Sysmon-rule mapping is the same idea as on Linux: every offensive technique has a defender's signature.

---

## Log sources every responder should know

| Source | OS | Lives where | What it tells you |
|--------|----|-------------|--------------------|
| `auth.log` / `secure` | Linux | `/var/log/auth.log` | Logins, sudo, SSH key auth |
| `syslog` / `messages` | Linux | `/var/log/syslog` | Kernel, services |
| `journalctl` | Linux (systemd) | binary store | Combined service logs |
| `audit.log` | Linux + auditd | `/var/log/audit/audit.log` | Syscall-level activity |
| `dpkg.log` / `yum.log` | Linux | `/var/log/` | Package install/removal |
| Web access/error | Web | varies | HTTP traffic, error stacks |
| **Security event log** (4624/4625/4672/4688) | Windows | Event Viewer | Logons, special privilege, process create |
| **Sysmon** | Windows | Event Viewer | Detailed process tree + network |
| **PowerShell ScriptBlock log** | Windows | Event Viewer | Full PS commands |
| **AWS CloudTrail** | Cloud | S3 + Athena | API calls, including credentials use |
| **AWS VPC Flow Logs** | Cloud | S3 | NetFlow for VPC traffic |
| **EDR telemetry** | Either | Vendor cloud | Process, network, file, registry events |
| **Application logs** | App | varies | What the app itself logged |

The "what to look at first" depends on the alert. Auth-related → `auth.log` + Windows 4624/4625. Process-related → Sysmon + ps tree. Network exfil → NetFlow + EDR network events.

---

## Common patterns to spot

The library every responder builds over years. The starter set:

| Pattern | Indicates |
|---------|-----------|
| Many failed logins, then a success | Successful brute force or credential stuffing |
| Logon from a country/ASN the user has never used | Account compromise |
| Process spawned outside `/usr/bin` or `C:\Windows\System32\` | LOLBin abuse, dropped binary |
| `web-user → sh → curl → /tmp/...` | Web shell + payload download |
| `whoami; id; hostname; ipconfig; netstat` in quick succession | Discovery burst |
| Outbound TCP to non-corporate ASN on port 443 sustained | C2 channel |
| New scheduled task / cron job created in the last 24 h | Persistence |
| LSASS handle from a user-mode process | Credential dumping |
| `/etc/passwd` modified outside a package operation | Privilege escalation |
| SMB connection to internet | Exfil over SMB (or NTLM relay attempt) |
| Browser-store files read by a non-browser process | Credential theft |

When you read incident reports — DFIR Report, Mandiant M-Trends, CrowdStrike Global Threat Report — you'll see these patterns over and over. The job is recognising them in your own logs.

---

## Chain of custody

If the incident might lead to disciplinary action, regulatory disclosure, or law-enforcement involvement, your evidence has to stand up to scrutiny later. The rules are simple:

1. **Capture, then hash.** SHA-256 every artefact at acquisition time. Re-hash before any analysis.
2. **Document every transfer.** Who handed what to whom, when, and how.
3. **Don't modify originals.** Always work on copies. Originals stay sealed.
4. **Use forensically-sound tools.** `dd` (or `dc3dd`) for disk; `lime` or `winpmem` for memory. Mounted always read-only.
5. **Keep a contemporaneous log.** Notes written *as you work*, not reconstructed later.

A simple custody log header in any analysis document:

```
== Evidence custody ==
Item:        host_box01_root_disk.dd
Acquired:    2026-05-27 11:55 IST by P.K. (responder #1)
SHA-256:     7f3c1a... (matches acquisition hash)
Source:      /dev/sda1 of host box01, powered off
Storage:     evidence-vault, locker #4, sealed bag #B12
Chain:
  11:55  acquired
  12:30  hashed by P.K.
  14:00  handed to S.R. (analyst) for triage
  17:30  returned to vault
```

For CTF purposes this is mostly theoretical. For real IR work it's the difference between an artefact you can use in a HR proceeding and one you can't.

---

## When to escalate

| Signal | Escalate to |
|--------|-------------|
| Production data access by an unknown source | IR manager + legal + business owner |
| Ransomware indicators (encrypted files, ransom note) | IR manager + executive + retainer-IR firm |
| Active lateral movement | IR manager + network team |
| Data leaving the environment | IR manager + comms + counsel |
| Suspected nation-state TTPs | Senior IR + intel + possibly law enforcement |
| Anything you genuinely cannot explain after 30 min of triage | Senior responder; don't sit on it |

Speed beats embarrassment. The cost of escalating something that turned out benign is one awkward Slack message. The cost of *not* escalating a real incident is measured in millions.

---

## CTF tie-in — the [forensics-log](../../CTFs/week-05/forensics-log/) artefact

The [`../../CTFs/week-05/forensics-log/`](../../CTFs/week-05/forensics-log/) challenge ships an `app.log` file with the flag embedded in an error line. The whole CTF challenge is solvable with `grep csot26 app.log` — but the *learning* in the challenge is the workflow:

1. Read the `README` to understand the scope.
2. `wc -l app.log`, `head app.log`, `tail app.log` — orient.
3. `grep -i 'error\|fail\|warn' app.log` — typical first pass for an IR analyst.
4. Notice the flag in the ERROR line.

That's the same pattern you'd apply against a real `/var/log/syslog` of unknown contents. Build the habit.

---

## Tying CTF writeups to IR writeups

Your [WRITEUP_TEMPLATE.md](WRITEUP_TEMPLATE.md) for the capstone deliberately uses the same skeleton as an IR report. The mapping:

| CTF writeup section | IR report equivalent |
|---------------------|----------------------|
| Description | Alert description / incident summary |
| Initial recon | Identification / scoping |
| Approach | Investigation timeline |
| Tools used | Tooling and data sources |
| Key insight | Root cause |
| Solution (commands, code) | Containment / eradication steps |
| Lessons learned | Lessons learned + action items |

Doing the writeups well now will make you a competent IR reporter later, with no extra effort. Both audiences want the same thing: clarity on what happened, what was done, and what to do next time.

---

## Further reading

- [NIST SP 800-61 r2](https://csrc.nist.gov/pubs/sp/800/61/r2/final) — the original IR lifecycle reference. Free PDF, ~80 pages, dense but worth scanning.
- [SANS Incident Handler's Handbook](https://www.sans.org/white-papers/33901/) — readable summary of the same lifecycle.
- [The DFIR Report](https://thedfirreport.com/) — read 3-5 cases; they show how the lifecycle plays out in real intrusions.
- [TryHackMe — SOC Level 1 path](https://tryhackme.com/path-action/soc-level-1) — guided, hands-on; the best free intro.
- [Awesome Incident Response](https://github.com/meirwah/awesome-incident-response) — curated tool list.
- [Velociraptor](https://docs.velociraptor.app/) — open-source endpoint visibility framework worth knowing.
- [Eric Zimmerman's tools](https://ericzimmerman.github.io/) — Windows forensic toolkit, free.

---

## Career paths from here

A short map of where this material leads professionally:

| Role | Primary toolkit |
|------|------------------|
| **SOC analyst (L1/L2)** | SIEM, EDR, log triage, ticketing |
| **Incident responder / DFIR** | Forensic imaging, memory analysis, malware triage |
| **Detection engineer** | Sigma/YARA rules, MITRE ATT&CK mapping, SOAR playbooks |
| **Threat hunter** | Same telemetry as SOC, but proactive — "what's wrong that hasn't alerted yet?" |
| **Red teamer / pentester** | Weeks 2–4 + ongoing tradecraft research |
| **AppSec** | Week 3 web content + secure-SDLC, threat modelling, code review |
| **Cloud security** | Week 5 cloud module + IaC + identity |
| **Security engineering** | Build and run security tools at scale |

Every role above pays you to know what's in this course, then deepens one slice of it. The capstone CTF is your last guided step; whichever role you pick from here, the path is more reps.

---

## Next module

[WRITEUP_TEMPLATE.md](WRITEUP_TEMPLATE.md) — A polished template for your capstone writeup. The IR lessons in this module map directly onto the template's sections; the template is what you'll fill in after the weekend CTF.
