# API security

Most modern apps are a thin frontend on top of a fat API. The HTML shell loads in your browser and then makes 30 JSON calls to `/api/...` to do real work. From an attacker's point of view, the API *is* the application — the UI is a polite suggestion, the API is what enforces (or fails to enforce) every rule.

That mental flip matters. A web page only shows you the buttons the developer remembered to render. The API behind it usually exposes more endpoints than the UI uses, accepts more fields than the form sends, returns more data than the page displays. Every "hidden" admin feature, every test endpoint left in by mistake, every legacy method that no longer has a frontend — they're all sitting there if you read the JS bundle or fuzz the routes.

This module covers the OWASP API Security Top 10 (2023 edition), how API recon differs from web-app recon, and how to test REST APIs (with a sidebar on GraphQL and gRPC). JWTs get their own module afterwards.

---

## REST vs GraphQL vs gRPC

You'll meet three flavors of API in the wild. They share security principles but differ in surface.

| Style | Transport | Schema | Quirks |
|-------|-----------|--------|--------|
| **REST / JSON** | HTTP/1.1, HTTP/2 | OpenAPI / Swagger (optional) | Resources at URLs (`/api/users/5`), verbs map to actions |
| **GraphQL** | HTTP POST (usually `/graphql`) | Introspectable schema | One endpoint, many queries; nested fetches; per-field auth pitfalls |
| **gRPC** | HTTP/2 + protobuf | `.proto` files | Binary frames; tooling lighter outside Google; needs `grpcurl` / Burp extension |

REST dominates by volume. GraphQL is fashionable in startups. gRPC is common inside microservice meshes and rare on a public edge. We focus on REST.

A REST request looks like:

```http
GET /api/v1/users/42 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOi...
Accept: application/json
```

A GraphQL request looks like:

```http
POST /graphql HTTP/1.1
Content-Type: application/json

{"query":"query { user(id: 42) { id name email } }"}
```

A gRPC call looks like an HTTP/2 POST with a binary body — you need `grpcurl` to read it.

The OWASP API Top 10 applies to all three.

---

## OWASP API Security Top 10 (2023)

The dedicated API list, distinct from the general OWASP Top 10. It exists because some bug classes (BOLA, mass assignment, business-flow abuse) are far more common on APIs than on classic web apps.

| ID | Category | What it covers |
|----|----------|----------------|
| **API1** | Broken Object Level Authorization (BOLA) | Server doesn't verify the caller owns the requested object |
| **API2** | Broken Authentication | Weak login/session/token mechanics |
| **API3** | Broken Object Property Level Authorization | Server returns or accepts fields the caller shouldn't see/set |
| **API4** | Unrestricted Resource Consumption | No rate-limit / quotas; cost-amplification, DoS |
| **API5** | Broken Function Level Authorization | Endpoint accessible by role that shouldn't reach it |
| **API6** | Unrestricted Access to Sensitive Business Flows | Workflow abuse (1M signups, scraping, ticket scalping) |
| **API7** | Server-Side Request Forgery (SSRF) | Server-side fetch with attacker-controlled URL |
| **API8** | Security Misconfiguration | Same as Top 10 A05 — verbose errors, default keys, CORS gaps |
| **API9** | Improper Inventory Management | Stale `/v1/`, dev/test endpoints exposed alongside `/v3/` |
| **API10** | Unsafe Consumption of APIs | Trusting third-party APIs you call (XSS via their data, etc.) |

We'll walk each, with a curl example you can actually run against the CSOT lab where it fits, or against PortSwigger Academy labs otherwise.

---

## API1 — Broken Object Level Authorization (BOLA)

The defining API bug class. Same shape as IDOR in classic web apps, but APIs return JSON objects and tend to be more granular. Every request that takes an object ID is a potential BOLA.

### Vulnerable example

```python
@app.route("/api/v1/invoices/<int:invoice_id>")
def get_invoice(invoice_id):
    inv = Invoice.query.get(invoice_id)
    return jsonify(inv.to_dict())
```

No check that `current_user` owns `inv`. Any authenticated user can read any invoice by ID.

```bash
curl -H "Authorization: Bearer $MY_TOKEN" https://api.example.com/api/v1/invoices/1234
# {"id":1234,"customer":"someone else","total":58000}
```

