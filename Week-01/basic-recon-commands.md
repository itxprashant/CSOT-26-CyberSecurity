# Basic reconnaissance commands

Reconnaissance (recon) is the process of gathering information about a system — what's running, who's using it, what's exposed, and where the interesting data lives. In the attack lifecycle, recon is always the first phase. In CTFs, it's how you figure out what a challenge is asking you to find.

**Critical rule:** Only run these commands on systems you're authorized to test. For this course that means: your own VM, course CTF infrastructure, and platforms like TryHackMe/HTB that explicitly allow it.

---

## Why recon matters

Before you can exploit anything, you need to answer:
- What services are running?
- What operating system and versions?
- What users exist?
- What files are accessible?
- What ports are listening?
- What processes hold interesting data?

These commands give you that picture. This module covers **local** reconnaissance (on a system you already have access to). Week 2 covers **remote** reconnaissance (scanning external targets).

---

## System information

These commands tell you about the machine you're currently on:

```bash
# Kernel and OS info
uname -a              # Full kernel version string
# Example output: Linux kali 6.1.0-kali9 #1 SMP x86_64 GNU/Linux

cat /etc/os-release   # Distribution name and version
# Useful fields: NAME, VERSION, ID

# Who am I?
whoami                # Current username
id                    # Current user's UID, GID, and group memberships
# Example: uid=1000(kali) gid=1000(kali) groups=1000(kali),27(sudo)

# Who else is here?
w                     # Who is logged in and what they're doing
who                   # Simpler list of logged-in users
last | head -20       # Recent login history
```

### Why this matters in CTFs

- `id` tells you your privilege level — if you're in the `sudo` or `docker` group, you may have paths to root
- `uname -a` reveals the kernel version — old kernels may have known exploits
- `/etc/os-release` helps you find OS-specific vulnerabilities or package locations

---

## User enumeration

```bash
# List all user accounts
cat /etc/passwd
# Format: username:x:UID:GID:description:home:shell

# Just the usernames
cut -d: -f1 /etc/passwd

# Users with login shells (not system accounts)
grep -v "nologin\|false" /etc/passwd | cut -d: -f1

# Password hashes (requires root)
sudo cat /etc/shadow
# Format: username:hash:lastchange:min:max:warn:inactive:expire

# Who can use sudo?
grep -E "^sudo|^wheel" /etc/group
# Or check sudoers
sudo cat /etc/sudoers 2>/dev/null
sudo -l              # What CAN I run with sudo?
```

### CTF pattern: checking sudo privileges

```bash
sudo -l
# If you see something like:
# (ALL) NOPASSWD: /usr/bin/vim
# That means you can run vim as root, which is a privilege escalation vector
# In vim: :!bash → gives you a root shell
```

---

## Network information (local)

Understanding the network configuration of a machine you're on:

```bash
# Network interfaces and IP addresses
ip addr                # Modern (preferred)
ifconfig               # Legacy (still common in CTFs)

# Default gateway and routing table
ip route               # Where does traffic go?
# Example: default via 192.168.1.1 dev eth0 → gateway is 192.168.1.1

# Listening ports — what services are running?
ss -tulpn              # TCP/UDP listening ports with process names
# -t: TCP, -u: UDP, -l: listening, -p: process name, -n: numeric ports
netstat -tulpn         # Legacy equivalent

# Active connections
ss -tupn               # Current established connections

# ARP table (nearby devices)
arp -a                 # Or: ip neigh

# DNS configuration
cat /etc/resolv.conf   # Which DNS servers does this machine use?

# Hosts file (local DNS overrides)
cat /etc/hosts         # Manually mapped hostnames
```

### Reading `ss -tulpn` output

```
State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN  0       128     0.0.0.0:22          0.0.0.0:*          users:(("sshd",pid=1234))
LISTEN  0       511     127.0.0.1:3306      0.0.0.0:*          users:(("mysqld",pid=5678))
```

