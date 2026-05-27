# Cloud metadata awareness

Modern web apps don't run on a server in a closet. They run on EC2, App Engine, Azure VMs, or one of the dozen serverless flavours, and every one of those platforms exposes an **internal metadata service** to the workloads it hosts. That metadata service is invisible from the outside — but very visible from inside, and that asymmetry is at the heart of a class of breaches with stomach-turning consequences (the Capital One breach in 2019 exposed 106 million records via exactly this path).

This module is mostly **conceptual and defensive**. We do not exfiltrate credentials from real cloud accounts. We learn what the attack class looks like, how it's chained from SSRF, what the warning signs are, and how a defender shuts it down. If you want hands-on practice, the safe lab is your own AWS free-tier account or LocalStack — not a target you found on Shodan.

> **Authorized targets only.** Reaching another organisation's metadata service via SSRF is unauthorized access to a cloud account — both the SSRF target and the cloud account belong to victims. Liability under IT Act 2000 §43 and §66 is total: courts have repeatedly treated SSRF-to-cloud-cred as no different from typing a stolen password. Practice exclusively on your own free-tier cloud account, LocalStack, or TryHackMe rooms that explicitly simulate the metadata service.

---

## What the metadata service is

Every major cloud provider exposes a special **link-local IP** — `169.254.169.254` — to every VM and serverless function. Hitting that IP over HTTP returns information about the workload itself: instance ID, region, network configuration, user-data script, and — crucially — **short-lived credentials** for the IAM role attached to the instance.

```
┌──────────────────────────────────────────────────────────┐
│                   Cloud VM / function                    │
│                                                          │
│   ┌─────────────┐         169.254.169.254                │
│   │             │  ───────HTTP GET────────►              │
│   │   app.py    │                                        │
│   │             │  ◄──── instance ID,                    │
│   │             │       region,                          │
│   │             │       IAM creds (AccessKey, Secret,    │
│   │             │       SessionToken)                    │
│   └─────────────┘                                        │
│                                                          │
│   (no auth, no audit — by design, for the workload)      │
└──────────────────────────────────────────────────────────┘
```

The metadata service has two design goals:

1. **Bootstrap data.** The instance needs to know its hostname, region, and user-data script when it boots, before any other source of truth is available.
2. **Credential delivery.** Instead of stashing long-lived API keys in env vars or on disk, the cloud rotates short-lived credentials and lets the instance fetch them on demand.

Both goals require the service to be reachable **without authentication** from the workload itself. That's the design tension: from *inside* the VM, no auth is needed. If an attacker can make the VM ask the metadata service on their behalf, they inherit that "inside" position.

The link-local address (`169.254.0.0/16`) is special — it's never routed across networks and has no DNS by default, which means the metadata service is literally unreachable from outside the VM. The attacker has to make the VM do the asking.

---

## Per-cloud cheat sheet

| Cloud | Metadata endpoint | Notes |
|-------|--------------------|-------|
| **AWS EC2** | `http://169.254.169.254/latest/meta-data/` | IMDSv1 (no auth) and IMDSv2 (token-based) |
| **AWS Lambda / ECS** | `http://169.254.170.2/v2/credentials/$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` | Distinct endpoint from EC2 |
| **GCP Compute** | `http://metadata.google.internal/computeMetadata/v1/` | Requires `Metadata-Flavor: Google` header |
| **Azure VM** | `http://169.254.169.254/metadata/instance?api-version=2021-02-01` | Requires `Metadata: true` header |
| **Azure Managed Identity** | `http://169.254.169.254/metadata/identity/oauth2/token?...` | Returns OAuth2 access token |
| **DigitalOcean** | `http://169.254.169.254/metadata/v1/` | No auth |
| **Alibaba Cloud** | `http://100.100.100.200/latest/meta-data/` | Different IP, otherwise similar to AWS |
| **Oracle Cloud** | `http://169.254.169.254/opc/v2/instance/` | Requires `Authorization: Bearer Oracle` header |

The header requirement on GCP, Azure, and OCI is a small mitigation against the simplest SSRF cases — but it's trivial to bypass when the SSRF lets you set headers (most do).

---

## The credential payload

What does the loot actually look like? On EC2 (IMDSv1, the legacy, no-auth variant):

```http
GET /latest/meta-data/iam/security-credentials/ HTTP/1.1
Host: 169.254.169.254
```

Response (a single line per role):

```
prod-app-role
```