### Detection workflow

1. Log in as user A. Inventory every endpoint that takes an ID (numeric, UUID, slug).
2. Create matching resources as user B in a second account.
3. From A's session, request B's resources by ID. Read? Update? Delete?

UUIDs feel safer because they're hard to guess, but they're often **leaked** in list endpoints, error messages, or returned in unrelated responses. Always test, never assume.

### Fix

Enforce ownership in the handler:

```python
@app.route("/api/v1/invoices/<int:invoice_id>")
@login_required
def get_invoice(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    if inv.owner_id != current_user.id and not current_user.is_admin:
        abort(403)
    return jsonify(inv.to_dict())
```

Better, use a framework that scopes queries to the current user (`Invoice.query.owned_by(current_user).get(...)`).

---

## API2 — Broken Authentication

Everything that goes wrong with login, sessions, tokens.

| Bug | Test |
|-----|------|
| No rate limit on login | 100 wrong creds in a row, see if anything blocks |
| Weak password policy | Submit `"a"` as a password |
| JWT secret hard-coded / weak | See [jwt-and-apis.md](jwt-and-apis.md) — try cracking `HS256` |
| Tokens never expire | Capture a token, wait a week, reuse |
| Refresh token also stateless | Revoke and reuse — does it really die? |
| Login returns user existence | "Wrong password" vs "No such user" |

A common API-specific variant: a separate `/api/v1/auth/login` doesn't share rate limits with the HTML login form, so the attacker hits the API path.

### Fix

- Same hardening as classic auth.
- Rotate JWT signing keys; short access tokens (5–15 min); long refresh tokens stored server-side and revocable.
- Generic error messages.
- Per-IP and per-account rate limits at the edge.

---

## API3 — Broken Object Property Level Authorization

Two related bugs in one category.

### Excessive data exposure

The API returns more fields than the UI displays. The frontend filters out the sensitive ones; the API doesn't.

```http
GET /api/v1/users/42

{
  "id": 42,
  "name": "Alice",
  "email": "alice@example.com",
  "phone": "+1-555-1234",
  "passwordHash": "$2b$12$...",
  "internalNotes": "VIP customer, escalate any issues",
  "isAdmin": false
}
```

You sniff the JSON, the page shows only `name`, you have the password hash anyway. The fix: **serialize explicitly**, never `model.to_dict()` for a public-facing response.

### Mass assignment

The API trusts every key the client sends and writes it into the database model. The CSOT lab's `/api/notes` demonstrates the pattern: an "admin" key in the JSON body unlocks a flag the legitimate UI never sends.

```bash
curl -X POST http://127.0.0.1:5000/api/notes \
  -H 'Content-Type: application/json' \
  -d '{"title":"normal","role":"admin"}'
# {"ok":true,"flag":"csot26{api_json_injection}"}
```

The challenge is [../../CTFs/week-03/api-notes/](../../CTFs/week-03/api-notes/). Real-world version: a profile-update endpoint that accepts any column, and an attacker sets `{"role":"admin","credits":99999}`.

### Fix

Whitelist the fields the endpoint accepts (Marshmallow schemas, Pydantic models, framework "strong parameters"):

```python
class CreateNoteSchema(Schema):
    title = fields.Str(required=True, validate=Length(1, 200))
    body  = fields.Str()
    tags  = fields.List(fields.Str())
    # role intentionally absent
```

And for responses, define what's serialized — never `.to_dict()` a model into a response body.

---

## API4 — Unrestricted Resource Consumption

APIs are cheap to call and expensive to serve. Without quotas, an attacker turns "1¢ cost per call" into a real bill.

| Variant | Example |
|---------|---------|
| No rate limit | 10 million logins/hr; brute force |
| No per-call cost limit | `?limit=1000000` triggers a massive DB scan |
| No body-size limit | `POST` 2GB JSON; OOM |
| No file-upload limit | Disk fills |
| Expensive endpoint | `GET /reports?range=10y` blocks workers |
| Pagination abuse | Page through 50M rows |
| GraphQL nested query | `user { friends { friends { friends { ... } } } }` n+1 explosion |

### Test

