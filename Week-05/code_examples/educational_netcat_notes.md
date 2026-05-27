# Educational netcat notes (not a weaponized payload)

CSOT does **not** ship a reverse-shell payload for use outside lab VMs.

## Concepts

| Term | Meaning |
|------|---------|
| Bind shell | Victim listens; you connect |
| Reverse shell | Victim connects back to your listener |
| Listener | `nc -lvnp 4444` on your attack box |

## Legal use

Only in TryHackMe VPN, HTB, or course Docker hosts.

## Learn more

- TryHackMe “Net Sec Challenge” / “Intro to Port Redirection”  
- [GTFOBins](https://gtfobins.github.io/) — how binaries can spawn shells when misconfigured  

Build understanding before using Metasploit `shell` stages.