Then ask for the credentials of that role:

```http
GET /latest/meta-data/iam/security-credentials/prod-app-role HTTP/1.1
```

Response:

```json
{
  "Code": "Success",
  "LastUpdated": "2026-05-27T11:42:13Z",
  "Type": "AWS-HMAC",
  "AccessKeyId": "ASIAEXAMPLEKEYID12345",
  "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "Token": "FwoGZXIvYXdzEEEa...long...base64...session token",
  "Expiration": "2026-05-27T17:42:13Z"
}
```

Three fields are all an attacker needs:

| Field | What it does |
|-------|--------------|
| `AccessKeyId` | Identifies which key is making the request |
| `SecretAccessKey` | Signs requests cryptographically |
| `Token` | Session token — required for temporary credentials; without it the other two don't work |

With these, the attacker can run any `aws` CLI command the IAM role is permitted to make. If the role can read S3 buckets, they read them. If the role can launch EC2 instances, they launch them. If the role is `AdministratorAccess` (it shouldn't be, but you'd be shocked), the cloud account is theirs.

Credentials expire (the `Expiration` field) — typically 6 hours on EC2. The window is short but more than enough to do enormous damage.

---

## The chain — SSRF as the doorway

A metadata theft virtually always begins with a **Server-Side Request Forgery** (SSRF). An app that fetches a URL on the user's behalf — image proxies, webhook validators, "share this link" previews, PDF generators, anything that calls `requests.get(user_input)` server-side — is the typical entry point.

```
┌────────────┐                        ┌──────────────────┐
│ Attacker   │  POST /preview         │ App server (EC2) │
│ (anywhere) │ ─────────────────────► │                  │
│            │   url=http://          │  fetch(url)      │
│            │   169.254.169.254/...  │  ↓               │
│            │                        │  169.254...      │
│            │ ◄──── response ────── │  ↓ creds         │
│            │      (cached preview)  │  return creds    │
└────────────┘                        └──────────────────┘
       │                                       
       │  AccessKey + Secret + Token            
       ▼                                       
┌────────────┐
│ aws s3 ls  │
│ s3://prod/ │
└────────────┘
```

The defining feature: the *server* (which can reach `169.254.169.254`) makes the request on the *attacker's* behalf (who cannot reach it directly). The attacker reads the response in whatever channel the app exposes — usually rendered as a "preview" of the URL.

Week 3's SSRF section covered the input side. This module is about why one specific destination — `169.254.169.254` — is the highest-value target for any SSRF in the cloud.

### Real-world variants — bypassing simple SSRF filters

Naive filters block the literal string `169.254.169.254`. They fall over to:

| Bypass | Why it works |
|--------|--------------|
| `http://169.254.169.254.nip.io/` | Public DNS that resolves to the literal IP |
| `http://[::ffff:169.254.169.254]/` | IPv6-mapped form |
| `http://2852039166/` | Decimal encoding of the IP |
| `http://0xa9.0xfe.0xa9.0xfe/` | Hex per-octet |
| `http://0251.0376.0251.0376/` | Octal per-octet |
| `http://metadata.google.internal/` | Resolves to `169.254.169.254` on GCP via internal DNS |
| `http://attacker.com/redirect?to=http://169...` | DNS rebinding or HTTP redirect chains |

Any allow-list-on-string approach is broken. The fix is **resolve the hostname to an IP and check the IP**, not the input string.

---

## IMDSv1 vs IMDSv2 — the AWS fix

The original (IMDSv1) endpoint had no authentication at all — any process inside the VM could `curl` it. AWS introduced **IMDSv2** in 2019 (post-Capital One) as an opt-in session-token model that breaks the SSRF chain.

**IMDSv2 flow:**

```http
PUT /latest/api/token HTTP/1.1
Host: 169.254.169.254
X-aws-ec2-metadata-token-ttl-seconds: 21600
```

Response: a session token (`AQAA...`).

```http
GET /latest/meta-data/iam/security-credentials/role/ HTTP/1.1
Host: 169.254.169.254
X-aws-ec2-metadata-token: AQAA...
```

Why this defeats most SSRF:

1. **PUT method.** Most SSRF primitives only let an attacker make GETs.
2. **Custom header.** Most SSRF primitives can't set arbitrary headers in the outgoing request.
3. **TTL hop limit of 1.** The PUT response uses an IP TTL of 1, meaning the token won't leave the EC2 instance — so even if the SSRF is *to* the instance from elsewhere, the token can't be retrieved.