```bash
# Bulk request bomb
for i in {1..1000}; do
  curl -s -o /dev/null http://127.0.0.1:5000/api/notes &
done
wait
```

If nothing slows down, there's no rate-limit between you and the database.

### Fix

- Per-route rate limits (cheaper routes 1000/min, expensive routes 10/min).
- Hard caps on `limit`, `page_size`, request body size.
- Query-cost analysis for GraphQL (limit depth, max complexity).
- A reverse-proxy quota layer (Envoy, NGINX, Cloudflare) that runs before the backend.

---

## API5 — Broken Function Level Authorization

Same family as broken access control, but per-*function* rather than per-*object*.

```http
DELETE /api/v1/users/42        # admin-only endpoint
```

The bug is that the endpoint *checks the user is logged in* but not *whether the role permits the action*. Regular users can call admin endpoints.

### Detection

1. Log in as a regular user.
2. From the admin user's browser, capture every admin request.
3. Replay each as the regular user (same URL, swap the cookie/token).
4. If you get 200/204 instead of 403, you found a function-level bug.

The Burp extension **Autorize** automates this: log in as user A, browse, then it replays every request with user B's cookies and flags responses where it shouldn't.

### Fix

Centralize role checks. Avoid per-handler boilerplate; use decorators or middleware that fail closed.

```python
@require_role("admin")
def delete_user(uid): ...
```

---

## API6 — Unrestricted Access to Sensitive Business Flows

The 2023 list's most "design level" entry. A flow that works fine for a real human is catastrophic if executed at machine speed.

Examples:

- Concert ticket purchase that lets one IP buy 1,000 tickets in 5 seconds (resale market).
- Free-trial sign-up that doesn't deduplicate by email/phone/device — attacker rolls credits forever.
- Loyalty point transfer with no anti-fraud — point laundering.
- API for sending notifications with no per-recipient cap — spam cannon.

You won't find these with a wordlist. You find them by **threat-modeling the feature**: "what would I do if I had a script and 24 hours?"

### Fix

- Bot/automation detection (TLS fingerprints, behavioral signals).
- Stricter per-account/per-IP/per-device caps on the sensitive flow.
- CAPTCHA, MFA, or proof-of-work gates inserted at known abuse points.
- Logging and alerting on flow-level anomalies.

---

## API7 — Server-Side Request Forgery (SSRF)

Identical to A10 in the general OWASP Top 10. APIs that accept URLs (webhook setup, profile image upload "from URL", PDF generation from URL, etc.) are SSRF hot zones. See the OWASP Top 10 module's A10 section for payloads and defenses.

```bash
curl -X POST https://api.example.com/v1/webhooks \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://169.254.169.254/latest/meta-data/iam/security-credentials/"}'
```

If the server fetches that URL and stores the body, you can read AWS IAM credentials.

---

## API8 — Security Misconfiguration

Same family as the main Top 10. API-specific flavors:

| Misconfig | Result |
|-----------|--------|
| Debug mode on production API | Stack traces in JSON responses |
| Verbose error messages | DB type, ORM, internal hostnames leaked |
| Permissive CORS | `Access-Control-Allow-Origin: *` with credentials |
| TLS not enforced | API also served over HTTP |
| Default API keys | `swagger`/`swagger` admin |
| Old API versions still online | `/api/v1/` insecure, `/api/v3/` patched, both reachable |
| Open `/docs` or `/swagger.json` exposing private endpoints | Free recon |

The CSOT lab's `/login` leaks SQL errors verbatim — same bug class, different layer.

---

## API9 — Improper Inventory Management

You can't secure what you don't know exists. Stale API versions, undocumented endpoints, and forgotten dev/staging hosts are easy attack surface.

| Bug | Example |
|-----|---------|
| `api-v1.example.com` still online after `v3` ships | All known v1 bugs still exploitable |
| `staging-api.example.com` reachable from the internet | Often weaker auth, real data |
| `/internal/` mounted on the same host with no auth | Used "for testing" |
| OpenAPI spec at `/swagger.json` lists every internal endpoint | Free map |

### Recon

- Look for older API versions by path (`/api/v1/`, `/api/v2/`, `/api/v3/`) and by host (`api-old.`, `legacy-api.`, `api-staging.`).
- Check WaybackMachine / archive.org for endpoints that used to exist.
- Pull and read every JS bundle.
- DNS for `*.api.target.tld` and `*-api.target.tld`.

