# Self-Publishing Guide

> For operators who run both the Publisher Action and the Registry Action from the same repository. Covers the combined setup, correct run order, end-to-end verification, and the limitations of same-repo independence.

---

## What self-publishing means

A self-publishing repository runs both workflows:

- **Publisher Action** (`moat.yml`) — signs content hashes and writes `moat-attestation.json` to the `moat-attestation` branch
- **Registry Action** (`moat-registry.yml`) — crawls the same repo, reads `moat-attestation.json`, verifies publisher Rekor entries, and publishes a signed `registry.json` manifest

The content items, the publisher attestation, and the registry manifest all live in the same repository. This is valid — two distinct GitHub Actions OIDC identities are involved (one per workflow file), producing two independently verifiable Rekor entries per item.

**The `self_published` flag:** The Registry Action detects when the source URI matches the registry's own repository and sets `self_published: true` in `registry.json`. This surfaces same-repo origin to clients and conforming tools.

This repository (`OpenScribbler/moat`) is a live working example of self-publishing.

---

## Prerequisites

- A GitHub repository with content in a recognized layout (see [Publisher Action Guide — Content Discovery](publisher.md#content-discovery))
- No additional software — Python 3.9+ and `cosign` are installed by the workflows

---

## Setup

### 1. Create `registry.yml`

```yaml
schema_version: 1

registry:
  name: my-registry
  operator: Your Name
  manifest_uri: https://raw.githubusercontent.com/<owner>/<repo>/main/registry.json

sources:
  - uri: https://github.com/<owner>/<repo>   # point at yourself

revocations: []
```

The source URI should point to the same repository. The Registry Action compares this against its own `GITHUB_REPOSITORY` to detect self-publishing and set `self_published: true`.

### 2. Copy both workflow files

Copy [`reference/moat.yml`](../../reference/moat.yml) to `.github/workflows/moat.yml`:

```yaml
on:
  push:
    branches:
      - main
    paths-ignore:
      - 'moat-attestation/**'
```

Copy [`reference/moat-registry.yml`](../../reference/moat-registry.yml) to `.github/workflows/moat-registry.yml`:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'   # daily
  push:
    paths:
      - 'registry.yml'
  workflow_dispatch:
```

**Important:** The Registry Action trigger must NOT include `push: branches: [main]`. It only needs the schedule, the `registry.yml` path trigger, and manual dispatch. If it triggered on every push to `main`, it would run every time the Publisher Action commits `moat-attestation.json` updates (which can happen on a different branch, but keep the triggers clean).

### 3. Verify permissions

Both workflows need:

```yaml
permissions:
  id-token: write   # Sigstore OIDC signing
  contents: write   # Pushing moat-attestation or registry.json
```

---

## Run order

The run order matters: the Publisher Action must complete before the Registry Action runs, so the Registry Action can find and verify the publisher's Rekor entries.

**First-time setup:**

1. Push your changes (adds workflow files + `registry.yml`) → triggers Publisher Action automatically
2. Wait for Publisher Action to complete (creates `moat-attestation` branch with `moat-attestation.json`)
3. Manually trigger the Registry Action:

```bash
gh workflow run moat-registry.yml --repo <owner>/<repo>
```

**Ongoing operation:**

After initial setup, the sequence is automatic:
- Push to `main` → Publisher Action runs → updates `moat-attestation.json`
- Registry Action runs on schedule (daily) → reads updated `moat-attestation.json` → promotes items to `Dual-Attested`

For immediate promotion after a content change (without waiting for the daily schedule):

```bash
# After confirming Publisher Action has completed:
gh workflow run moat-registry.yml --repo <owner>/<repo>
```

---

## End-to-end verification

### Step 1 — Verify the publisher attestation

```bash
# Fetch moat-attestation.json from the moat-attestation branch
gh api "repos/<owner>/<repo>/contents/moat-attestation.json?ref=moat-attestation" \
  --jq '.content' | base64 -d | python3 -m json.tool
```

Confirm:
- `publisher_workflow_ref` is present and matches `.github/workflows/moat.yml@refs/heads/main`
- Each content item has a `rekor_log_index`

### Step 2 — Verify the registry manifest

```bash
gh api repos/<owner>/<repo>/contents/registry.json \
  --jq '.content' | base64 -d | python3 -m json.tool
```

Confirm:
- `self_published` is `true`
- `registry_signing_profile.subject` ends with `moat-registry.yml@refs/heads/main`
- Content items have `signing_profile` (indicating `Dual-Attested`)

### Step 3 — Verify the manifest signature

```bash
gh api repos/<owner>/<repo>/contents/registry.json \
  --jq '.content' | base64 -d > /tmp/registry.json

gh api repos/<owner>/<repo>/contents/registry.json.sigstore \
  --jq '.content' | base64 -d > /tmp/registry.json.sigstore

cosign verify-blob \
  --bundle /tmp/registry.json.sigstore \
  --certificate-identity "https://github.com/<owner>/<repo>/.github/workflows/moat-registry.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  /tmp/registry.json
# Expected: Verified OK
```

### Step 4 — Verify a publisher Rekor entry

Pick an item from `moat-attestation.json` and confirm its Rekor entry:

```bash
LOG_INDEX=<rekor_log_index from moat-attestation.json>
CONTENT_HASH="<content_hash from same item>"

curl -s "https://rekor.sigstore.dev/api/v1/log/entries?logIndex=${LOG_INDEX}" \
  | python3 -c "
import sys, json, base64, hashlib

entry = next(iter(json.load(sys.stdin).values()))
body = json.loads(base64.b64decode(entry['body']))
entry_hash = body['spec']['data']['hash']['value']

content_hash = '${CONTENT_HASH}'
canonical = json.dumps({'_version': 1, 'content_hash': content_hash},
                       separators=(',', ':'), sort_keys=True).encode('utf-8')
expected = hashlib.sha256(canonical).hexdigest()

print('Publisher entry hash match:', entry_hash == expected)
"
```

### Step 5 — Verify a registry Rekor entry

Pick the same item's `rekor_log_index` from `registry.json` (this is a different entry — the registry's own signing):

```bash
LOG_INDEX=<rekor_log_index from registry.json content[]>
CONTENT_HASH="<content_hash from same item>"

curl -s "https://rekor.sigstore.dev/api/v1/log/entries?logIndex=${LOG_INDEX}" \
  | python3 -c "
import sys, json, base64, hashlib

entry = next(iter(json.load(sys.stdin).values()))
body = json.loads(base64.b64decode(entry['body']))
entry_hash = body['spec']['data']['hash']['value']

content_hash = '${CONTENT_HASH}'
canonical = json.dumps({'_version': 1, 'content_hash': content_hash},
                       separators=(',', ':'), sort_keys=True).encode('utf-8')
expected = hashlib.sha256(canonical).hexdigest()

print('Registry entry hash match:', entry_hash == expected)
"
```

Both entries should match. They cover the same canonical payload `{"_version":1,"content_hash":"<hex>"}` but were signed by different OIDC identities (`moat.yml` vs `moat-registry.yml`).

---

## What `self_published: true` means

`self_published: true` in `registry.json` signals that the organization running the registry is the same organization that produced the content. Clients and conforming tools may surface this to End Users.

The independence guarantee in self-publishing comes from OIDC subject binding, not organizational separation:

- Publisher OIDC subject: `https://github.com/<owner>/<repo>/.github/workflows/moat.yml@refs/heads/main`
- Registry OIDC subject: `https://github.com/<owner>/<repo>/.github/workflows/moat-registry.yml@refs/heads/main`

These are two distinct, independently verifiable Rekor entries. Compromising one workflow's execution context does not automatically compromise the other — a supply-chain attacker who can manipulate the Publisher Action cannot forge the registry's OIDC identity, and vice versa.

---

## Limitations vs. cross-repo Dual-Attested

Self-publishing provides **integrity and tamper evidence** but not **organizational independence**. Anyone with push access to the repository can trigger both workflows. If a single attacker gains control of the repository, they can produce matching publisher and registry attestations.

Cross-repo `Dual-Attested` — where the publisher and registry are controlled by separate GitHub accounts or organizations — provides stronger independence. An attacker who compromises one organization's CI cannot produce matching attestations from the other organization's OIDC identity.

For content distributed to high-security environments, consider whether cross-repo attestation is required. The `self_published` flag in the manifest is the signal downstream clients use to make this distinction.

---

## Troubleshooting

**Items show as `Signed` instead of `Dual-Attested` after first setup**

The most common cause: the Registry Action ran before the Publisher Action completed. Check that:

1. The Publisher Action run completed successfully and `moat-attestation.json` exists on the `moat-attestation` branch
2. The Registry Action ran after that (check run timestamps)

If the Registry Action ran first, manually trigger it again:

```bash
gh workflow run moat-registry.yml --repo <owner>/<repo>
```

**`self_published` is `false` in `registry.json`**

The `sources[].uri` in `registry.yml` does not match the registry repository's own URI. Confirm the URI is exactly `https://github.com/<owner>/<repo>` with no trailing slash.

**Publisher Action triggers Registry Action recursively**

This cannot happen by design — the Publisher Action pushes to the `moat-attestation` branch, not to `main`. The Registry Action is only triggered by changes to `registry.yml`, by schedule, or by `workflow_dispatch`. Verify neither workflow has an accidental `push: branches: [main, moat-attestation]` trigger.
