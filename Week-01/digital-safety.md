# Digital safety for builders

You already know how computers work. This module covers **operational security (OpSec)** — the same hygiene that professional developers and security engineers practice before touching offensive tools. Think of it as wearing safety equipment before entering a chemistry lab.

---

## Why this matters before anything else

In the coming weeks you'll install security tools, connect to vulnerable machines, and run exploits. Without proper hygiene:
- A tool you download could be malware disguised as a security utility
- Your credentials could end up in a public git repo
- You could accidentally scan a production network instead of your lab
- A phishing email could compromise your IIT account while you're focused on CTF prep

**Principle:** Protect yourself first. Then learn to protect (and test) others.

---

## Threat modeling (lightweight version)

A threat model answers: "What could go wrong, and how likely is it?" You don't need a formal framework yet — just ask four questions about any system you care about:

| Question | Your laptop/accounts | Course VM |
|----------|---------------------|-----------|
| **What are the assets?** | GitHub tokens, `.env` files, browser sessions, IIT SSO credentials, project databases, SSH keys | CTF flags, tools you installed, notes |
| **Who are the adversaries?** | Credential stuffers, phishing campaigns, malicious packages, nosy classmates | None (it's disposable) |
| **What are the attack vectors?** | Phishing email, supply-chain attack via npm/pip, leaked API key, malicious browser extension | Accidentally breaking something |
| **What controls mitigate risk?** | MFA, password manager, secret scanning, `.gitignore`, network isolation | Snapshots, re-install if broken |

### Working through an example

**Scenario:** You store a GitHub personal access token in a `.env` file in your project directory.

| Question | Answer |
|----------|--------|
| Asset | The token (grants push access to your repos) |
| Adversary | Automated scrapers that scan public repos for secrets |
| Vector | You accidentally `git add .` and push the `.env` file |
| Control | `.gitignore` entry for `.env`, GitHub secret scanning alerts, using short-lived tokens |

**Practice:** Do this exercise for your own setup. What's the most valuable credential on your machine? What would happen if it leaked?

---

## CSOT lab rules

Before we go further, the ground rules for offensive work in this course:

- Offensive techniques run **only** on course infrastructure, your personal VMs, or platforms that explicitly allow it (HTB, THM, picoCTF, OverTheWire, PortSwigger)
- Never scan or attack IIT networks, other students' machines, or public websites
- If you're unsure whether a target is in scope, **ask first**
- Run labs in isolated environments (WSL/VM) — not directly on your daily driver if avoidable

---

## Evaluating untrusted URLs and sites

During CTF research you'll encounter unknown tools, sites, and links. Before visiting or entering credentials:

### Step 1: Check with ScamAdviser

[ScamAdviser](https://www.scamadviser.com/) — paste any domain to get an automated Trust Score based on domain age, SSL configuration, hosting reputation, and reported scams.

| Score | Interpretation | Action |
|-------|---------------|--------|
| 81–100 | Few negative signals | Probably fine, but still verify independently |
| 41–80 | Mixed signals | Don't enter credentials or payment info; dig deeper |
| 0–40 | High risk | Avoid entirely; treat as hostile |

**Important limitations:**
- Brand-new legitimate sites score low (no history)
- Sophisticated scammers clone trusted brands perfectly
- ScamAdviser is a triage tool, not proof of safety

### Step 2: Cross-reference

| Check | How |
|-------|-----|
| WHOIS/registrar | `whois domain.com` — when was it registered? By whom? |
| DNS records | `dig domain.com` — does it resolve to expected infrastructure? |
| Official source | Did you get the link from the [course WhatsApp group](https://chat.whatsapp.com/BJN7duZuObq1gbGPrped0y) or this repository? Or from an unsolicited email? |
| Search engine | Google `"domain.com" scam` or `"domain.com" review` |
| Browser extension | [ScamAdviser Chrome Extension](https://chromewebstore.google.com/detail/scamadviser/lcmofkcgjjagmhodenahpocfkpopjdci) for passive checks |

### Real-world example

You find a site claiming to offer "free Burp Suite Pro license keys for students." Red flags:
- Domain registered 2 weeks ago (WHOIS)
- No HTTPS or self-signed certificate
- ScamAdviser score: 22
- Not linked from portswigger.net (the official source)

**Verdict:** Malware distribution site. Close and report.

---

## Credential exposure monitoring

### Have I Been Pwned (HIBP)

[haveibeenpwned.com](https://haveibeenpwned.com/) — Troy Hunt's free service that aggregates data from known breaches.

**What to do:**

1. **Check your email** — Enter your IIT and personal email addresses. HIBP tells you which breaches included that email.

2. **Check passwords** — Use [Pwned Passwords](https://haveibeenpwned.com/Passwords) to check if a password hash exists in breach databases. It uses **k-anonymity** (sends only the first 5 characters of the hash), so your actual password never leaves your machine.

3. **Set up notifications** — Subscribe to alerts for future breaches involving your email.

### If you're in a breach

| Step | Action |
|------|--------|
| 1 | Change the password on the breached service immediately |
| 2 | If you reused that password anywhere else, change it there too |
| 3 | Enable MFA on the affected account |
| 4 | Check for unauthorized OAuth apps (GitHub → Settings → Applications; Google → Security → Third-party access) |
| 5 | Review recent login activity for suspicious sessions |

### For developers: secret monitoring

Leaked credentials aren't just passwords. As a developer, also watch for:

| Secret type | Where it leaks | Detection |
|-------------|---------------|-----------|
| API keys | Public git repos, Pastebin, error messages | GitHub secret scanning, `gitleaks`, `trufflehog` |
| SSH private keys | Accidentally committed `.ssh/id_rsa` | Pre-commit hooks |
| Database connection strings | Hardcoded in source, Docker configs | Environment variable injection instead |
| JWT signing secrets | Committed config files | Rotate and use vault services |

We'll cover `gitleaks` in more depth in [Week 4](../Week-04/).

---

## Phishing and social engineering — technical detection

Phishing is the #1 initial access vector for real-world breaches. As a technical person, you can spot attacks that non-technical users miss:

### Domain tricks

| Technique | Example | How to spot |
|-----------|---------|-------------|
| Typosquatting | `goggle.com`, `githuh.com` | Read the domain letter by letter |
| Punycode/IDN | `xn--pple-43d.com` (looks like `apple.com` with Cyrillic 'а') | Check the URL bar encoding; browsers show `xn--` prefix |
| Subdomain abuse | `login.microsoft.com.evil.com` | The actual domain is `evil.com`; everything before is a subdomain |
| TLD swaps | `company.io` vs `company.com` | Verify which TLD the real company uses |
| Path confusion | `legitimate.com/login` → redirects to `evil.com` | Watch the address bar after clicking |

### Email header analysis

When an email looks suspicious, view the raw headers:
- **Gmail:** Open email → three dots → "Show original"
- **Outlook:** Open email → File → Properties → Internet Headers

| Header | What to check |
|--------|---------------|
| `From` | Display name vs actual address (e.g., "GitHub Security" but from `random@gmail.com`) |
| `Return-Path` | Where bounces go — should match the `From` domain |
| `Received` | Trace the path of the email; first `Received` header is the origin |
| SPF result | `spf=pass` means the sending server is authorized for that domain |
| DKIM result | `dkim=pass` means the email wasn't tampered with in transit |
| `Reply-To` | Sometimes different from `From` — attacker collects responses at a different address |

### Attachment red flags

| Type | Risk |
|------|------|
| `.html` files | Often contain fake login pages that POST credentials to attacker servers |
| Office docs with macros | Macro malware is still common; never enable macros from unknown sources |
| `.exe`, `.scr`, `.bat` disguised with double extensions | `invoice.pdf.exe` — Windows hides the real extension by default |
| Password-protected archives | Evades antivirus scanning; legitimate senders explain why in the email |

### OAuth consent attacks

Malicious apps request broad permissions through legitimate-looking OAuth flows:

```
"CSOT Helper Tool" wants to:
  ✓ Read your email
  ✓ Manage your repositories
  ✓ Access your contacts
```

**Rule:** Only grant OAuth access to apps you specifically sought out. Revoke anything suspicious at:
- GitHub: Settings → Applications → Authorized OAuth Apps
- Google: myaccount.google.com → Security → Third-party apps

### Practice

Take the [Google Phishing Quiz](https://phishingquiz.withgoogle.com/) — it tests whether you can distinguish real emails from phishing attempts using the signals above.

---

## Password and account security

### Password manager (non-negotiable)

Use a password manager (Bitwarden, 1Password, KeePassXC) to generate and store unique credentials for every service. Why:

- **Breach containment** — when one service leaks, only that password is compromised
- **No mental overhead** — you don't need to remember 50+ passwords
- **Auto-fill** — reduces phishing risk because the manager checks the domain before filling

### Multi-factor authentication (MFA)

| MFA method | Security level | Notes |
|------------|---------------|-------|
| Hardware key (YubiKey) | Highest | Phishing-resistant; can't be intercepted |
| TOTP app (Authy, Google Authenticator) | High | Time-based codes; better than SMS |
| Push notification | Medium | Vulnerable to "MFA fatigue" (spamming prompts until user accepts) |
| SMS | Low | SIM-swapping attacks can intercept codes |

Enable MFA on: GitHub, Google, IIT SSO, any service storing sensitive data.

### CTF-specific account hygiene

- Use a **burner email or alias** for CTF platform signups (not your primary inbox)
- **Never** reuse your banking, IIT, or work passwords on random CTF platforms
- Different password for every CTF site (password manager handles this)

### Developer secret hygiene

- **`.env` files** — never committed to version control; use `.gitignore`
- **Environment variables** — inject secrets at runtime, not in source code
- **Short-lived tokens** — prefer tokens with expiry over long-lived API keys
- **git-secrets or pre-commit hooks** — automated protection against accidental commits

---

## Lab environment hygiene

### Isolation

| Practice | Why |
|----------|-----|
| Run labs in WSL/VM, not bare-metal daily driver | Malware from a CTF challenge stays contained |
| Use separate browser profile for labs | Cookies and extensions from personal browsing don't interfere |
| Snapshot VMs before risky operations | Easy rollback if something breaks |
| Use NAT networking for VMs by default | VM can reach the internet but isn't directly reachable from LAN |

### Verifying course materials

- Confirm CTF links come from the [official course WhatsApp group](https://chat.whatsapp.com/BJN7duZuObq1gbGPrped0y) or this repository
- Don't submit flags to unknown "checkers" or paste challenge URLs into untrusted sites
- If a "classmate" DMs you a tool link, verify through official channels first

### Network safety during labs

- When connected to a TryHackMe/HTB VPN, you're on a shared network with other players
- Don't leave sensitive services (SSH with weak passwords) running on your machine while on these VPNs
- Disconnect VPNs when not actively using them

---

## Connecting this to the rest of the course

| Week | How digital safety applies |
|------|---------------------------|
| 1 | Set up safe lab environment; don't leak credentials while learning git |
| 2 | OSINT works both ways — protect your own digital footprint while researching others |
| 3 | Web labs involve real HTTP traffic — don't accidentally send credentials to the wrong server |
| 4 | Cryptography tools often need you to handle keys — keep them out of git |
| 5 | Post-exploitation content teaches attackers' methods — understand them to defend, not to misuse |

---

## Summary checklist

Before proceeding to the next module, ensure you have:

- [ ] Run your email through [HIBP](https://haveibeenpwned.com/) and addressed any findings
- [ ] Installed a password manager (or confirmed yours is active)
- [ ] Enabled MFA on GitHub and Google
- [ ] Created a separate browser profile or VM for lab work
- [ ] Taken the [Google Phishing Quiz](https://phishingquiz.withgoogle.com/)
- [ ] Added `.env` to your global `.gitignore`

---

## Next

[ctf-fundamentals.md](ctf-fundamentals.md) — Understanding CTF competitions, challenge categories, and the mindset for solving them.