### Fix

Maintain an inventory. Decommission what isn't shipped. Apply security gates to staging as you do to production.

---

## API10 — Unsafe Consumption of APIs

The risk that your **server** trusts a third-party API too much.

```python
data = requests.get("https://partner.example.com/users/42").json()
return render_template("profile.html", **data)            # XSS via partner.example.com
```

Or:

```python
status = requests.get(f"https://partner/check/{uid}").text
if status == "ok": grant_premium(uid)                      # spoofable if partner is MITMed
```

Treat data coming back from external APIs the same way you treat user input: validate types, escape on output, verify integrity. Pin TLS where it matters. Don't follow arbitrary redirects from third-party APIs into your own internal network.

---

## API recon — how it differs from web app recon

You won't find the API by clicking links. You find it by reading what the frontend already does.

### Pull the JS bundle

```bash
# Grab every JS file referenced from the homepage
curl -s https://example.com | grep -oE 'src="[^"]+\.js"' \
  | cut -d'"' -f2 | while read js; do
    curl -s "$(echo $js | sed 's|^|https://example.com/|')" \
      | grep -oE '"/api/[^"]+"' | sort -u
  done
```

You'll see paths like `/api/v1/me`, `/api/v1/orders`, `/api/v1/admin/users`. Some of those won't have UI buttons.

### Look for OpenAPI / Swagger / Postman

Common paths to probe:

```
/openapi.json
/openapi.yaml
/swagger.json
/swagger.yaml
/swagger-ui.html
/swagger-ui/
/api-docs
/api/v1/swagger
/graphql
/graphiql
/playground
/docs
/redoc
```

