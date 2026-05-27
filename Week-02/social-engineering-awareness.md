# Social engineering awareness

Most successful breaches don't start with a clever exploit. They start with a person clicking a link, opening an attachment, holding a door open, or answering a phone call. **Social engineering** is the discipline of manipulating people — exploiting trust, urgency, authority, and curiosity — instead of (or before) exploiting machines.

This module is unusual in CSOT for being mostly **defensive**. You should be able to recognize social-engineering patterns, build resistance to them, and explain to non-technical people why "just don't click suspicious links" is bad advice. We don't run social-engineering attacks against real people in this course — only against the synthetic personas in the Week 2 lab.

---

## Why this matters

The boundary between OSINT (last module) and social engineering is **action**. OSINT is *collecting* public information. Social engineering is *using* that information to make someone act against their interest.

- An attacker spends an hour on LinkedIn learning the org chart.
- They find the CFO's name, the new hire's name, and the IT lead's writing style.
- They send the new hire an email "from" the CFO, cc-ing IT, asking for a payroll change.
- The new hire complies because every concrete detail checks out.

No vulnerabilities were scanned. No firewalls were touched. Money disappeared.

The Verizon DBIR (Data Breach Investigations Report) consistently finds that **the human element is involved in roughly 70–80% of breaches**. You can have the best WAF in the industry and still lose because someone clicked.

---

## The attack chain — OSINT → engineering → impact

A real social-engineering campaign almost always follows this shape:

```
1. RECON         Collect public info: employees, vendors, tools, writing style
                 ↓ (this is exactly the OSINT module)
2. PRETEXTING    Build a believable persona / scenario tailored to the target
                 ↓
3. DELIVERY      Send the email / make the call / show up at the door
                 ↓
4. EXPLOITATION  Target clicks, types creds, runs macro, opens door, transfers funds
                 ↓
5. IMPACT        Credential reuse, malware foothold, wire fraud, physical access
```

Each step makes the next easier. Defenders can disrupt at any step — but **the earlier you catch it, the less damage**. Recognizing the *recon* (unusual LinkedIn views, traffic spikes from a single ASN) and the *pretext* (sender domain looks off) is much cheaper than recovering stolen funds.

---

## The classic attack types

### Phishing

Bulk email pretending to be a trusted entity (bank, courier, IT, Microsoft, etc.) to harvest credentials or deliver malware.

| Sub-type | What it is |
|----------|------------|
| **Bulk phishing** | Mass-mailed, low effort, hopes a small percentage bite |
| **Spear phishing** | Personalized to a specific person — uses their name, role, recent activity |
| **Whaling** | Spear phishing aimed at executives or high-value targets |
| **BEC** (Business Email Compromise) | Spoofs or compromises an exec's account to request wire transfers, payroll changes, gift cards |
| **Clone phishing** | A real email is copied, the attachment replaced with a malicious one, and re-sent |

### Vishing (voice phishing)

A phone call. "Hi, this is Raj from IT, we're seeing strange activity on your account, can I have you read me the OTP your phone just got?" Works because real IT departments make outbound calls and most people don't have a way to verify.

Modern variant: AI-cloned voices of executives ordering urgent transfers.

### Smishing (SMS phishing)

The same idea over SMS or WhatsApp. Often impersonates couriers ("package held, click to reschedule"), banks ("KYC update required"), government ("refund pending").

### Pretexting

A fabricated scenario used to extract information. "I'm doing a compliance audit and need your employee ID and date of joining" — and now the caller has half of what they need to reset your password.

### Baiting

Leaving something tempting where the target will pick it up. The classic is the USB drive labeled "Salaries 2024" left in the parking lot. Plug it in → autorun malware → foothold. Digital equivalent: "free software downloads."

### Quid pro quo

Offering something in exchange for action. "I'll give you free tech support if you let me remote-connect to your laptop." Often combined with vishing.

### Tailgating / piggybacking

Physical. Following someone through a secured door without badging in. "Hey, my hands are full, can you hold the door?" Combined with a fake badge or contractor uniform, this works embarrassingly often.

### Watering hole

Compromise a website the target community is known to visit, then wait. Instead of attacking the company, you attack a forum or vendor blog its employees read.

---

## The psychological levers

Robert Cialdini's *Influence* (1984) catalogued six principles of persuasion. Every social-engineering attack abuses one or more of them. Recognizing the **lever** in real time is the single best defense.