| Local Address | Meaning |
|---------------|---------|
| `0.0.0.0:22` | SSH listening on all interfaces (accessible from network) |
| `127.0.0.1:3306` | MySQL only on localhost (not network-accessible) |
| `:::80` | HTTP on all IPv6 interfaces |

---

## DNS lookups (authorized domains only)

DNS (Domain Name System) translates hostnames to IP addresses. Querying DNS reveals infrastructure:

```bash
# Basic lookup
nslookup example.com
dig example.com

# Specific record types
dig A example.com +short         # IPv4 address
dig AAAA example.com +short      # IPv6 address
dig MX example.com +short        # Mail servers
dig NS example.com +short        # Name servers
dig TXT example.com +short       # TXT records (often contain interesting info)
dig CNAME sub.example.com +short # Canonical name (aliases)

# Reverse DNS (IP → hostname)
dig -x 8.8.8.8 +short

# Query a specific DNS server
dig @8.8.8.8 example.com

# All records
dig ANY example.com +short
```

### CTF pattern: flags in TXT records

Organizations sometimes store verification tokens, SPF records, or (in CTFs) flags in DNS TXT records:

```bash
dig TXT ctf.example.com +short
# "csot26{dns_records_are_public}"
```

---

## Simple connectivity checks

```bash
# Is this host alive?
ping -c 3 192.168.1.1            # Send 3 ICMP packets

# Can I reach this port?
nc -zv host 80                   # Zero-I/O mode (just check connectivity)
nc -zv host 1-1000               # Check a range (slow but works)

# HTTP check
curl -I https://example.com      # Headers only (quick check if web server responds)
curl -s https://example.com      # Silent mode (just the body)
curl -v https://example.com      # Verbose (shows TLS handshake, headers, everything)

# Download a file
wget https://example.com/file.txt         # Saves to current directory
curl -O https://example.com/file.txt      # Same with curl
```

---

## Filesystem hunting (CTF-style)

In CTF challenges (and in real penetration tests after gaining access), you need to find interesting files:

### Finding flags

```bash
# Search for flag format in all readable files
grep -r "csot26{" / 2>/dev/null

# Find files named "flag"
find / -name "*flag*" 2>/dev/null

# Find recently modified files (challenge authors just placed them)
find / -mmin -60 -type f 2>/dev/null     # Modified in last hour

# Find hidden files (starting with .)
find / -name ".*" -type f 2>/dev/null | head -20
```

### Finding sensitive files

```bash
# Configuration files
find / -name "*.conf" -type f 2>/dev/null | head -20
find / -name "*.ini" -type f 2>/dev/null
find / -name "*.env" -type f 2>/dev/null

# Database files
find / -name "*.db" -o -name "*.sqlite*" 2>/dev/null

# SSH keys
find / -name "id_rsa" -o -name "id_ed25519" 2>/dev/null

# Files with "password" in the name
find / -iname "*password*" -type f 2>/dev/null

# World-readable files in sensitive locations
find /root -readable 2>/dev/null
find /home -readable -type f 2>/dev/null
```

### Finding privilege escalation vectors

```bash
# SUID binaries (run as owner, usually root)
find / -perm -4000 -type f 2>/dev/null

# SGID binaries
find / -perm -2000 -type f 2>/dev/null

# World-writable files
find / -perm -0002 -type f 2>/dev/null

# World-writable directories
find / -perm -0002 -type d 2>/dev/null

# Files owned by root but writable by you
find / -user root -writable 2>/dev/null

# Cron jobs (scheduled tasks)
cat /etc/crontab
ls -la /etc/cron*
crontab -l                        # Current user's cron
```

---

## Process inspection

Running processes often contain sensitive information in their environment variables, command lines, or open files:

```bash
# List all processes
ps aux                            # Full listing
ps aux | grep -i "interesting"    # Filter for specific processes

# Process tree (shows parent-child relationships)
pstree

# What's using the most CPU/memory?
top                               # Interactive (q to quit)
ps aux --sort=-%mem | head -10    # Top 10 by memory
```

### The `/proc` filesystem (CTF goldmine)

Every running process has a directory in `/proc/<PID>/`:

```bash
# Environment variables of a process (often contains secrets!)
cat /proc/<PID>/environ | tr '\0' '\n'
# This might reveal: DATABASE_URL, API_KEY, FLAG, SECRET_TOKEN

# Command line that started the process
cat /proc/<PID>/cmdline | tr '\0' ' '

# Current working directory of the process
ls -la /proc/<PID>/cwd

# Open file descriptors
ls -la /proc/<PID>/fd/

# Memory maps (what libraries are loaded)
cat /proc/<PID>/maps

# For the current process (self)
cat /proc/self/environ | tr '\0' '\n'
```

### CTF pattern: flag in process environment

```bash
# A CTF challenge might run a process with the flag as an environment variable
# First, find the process
ps aux | grep "challenge"
# Note the PID (e.g., 1234)

# Then read its environment
cat /proc/1234/environ | tr '\0' '\n' | grep "FLAG"
# FLAG=csot26{process_memory_is_readable}
```

---

## History and logs

```bash
# Command history (what was run previously?)
history
cat ~/.bash_history

# System logs
ls /var/log/
cat /var/log/syslog | tail -50    # Recent system events
cat /var/log/auth.log | tail -50  # Authentication events (logins, sudo)
journalctl -n 50                  # Systemd journal (recent entries)

# Application logs
find /var/log -name "*.log" -mtime -1  # Logs modified today
```

---

## Putting it together: a quick enumeration workflow

When you first get access to a system (in a CTF or authorized pentest):

```bash
#!/bin/bash
# quick-enum.sh — Fast local enumeration

echo "=== IDENTITY ==="
whoami
id
hostname

echo ""
echo "=== SYSTEM ==="
uname -a
cat /etc/os-release 2>/dev/null | grep -E "^(NAME|VERSION)="

echo ""
echo "=== NETWORK ==="
ip addr | grep "inet " | grep -v 127.0.0.1
ss -tulpn 2>/dev/null | grep LISTEN

echo ""
echo "=== SUDO ==="
sudo -l 2>/dev/null

echo ""
echo "=== SUID BINARIES ==="
find / -perm -4000 -type f 2>/dev/null

echo ""
echo "=== INTERESTING FILES ==="
find / -name "*flag*" -type f 2>/dev/null
find / -name "*.env" -type f 2>/dev/null
find /home -readable -name ".*" -type f 2>/dev/null

echo ""
echo "=== CRON JOBS ==="
cat /etc/crontab 2>/dev/null
ls /etc/cron.d/ 2>/dev/null
```

---

## Ethics reminder

These commands are powerful. With great power comes responsibility:

| Authorized | Not authorized |
|------------|----------------|
| Your own VM/WSL | IIT campus network |
| Course CTF containers | Other students' machines |
| TryHackMe/HTB (while on their VPN) | Random internet servers |
| Platforms with explicit permission | Your friend's laptop "as a joke" |

Unauthorized scanning or enumeration of systems is illegal in most jurisdictions, even if you don't actually exploit anything.

---

## What's next

In **Week 2**, you'll apply these concepts to remote targets:
- **nmap** for sophisticated port scanning
- **DNS enumeration** at scale
- **OSINT** — gathering information from public sources
- **Automation** — scripting recon workflows

The local enumeration skills from this module are the foundation. Once you compromise a remote system (Week 3+), you'll run these same commands on the target to understand what you've accessed.

---

## Further reading

- [HackTricks — Linux privilege escalation](https://book.hacktricks.xyz/linux-hardening/privilege-escalation) — comprehensive checklist
- [GTFOBins](https://gtfobins.github.io/) — Unix binaries that can be exploited for privilege escalation
- [LinPEAS](https://github.com/carlospolop/PEASS-ng/tree/master/linPEAS) — automated Linux enumeration script
- [PayloadsAllTheThings — Linux privesc](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Linux%20-%20Privilege%20Escalation.md)

---

## Next week

[Week 2 — OSINT & open-source investigation](../Week-02/) — Taking reconnaissance beyond the local system.
