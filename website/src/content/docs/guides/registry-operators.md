---
title: Registry operator guide
description: How to run a MOAT registry using the Registry Action.
---

> For operators who want to run a MOAT registry — a signed, crawled index of AI agent content. Covers setup, first run, trust tier verification, and revocation.

---

## What you get

A MOAT registry is a GitHub repository that runs a scheduled workflow to:

1. Crawl configured source repositories for content items
2. Compute content hashes and verify publisher attestations (if present)
3. Sign each item's canonical payload with `cosign sign-blob`, producing a Rekor transparency log entry
4. Publish a signed `registry.json` manifest that conforming clients can verify

The result is a tamper-evident, publicly auditable content index. Clients verify the manifest signature, then verify each item's Rekor entry independently.

---

## Prerequisites

- A GitHub repository to host the registry (can be the same repo as your content — see the [Publisher guide](/guides/publishers))
- Python 3.9+ and `cosign` v2.x are installed automatically by the workflow

---

## Setup

### 1. Create `.moat/registry.yml`

Create `.moat/registry.yml`. This is the registry configuration:

```yaml
schema_version: 1

registry:
  name: my-registry            # lowercase letters, digits, hyphens only
  operator: Your Name
  manifest_uri: https://raw.githubusercontent.com/<owner>/<repo>/moat-registry/registry.json

sources:
  - uri: https://github.com/<owner>/<content-repo>
  # add more sources as needed

revocations: []
```

**Field notes:**

| Field | Requirement | Notes |
|---|---|---|
| `schema_version` | REQUIRED | Must be `1` |
| `registry.name` | REQUIRED | Pattern: `[a-z0-9-]+` — used as a stable identifier |
| `registry.operator` | REQUIRED | Display name for the registry operator |
| `registry.manifest_uri` | REQUIRED | The public URL where `registry.json` will be served |
| `sources[].uri` | REQUIRED | GitHub repository URLs |
| `revocations` | REQUIRED | Empty array if none |

The `manifest_uri` should point to the raw file in your repository's `moat-registry` branch — this is where conforming clients and `moat-verify` will fetch the manifest from.

### 2. Copy the workflow file

Copy the workflow file from the [Registry Action spec](/spec/registry-action) to `.github/workflows/moat-registry.yml` in your registry repo.

The workflow is pre-configured with:
- A daily schedule (`cron: '0 0 * * *'`)
- A push trigger on `.moat/registry.yml` changes (for emergency revocation)
- `workflow_dispatch` for manual runs

### 3. Verify required permissions

The workflow needs two permissions. Confirm they are set in the workflow file:

```yaml
permissions:
  id-token: write   # Required for Sigstore OIDC keyless signing
  contents: write   # Required to commit registry.json
```

If your repository has default permissions set to read-only in organization settings, you may need to explicitly grant write access to this workflow.

---

## First run

Trigger the Registry Action manually:

```bash
gh workflow run moat-registry.yml --repo <owner>/<repo>
```

Watch it:

```bash
gh run list --repo <owner>/<repo> --workflow=moat-registry.yml --limit=5
gh run watch <run-id> --repo <owner>/<repo>
```

A successful run commits `registry.json` and `registry.json.sigstore` to your `moat-registry` branch and ends with:

```
Manifest committed and pushed.
```

### What if a source has no `moat-attestation.json` yet?

The Registry Action does not block on missing publisher attestations. If a source repo has not yet run its Publisher Action — or has run it but the `moat-attestation` branch is empty — the registry indexes that source's items as `Signed`, not `Dual-Attested`, and continues normally.

This matters most in two situations:

1. **You operate the registry and run sources you also publish from.** If you push the `.moat/registry.yml` config in the same commit as the publisher workflow, the registry will probably finish before the publisher creates the `moat-attestation` branch. First-run items show up as `Signed`. Re-trigger the registry after the publisher completes; items get promoted to `Dual-Attested`. See the [self-publishing guide](/guides/self-publishing#what-to-expect-on-the-first-push) for the recommended sequence.
2. **You added a new source that is still adopting the Publisher Action.** Their items show as `Signed` on every crawl until they push their workflow. No action needed on your side — the next crawl after they ship will promote automatically.

---

## Verify the manifest

### Fetch registry.json

The manifest lives on the `moat-registry` branch, not `main`:

```bash
gh api "repos/<owner>/<repo>/contents/registry.json?ref=moat-registry" \
  --jq '.content' | base64 -d | python3 -m json.tool
```

### What a valid `registry.json` looks like

```json
{
  "schema_version": 1,
  "manifest_uri": "https://raw.githubusercontent.com/<owner>/<repo>/moat-registry/registry.json",
  "name": "my-registry",
  "operator": "Your Name",
  "updated_at": "2026-04-11T04:48:55Z",
  "self_published": false,
  "registry_signing_profile": {
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "https://github.com/<owner>/<repo>/.github/workflows/moat-registry.yml@refs/heads/main"
  },
  "content": [
    {
      "name": "my-summarizer",
      "display_name": "My Summarizer",
      "type": "skill",
      "content_hash": "sha256:abc123...",
      "source_uri": "https://github.com/<owner>/<content-repo>",
      "attested_at": "2026-04-11T04:48:55Z",
      "private_repo": false,
      "rekor_log_index": 12345678
    }
  ],
  "revocations": []
}
```

Check each field:

| Field | Expected |
|---|---|
| `registry_signing_profile.subject` | Your registry workflow path: `...moat-registry.yml@refs/heads/main` |
| `content[].rekor_log_index` | A positive integer for each Signed/Dual-Attested item |
| `content[].trust_tier` | `Dual-Attested`, `Signed`, or `Unsigned` |

### Verify the signing bundle

The manifest's `.sigstore` bundle is committed alongside `registry.json`. Verify it with `cosign`:

```bash
# Fetch both files
gh api "repos/<owner>/<repo>/contents/registry.json?ref=moat-registry" \
  --jq '.content' | base64 -d > /tmp/registry.json

gh api "repos/<owner>/<repo>/contents/registry.json.sigstore?ref=moat-registry" \
  --jq '.content' | base64 -d > /tmp/registry.json.sigstore

# Verify the bundle covers the manifest
cosign verify-blob \
  --bundle /tmp/registry.json.sigstore \
  --certificate-identity "https://github.com/<owner>/<repo>/.github/workflows/moat-registry.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  /tmp/registry.json
```

Expected:
```
Verified OK
```

### Verify a per-item Rekor entry

For any item in `content[]`, confirm its Rekor entry covers the expected content hash:

```bash
LOG_INDEX=12345678        # from content[].rekor_log_index
CONTENT_HASH="sha256:..."  # from content[].content_hash

curl -s "https://rekor.sigstore.dev/api/v1/log/entries?logIndex=${LOG_INDEX}" \
  | python3 -c "
import sys, json, base64, hashlib

entry = next(iter(json.load(sys.stdin).values()))
body = json.loads(base64.b64decode(entry['body']))
entry_hash = body['spec']['data']['hash']['value']

content_hash = '${CONTENT_HASH}'
canonical = json.dumps({'_version': 1, 'content_hash': content_hash},
                       separators=(',', ':'), sort_keys=True).encode('utf-8')
expected_hash = hashlib.sha256(canonical).hexdigest()

print('Entry hash:    ', entry_hash[:16] + '...')
print('Expected hash: ', expected_hash[:16] + '...')
print('Match:', entry_hash == expected_hash)
"
```

---

## Understanding trust tiers

Each item in `content[]` is assigned one of three trust tiers. The tier is determined at crawl time:

| Tier | What it means | `signing_profile` in manifest? |
|---|---|---|
| `Dual-Attested` | Registry-signed + publisher independently attested the same hash | Yes |
| `Signed` | Registry-signed only | No |
| `Unsigned` | No Rekor entry (no `rekor_log_index`) | No |

### What triggers Dual-Attested

For an item to qualify as `Dual-Attested`:

1. The source repository must have a `moat-attestation` branch with a `moat-attestation.json` file
2. The file must contain an entry for the item with a `rekor_log_index`
3. The Registry Action fetches that Rekor entry and verifies:
   - The payload hash matches the canonical payload for the item's content hash
   - The OIDC subject in the certificate matches the publisher's workflow path (read from `publisher_workflow_ref`)

If all three pass, the item gets `signing_profile` written to the manifest entry. Look for this in the action log:

```
  Item: my-summarizer (skill)
    Content hash: sha256:abc123...
    Publisher Rekor entry found at #12345678
    Trust tier: Dual-Attested ✓
```

If verification fails, you'll see:

```
Publisher Rekor verification failed for skills/my-summarizer (log index 12345678):
  Expected OIDC subject: https://github.com/<owner>/<content-repo>/.github/workflows/moat-publisher.yml@refs/heads/main
  Observed OIDC subject: https://github.com/<owner>/<content-repo>/.github/workflows/ci.yml@refs/heads/main
  Item will be indexed as Signed.
```

The item is still indexed — it just falls back to `Signed`.

---

## Adding sources

Add source URIs to `.moat/registry.yml`:

```yaml
sources:
  - uri: https://github.com/alice/skills-collection
  - uri: https://github.com/bob/agent-tools
  - uri: https://github.com/org/shared-rules
```

Push the change to `.moat/registry.yml` — this triggers the Registry Action via the path trigger, so you don't need to wait for the next scheduled run.

Sources that fail to respond (network error, non-existent repo, rate limit) are skipped with a warning — they don't abort the run. The manifest is updated with whichever sources succeeded.

---

## Revocation

To revoke a content item, add an entry to `revocations` in `.moat/registry.yml` and push:

```yaml
revocations:
  - content_hash: sha256:abc123...
    reason: malicious           # malicious | compromised | deprecated | policy_violation
    details_url: https://github.com/<owner>/<repo>/security/advisories/GHSA-xxxx
```

The push triggers the Registry Action immediately (via the `.moat/registry.yml` path trigger). On the next run, the revoked item is removed from `content[]` and added to `revocations[]` in `registry.json`.

**Reason code urgency signals** (informational — for display to end users):

| Reason | Urgency |
|---|---|
| `malicious` | High — surface prominently |
| `compromised` | High — surface prominently |
| `policy_violation` | Informational |
| `deprecated` | Low |

Revocations are permanent in `registry.json`. If you un-revoke a hash later, remove the entry from `.moat/registry.yml` — the item will be re-indexed on the next crawl.

---

## Troubleshooting

**All sources fail, manifest not updated**

If every source in `sources` fails, the action exits non-zero and does not update `registry.json`. Check the action log for per-source error messages. Common causes: private repository without `allow-private-source: true`, invalid URI format, GitHub API rate limit.

**Private source skipped — the warning you'll see**

When a source repo is private (or internal) and you have not set `allow-private-source: true` for it in `.moat/registry.yml`, the action prints this in the `Run MOAT registry action` step and skips the source:

```
Processing source: https://github.com/<owner>/<repo>
  Self-publishing detected.
  WARNING: Source is private; skipping (set allow-private-source: true to index).
```

The `Self-publishing detected.` line only appears if the source URI matches the registry's own repo. The warning itself fires for any private source.

If that source was the only one configured, the next thing in the log is the fatal error and the failed exit:

```
error: all sources failed — no manifest update produced
##[error]Process completed with exit code 1.
```

The actionable line is the WARNING — it names the field you need to set. The "all sources failed" line is just the consequence. Set `allow-private-source: true` on that source's entry and re-run, or make the source repo public.

**Items show as `Signed` instead of `Dual-Attested`**

See the trust tier section above. Check the action log for `Publisher Rekor verification failed` messages. If the publisher recently renamed their workflow file, their old Rekor entries won't match and they need to retrigger their Publisher Action.

**`registry_signing_profile.subject` is wrong**

The subject is derived at runtime from `GITHUB_WORKFLOW_REF`. If the workflow file is named differently from `moat-registry.yml`, the subject will reflect the actual filename. This is expected — the self-recorded subject is what clients use to verify the manifest.

**`cosign verify-blob` fails on the manifest bundle**

Confirm the `--certificate-identity` exactly matches the `registry_signing_profile.subject` in `registry.json`. Even a trailing slash or case difference causes failure.