| Principle | How attackers use it | Counter-instinct |
|-----------|----------------------|------------------|
| **Authority** | "I'm from IT / from the CEO / from the auditor" | Slow down. Verify through a separate channel. |
| **Urgency** | "Wire this in the next 30 minutes or we lose the deal" | Urgency is the red flag, not the legitimacy signal. |
| **Scarcity** | "Last chance to claim — link expires in 1 hour" | Genuine business rarely depends on you acting in minutes. |
| **Reciprocity** | "I helped you with X, can you just do this small thing?" | You owe nothing to strangers. |
| **Liking** | Build rapport, mention shared connections | Likable doesn't mean truthful. |
| **Social proof** | "Everyone in your team already did this" | Verify directly with one teammate. |

A useful heuristic: **the more emotional the message makes you feel, the slower you should respond**. Phishing thrives on people in a hurry.

---

## Anatomy of a phishing email

Real phishing emails have telltales if you slow down enough to look. Here's an annotated example:

```
From:    "IT Support" <it-support@example-corp.support>      ← look-alike domain
To:      newhire@example-corp.com
Subject: Urgent: Your account will be locked in 24 hours      ← urgency
Date:    Sun, 5:14 AM                                         ← odd timing

Hi,                                                            ← generic greeting

We have detected unusual activity on your account.            ← vague threat
To prevent it from being locked, please verify your
credentials immediately by clicking the link below:

    https://example-corp.support.verify-now.io/login          ← suspicious URL
                                                              ← hovering shows real
                                                                target

Failure to do so will result in suspension of all access.     ← scarcity + threat

— IT Support
```

### Red flags in order of reliability

1. **Sender domain mismatch.** `it-support@example-corp.support` is *not* `example-corp.com`. Look at the full address, not just the display name.
2. **Look-alike domains.** `examp1e-corp.com` (digit 1 vs letter l), `example-corρ.com` (Cyrillic ρ), `xn--…` (punycode).
3. **Mismatched link target.** Hover the link before clicking — the real URL is almost always different from the visible text.
4. **Urgency or fear.** "24 hours," "account suspended," "legal action."
5. **Generic greeting** when the sender claims to know you.
6. **Unexpected attachments**, especially `.zip`, `.iso`, `.lnk`, `.docm`, `.xlsm`, or anything that asks you to enable macros.
7. **Odd timing** (5 AM Sunday) or unusual location of links (Google Drive sharing for an "internal" doc).
8. **Reply-to differs from From.** Often the displayed `From:` is correct but `Reply-To:` redirects to the attacker.

### Authentication headers (the technical side)

Modern mail servers attach **SPF**, **DKIM**, and **DMARC** results. You can see them in the raw headers (Gmail: "Show original"; Outlook: "View message source").

| Header | Meaning |
|--------|---------|
| `Received-SPF: pass` | The sending server was authorized to send for the From-domain |
| `DKIM-Signature: ... ; dkim=pass` | The message was signed by the From-domain's key and not modified |
| `Authentication-Results: dmarc=pass` | Both SPF and DKIM align with the From-domain |
| `dmarc=fail` | Strong signal of spoofing |

Most well-run enterprises now require all three to pass. Phishing emails frequently come from domains where DMARC is "pass" because the attacker registered a **look-alike domain** and configured DKIM properly for it. That's why domain inspection (#1 and #2 above) still matters even when headers say "pass."

---

## Defensive habits — for you, personally

You will be targeted. Treat it as a baseline.

### Email