A single `swagger.json` hit gives you the full API map. Tools like [`kiterunner`](https://github.com/assetnote/kiterunner) brute-force Swagger paths efficiently:

```bash
kr scan https://api.example.com -w routes-large.kite
```

Hunt for Postman collections that companies have published publicly — `site:postman.com "example.com"`. Sometimes the collection includes test bearer tokens.

### Test the GraphQL endpoint for introspection

```bash
curl -X POST https://example.com/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ __schema { types { name } } }"}'
```

If introspection is enabled in production, you've got the schema for free. Tools like [`graphql-cop`](https://github.com/dolevf/graphql-cop) and [`InQL`](https://github.com/doyensec/inql) automate further enumeration.

### Look in mobile apps

Decompile the APK with `apktool d app.apk` or `jadx-gui app.apk`. Search for `https://`, `/api/`, `Authorization` strings. Mobile apps often hit endpoints the web client doesn't.

---

## Testing patterns with curl

Practical curl recipes you'll reuse:

```bash
# JSON GET with auth
curl -H 'Authorization: Bearer eyJ...' \
     -H 'Accept: application/json' \
     https://api.example.com/v1/me

# JSON POST
curl -X POST -H 'Authorization: Bearer eyJ...' \
     -H 'Content-Type: application/json' \
     -d '{"title":"x","role":"admin"}' \
     https://api.example.com/v1/notes

# Switch content type to see what server accepts
curl -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'title=x&role=admin' \
     https://api.example.com/v1/notes

# Try a forbidden method
curl -X PUT https://api.example.com/v1/users/42 \
     -H 'Content-Type: application/json' \
     -d '{"isAdmin":true}'

# Discover allowed methods
curl -X OPTIONS -i https://api.example.com/v1/users/42

# Replay with a different user's token (BOLA probe)
curl -H 'Authorization: Bearer eyJ...USER_B...' \
     https://api.example.com/v1/users/USER_A_ID

# Watch the request through Burp
curl --proxy http://127.0.0.1:8080 -k \
     https://api.example.com/v1/me

# Pipe JSON through jq for human reading
curl -s https://api.example.com/v1/users/me | jq .

# Save a request to a file for sqlmap to consume
curl -v ... 2>&1 | grep '^>' > req.txt
# (or right-click in Burp → Copy to file)
```

---

## Worked example — the CSOT api-notes challenge

The lab's `/api/notes` accepts a POST. The handler awards the flag if the JSON contains the string `admin` or has `<script>` in the title:

```python
@app.route("/api/notes", methods=["GET", "POST"])
def api_notes():
    if request.method == "GET":
        return jsonify({"notes": []})
    data = request.get_json(force=True, silent=True) or {}
    title = data.get("title", "")
    if "<script>" in title.lower() or "admin" in json.dumps(data):
        return jsonify({"ok": True, "flag": FLAGS["api"]})
    return jsonify({"ok": True, "stored": title})
```

Solve:

```bash
curl -X POST http://127.0.0.1:5000/api/notes \
  -H 'Content-Type: application/json' \
  -d '{"title":"hello","role":"admin"}'
# {"flag":"csot26{api_json_injection}","ok":true}
```

This is a teaching version of two real bugs at once: **mass assignment** (the API treats every key as input) and **excessive trust** (no schema, no allow-list). In a real app, a `role` you didn't intend to set would be persisted and would silently grant privileges.

The challenge is [../../CTFs/week-03/api-notes/](../../CTFs/week-03/api-notes/).

---

## Burp workflow for APIs

The same Burp you used for the website works for the API:

1. Set scope to the API host(s).
2. Run the frontend through Burp so you populate HTTP history with real API calls.
3. Send each interesting request to Repeater.
4. Per request, walk the OWASP API Top 10: BOLA (change IDs), mass assignment (add fields), function-level (try as another role), rate limit (Intruder 1000 reps).
5. For tokens, see the next module — install the **JWT Editor** extension and decode + re-sign in place.

Useful Burp extensions for APIs:

- **JWT Editor** — decode/edit/re-sign JWTs.
- **Autorize** — automated horizontal-auth testing.
- **Postman Integration / Inserter** — pull endpoints from Postman collections.
- **JSON Beautifier** — readable Repeater views.
- **Logger++** — searchable history with column filters for response sizes / paths.

---

## API gateways and edge protection

Production APIs often sit behind a gateway (AWS API Gateway, Apigee, Kong, Cloudflare, Akamai) that enforces some of the OWASP API Top 10 outside the application:

| Defense | Layer | Catches |
|---------|-------|---------|
| API key validation | Gateway | API2 partially |
| Rate limit per key/IP | Gateway | API4, API6 |
| Schema validation (OpenAPI) | Gateway | Mass assignment, malformed requests |
| Request body size limit | Gateway / WAF | API4 |
| CORS policy | Gateway / WAF | API8 |
| WAF rules | WAF | Injection, SSRF |

A gateway doesn't make the underlying API safe; it makes the loudest attacks louder. **Authorization** still has to live in the app.

---

## Gotchas

- A `200 OK` with `{"error": "..."}` is not a "success." Always read the body, not just the status.
- A "missing" endpoint that returns `404` may be lying — try the same path with a different method (`OPTIONS`, `POST`) and see if it changes.
- Bearer tokens in URLs (`?token=...`) end up in logs, referers, CDNs. Always test if the API also accepts them in the header — it usually does, even if the docs say otherwise.
- APIs with no `Content-Type` enforcement can be tricked by switching JSON to form-encoded or vice versa. Many parsers behave differently per content type.
- An OPTIONS preflight can leak the full method/header allow-list for an endpoint, even if the endpoint itself returns 403 on GET.

---

## Further reading

- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/) — official, including extended examples.
- [PortSwigger — API testing](https://portswigger.net/web-security/api-testing) — guided labs with Burp.
- [HackTricks — REST API pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web/web-api-pentesting) — checklist.
- [Inon Shkedy's "31 Days of API Security Tips"](https://github.com/inonshk/31-days-of-API-Security-Tips) — practical mini-essays.
- [APIsecurity.io newsletter](https://apisecurity.io/) — weekly real-world API breaches.
- [kiterunner](https://github.com/assetnote/kiterunner) — Swagger-route brute-force.
- [graphql-cop](https://github.com/dolevf/graphql-cop), [InQL](https://github.com/doyensec/inql) — GraphQL tooling.

---

## Next module

[jwt-and-apis.md](jwt-and-apis.md) — JWTs deserve their own module. The token format, the algorithms, the famous `alg: none` bug, the key-confusion attacks, and how to inspect/modify/forge tokens with `jwt_tool` and Burp.