| | IMDSv1 | IMDSv2 |
|-|--------|--------|
| Authentication | None | Session token |
| Method | GET works | `PUT` to obtain token, then GET with token |
| SSRF exploitability | Almost any SSRF can read metadata | Requires SSRF that can issue arbitrary PUTs *and* custom headers — rare |
| Adoption | Default until ~2023 | Default on new EC2; can be enforced cluster-wide |

AWS now offers a `MetadataOptions` flag (`HttpTokens: required`) to enforce IMDSv2 only — that flag is the single most impactful one-line defence you can apply. GCP, Azure, and OCI took the header-on-GET path instead, which is somewhat weaker but also blocks the most naive SSRF.

---

## Case study — Capital One, 2019

A short, accurate retelling because this case basically defines the threat model:

1. Capital One's open-banking infrastructure ran on AWS. An EC2 instance hosted a WAF (ironically, ModSecurity-as-a-service).
2. The WAF had an SSRF vulnerability that let an authenticated user make it fetch arbitrary URLs.
3. An attacker (a former AWS engineer) used the SSRF to hit `169.254.169.254/latest/meta-data/iam/security-credentials/`.
4. The WAF's IAM role had `s3:ListBucket` and `s3:GetObject` on the production data buckets.
5. The attacker used the temporary creds with the `aws` CLI to download **106 million customer records**, including ~140k SSNs, 1M Canadian Social Insurance Numbers, ~80k bank account numbers.
6. The attacker boasted on a public Slack and was identified within a month.

The aftermath: USD 80M fine, USD 190M class-action settlement, the largest cloud-breach disclosure to that date. The technical lessons baked into every modern guide come straight from this incident:

- **IMDSv1 is over-privileged by design.** AWS shipped IMDSv2 directly in response.
- **IAM least privilege matters.** The WAF didn't need `s3:GetObject *`. Scope IAM to specific buckets and operations.
- **WAF-level SSRF protection.** Filter outbound destinations from app servers, not just inbound traffic.
- **VPC-level egress filtering.** Block the metadata IP at the security group / NACL where appropriate.
- **Detection.** Unusual `iam/security-credentials/` access patterns are a high-fidelity signal.

The Capital One docket is public and very readable. It's the closest thing to a cloud-security exam case study you can ask for.

---

## Other lookalike risks worth knowing

| Risk | Why it's related |
|------|------------------|
| **Container metadata** | Container orchestrators (ECS, Fargate, Kubernetes IRSA) expose a per-container credentials endpoint at a *different* IP/path. Same idea, slightly different URL. |
| **Kubelet `/spec/`** | A misconfigured kubelet exposes pod specs (including env vars with secrets) on port 10255/10250. |
| **Vault sidecar** | HashiCorp Vault agents serve secrets on a unix socket or localhost — SSRF to localhost can sometimes hit them. |
| **Docker socket via SSRF** | If `/var/run/docker.sock` is HTTP-proxied somewhere, SSRF can talk to it and own the host. |

The shared theme: any "trusted internal service that proves identity by being inside" is a high-value SSRF target. The fix is the same — assume identity is *not* proved by network position; require explicit auth.

---

## Defending against this class

Layered, because no single control is sufficient:

| Layer | Control |
|-------|---------|
| **Cloud platform** | Enforce IMDSv2 (`HttpTokens: required`) on every EC2 instance. GCP/Azure: require the metadata header. |
| **IAM** | Least privilege. Per-instance roles, not account-wide. Time-bounded sessions where possible. Never `*` resources or `*` actions. |
| **Application** | Don't fetch user URLs server-side. If you must, use an allow-list of explicit hostnames; resolve the hostname yourself; check the IP against `RFC 1918`, link-local, loopback, multicast and refuse. |
| **Network** | VPC egress rules that block `169.254.169.254` from application subnets that don't need it. Some orgs use a [HTTP proxy](https://github.com/aws-samples/ec2-imds-packet-analyzer) that strips metadata requests from app traffic. |
| **Detection** | Log every successful and failed metadata access. CloudTrail surfaces credential-use anomalies (e.g. a key minted on instance A used from instance B's IP). |
| **Code** | Static analysis rules for `requests.get(user_input)`, `urllib.request.urlopen(user_input)`, and equivalents in other languages. |

A real-world hardened app:

```python
import ipaddress, socket
from urllib.parse import urlparse

BLOCKED = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

def safe_fetch(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("scheme not allowed")
    ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
    if any(ip in net for net in BLOCKED):
        raise ValueError(f"blocked destination: {ip}")
    return requests.get(url, timeout=5, allow_redirects=False)
```

Two subtleties: **disable redirects** (otherwise a public URL can 302 you to `169.254.169.254`), and **resolve the hostname yourself** (otherwise DNS rebinding flips the IP between your check and the actual `requests.get`).

---

## Lab-only experimentation

| Lab | Why it's safe |
|-----|---------------|
| **LocalStack** ([github.com/localstack/localstack](https://github.com/localstack/localstack)) | Local-only AWS emulator; has a fake metadata service you can poke at. |
| **Your own AWS free-tier** | You own the account; you set IMDS to v1 deliberately; you own the SSRF demo app. |
| **TryHackMe — Cloud rooms** (e.g. "AWS Basics", "Attacking Kubernetes") | Authorised on their VPN. |
| **PortSwigger Web Academy — SSRF labs** | Includes a "cloud metadata" lab that simulates the response from a fake endpoint. |
| **`hackerone CloudGoat`** ([github.com/RhinoSecurityLabs/cloudgoat](https://github.com/RhinoSecurityLabs/cloudgoat)) | Terraform scenarios that intentionally misconfigure AWS for safe practice in your own account. |

For CSOT specifically: spin up a tiny LocalStack container, point `curl http://localhost:4566/latest/meta-data/` at it (LocalStack proxies metadata too), and confirm the response shape matches what's documented here. That's the entire safe practice loop you need.

---

## CTF tip — recognising the pattern

In CTFs, "cloud metadata" usually appears as an SSRF challenge with a flag stored at `http://169.254.169.254/<something>` or a simulated metadata path. The cue is almost always:

- An input that fetches a URL on the server-side.
- A `127.0.0.1` filter (and not much else).
- A note in the description hinting at "internal" or "metadata" services.

Bypass paths to try (lab targets only):

```
http://127.1/                 ← short-form loopback (sometimes filters miss this)
http://0.0.0.0/               ← also reaches localhost on most systems
http://169.254.169.254/       ← if the lab models AWS
http://localhost@127.0.0.1/   ← URL userinfo trick (legacy bypass)
http://2130706433/            ← decimal 127.0.0.1
```

If the lab models GCP, add the `Metadata-Flavor: Google` header (most SSRF challenges with header-injection let you do this).

---

## Defender's lens — what to log and alert on

| Signal | Alert when |
|--------|------------|
| Successful metadata access | If your app shouldn't be calling metadata, *any* call is suspect |
| Credential use from unusual source IP | CloudTrail event source IP differs from the instance's normal IP |
| Cross-region API calls | Instance in `us-east-1` suddenly calling `eu-west-3`? |
| Calls to S3 buckets outside the instance's usual list | Anomaly detection on `s3:GetObject` for new buckets |
| Failed metadata token PUTs from app server | An IMDSv2-aware attack attempt; suggests the SSRF is being probed |
| `iam:CreateAccessKey` from a session token credential | Attacker upgrading temporary creds to long-lived ones |

These are the signals SOC analysts triage every day in cloud-heavy environments. They're also exactly what you'd write in an [incident-response-lite.md](incident-response-lite.md) report if this incident landed on your desk.

---

## Further reading

- [Capital One indictment — public PDF](https://www.justice.gov/usao-wdwa/press-release/file/1188626/download) — names redacted; technical details intact.
- [AWS IMDS documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) — official IMDSv2 enforcement guide.
- [GCP metadata server docs](https://cloud.google.com/compute/docs/metadata/overview).
- [Azure Instance Metadata Service](https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-service).
- [HackTricks — SSRF to metadata](https://book.hacktricks.xyz/pentesting-web/ssrf-server-side-request-forgery/cloud-ssrf) — every endpoint and bypass collected.
- [CloudGoat scenarios](https://github.com/RhinoSecurityLabs/cloudgoat) — IaC-driven AWS misconfig labs.
- [SSRF Bible](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) — OWASP defensive cheat sheet.

---

## Next module

[detection-evasion-awareness.md](detection-evasion-awareness.md) — Every offensive technique in this week leaves traces. The next module looks at exactly what gets logged, why "I evaded AV" is usually false, and how this all connects to MITRE ATT&CK's Defense Evasion tactic.