- Hover before you click. Browsers and mail clients show the real URL.
- For anything financial or credential-related, navigate manually. Don't click email links to log into bank accounts.
- Treat attachments from unexpected senders as malicious until proven otherwise. Re-deliver to a sandbox or [virustotal.com](https://www.virustotal.com/) (don't upload sensitive files).
- Set up **2FA everywhere**, ideally with a security key (FIDO2/WebAuthn) instead of SMS. Phishing kits replay SMS OTPs in real time; FIDO keys are bound to the legitimate domain and refuse to authenticate on look-alikes.

### Phone

- Real IT, real banks, real tax officers do **not** ask for OTPs over the phone. Ever.
- If a "company representative" calls, hang up and call back on the official number from the company's website.
- Treat caller ID as untrusted — VoIP makes spoofing trivial.

### In person

- Don't hold secured doors open for strangers; politely ask them to badge in themselves.
- Be skeptical of unsolicited "vendor" visits.
- Don't plug in found USB drives. Hand them to security.

### Account hygiene

- Use a **password manager** (Bitwarden, 1Password, KeePassXC). Unique passwords per site neutralize credential-stuffing entirely.
- Check [haveibeenpwned.com](https://haveibeenpwned.com/) for your email — change the password anywhere you reused the breached one.
- Enable login alerts on critical accounts (email, bank, government portals).

### When you do click

It happens. If you suspect you clicked a phishing link or typed credentials into a fake site:

1. **Change the password** of the impersonated account immediately, from a clean device.
2. **Revoke active sessions** in the account's security settings.
3. **Check 2FA settings** — confirm the attacker didn't add their own backup factor.
4. **Report to your security team / IT** — speed beats embarrassment. They've seen worse this week.
5. **Look for follow-on activity** — strange forwarding rules, new OAuth grants, unfamiliar devices.

---

## Defensive habits — for organizations

Worth knowing even if you're not yet in a security role, because it'll come up in interviews.

| Control | What it does |
|---------|--------------|
| **SPF / DKIM / DMARC** with `p=reject` | Stops most domain spoofing |
| **Phishing-resistant MFA** (FIDO2) | Defeats credential phishing for protected accounts |
| **Email gateway with sandbox detonation** | Catches malicious attachments before delivery |
| **Link rewriting** (e.g., Mimecast, Proofpoint) | Inspects URLs at click time, not just delivery time |
| **Banner on external mail** | "This message originated outside the organization" — high-ROI UI cue |
| **Browser isolation** | Suspicious links open in a remote sandbox |
| **Security awareness training + simulated phishing** | Measures and lowers click rate over time |
| **Out-of-band approval** for wire transfers | Defeats BEC scams |
| **Just-in-time admin access** + privileged session monitoring | Limits blast radius if a regular account is compromised |

The goal isn't "zero clicks" (impossible). It's **degrading the kill chain** — even a click should not equal a breach.

---

## CSOT lab rules

- All targets in [../../CTFs/week-02/osint-dossier/](../../CTFs/week-02/osint-dossier/) and any future social-engineering challenge are **synthetic**. The "CEO," "pet name," and "project codename" are made up.
- Do not run sherlock/maigret/hunter.io against real classmates, faculty, or course staff.
- Do not send phishing simulations to real people without explicit prior authorization from the recipient and from the relevant administrator.
- Do not impersonate real organizations (the institute, banks, vendors) even in jest — this can quickly land in IT Act territory.

If something feels uncomfortable to do, that's a useful signal. Stop and check before continuing.

---

## Legal awareness

Social engineering against real people without authorization is illegal in essentially every jurisdiction. A few specific lines:

| Jurisdiction | Law / clause | What it covers |
|--------------|-------------|----------------|
| India | IT Act 2000 §66C | Identity theft (using someone else's password/credentials) |
| India | IT Act 2000 §66D | "Cheating by personation by using computer resource" — covers phishing |
| India | IPC §419, §420 | Cheating by impersonation, cheating with fraudulent intent |
| US | 18 USC §1343 | Wire fraud |
| US | CFAA | Unauthorized access |
| EU | GDPR | Misuse of personal data |

Authorized engagements (red-team retainers, official phishing simulations with HR/legal sign-off) operate under explicit contracts. Outside those, it's crime.

---

## Practice (defensive)

| Resource | What you'll do |
|----------|---------------|
| [Hacksplaining](https://www.hacksplaining.com/) | Interactive walkthroughs of phishing, password reuse, etc. |
| [Google's phishing quiz](https://phishingquiz.withgoogle.com/) | Identify real vs phish in eight emails |
| [OpenPhish](https://openphish.com/) | Live feed of currently-active phishing URLs (look, don't click) |
| TryHackMe — *Phishing Emails 1–5* | Step-by-step header analysis |
| TryHackMe — *Greenholt Phish* | Realistic phishing investigation room |
| TryHackMe — *Social Engineering* | Concept overview |

---

## Connecting back to CSOT

[../../CTFs/week-02/osint-dossier/](../../CTFs/week-02/osint-dossier/) is your hands-on tie-in: a fictional company's `about.md` exposes a pet name and a project codename. Combining them yields the flag. That's the OSINT half — the social-engineering half would be using the same two facts as password-reset answers in a security-question attack against a real account. We don't do that part. But you should be able to articulate, after this module, **why** combining those two innocuous facts is dangerous in the real world.

---

## Further reading

- *The Art of Deception* — Kevin Mitnick. Practitioner classic; mostly war stories.
- *Influence: The Psychology of Persuasion* — Robert Cialdini. The principles attackers exploit.
- [SANS Security Awareness — Phishing](https://www.sans.org/security-awareness-training/resources/phishing-resources) — checklists and ready-made training material.
- [Verizon DBIR](https://www.verizon.com/business/resources/reports/dbir/) — annual breach statistics; always cites human factors.
- [APWG — Anti-Phishing Working Group reports](https://apwg.org/trendsreports/) — quarterly phishing trends.

---

## Next module

[dns-enumeration.md](dns-enumeration.md) — back to technical recon. (If you've already read the modules in README order, the next is [recon-automation.md](recon-automation.md).)
