# Publisher Action Guide

> For source repo owners who want to co-sign their content and qualify for the `Dual-Attested` trust tier. Covers setup, first run, and how to verify everything is working.

---

## What you get

When a registry crawls your repository, it checks whether you have a `moat-attestation.json` on the `moat-attestation` branch with valid Rekor entries for each content item. If it finds them and the Rekor signatures check out, your content is indexed as `Dual-Attested` instead of `Signed`.

`Dual-Attested` means: the registry attested the content, AND the source repository's own CI independently attested the same content hash. Neither can tamper with the other's entry.

---

## Prerequisites

- A GitHub repository containing content in one of the recognized layouts (see [Content Discovery](#content-discovery))
- Python 3.9+ and `cosign` v2.x are installed automatically by the workflow — you do not need them locally

---

## Content discovery

The Publisher Action finds content items using the same two-tier model as the Registry Action:

**Tier 1 — canonical directories:** Any of `skills/`, `subagents/`, `rules/`, `commands/` at the repository root. Each subdirectory inside one of these is treated as one content item.

```
my-repo/
  skills/
    my-summarizer/     ← one item, type: skill
      SKILL.md
      ...
    my-formatter/      ← one item, type: skill
      SKILL.md
      ...
  rules/
    coding-standards/  ← one item, type: rules
      rules.md
```

**Tier 2 — `.moat/publisher.yml` config:** For custom layouts, create `.moat/publisher.yml`:

```yaml
items:
  - name: my-tool
    type: skill
    path: tools/my-tool
  - name: shared-rules
    type: rules
    path: config/rules
```

Tier 2 supplements Tier 1 — both are discovered if both are present.

---

## Setup

### 1. Copy the workflow file

Copy [`reference/moat-publisher.yml`](../../reference/moat-publisher.yml) from this repository to `.github/workflows/moat-publisher.yml` in your source repo. The recommended filename is `moat-publisher.yml` — you may use a different name, but the filename is encoded into the Rekor certificate and registries use it to verify your attestation (see [Workflow filename](#workflow-filename)).

### 2. Configure the trigger

The default workflow triggers on push to `main`. If your default branch is named differently, update the trigger:

```yaml
on:
  push:
    branches:
      - trunk    # or whatever your default branch is named
    paths-ignore:
      - 'moat-attestation/**'
```

The `paths-ignore` guard is belt-and-suspenders — recursive execution is structurally impossible because the action pushes to `moat-attestation`, not to the triggering branch. Keep it for clarity.

### 3. Private repositories (optional)

By default the action exits with an error if your repository is `private` or `internal`. If you intentionally want to attest a private repo, set:

```yaml
env:
  ALLOW_PRIVATE_REPO: 'true'
```

**Note:** Content hashes and repository identity are permanently recorded in the public Rekor transparency log regardless of repository visibility. The content itself is not uploaded, but the metadata is public and irreversible.

---

## First run

Push any change to your default branch to trigger the Publisher Action, or trigger it manually:

```bash
gh workflow run moat-publisher.yml --repo <owner>/<repo>
```

Watch it run:

```bash
gh run list --repo <owner>/<repo> --workflow=moat-publisher.yml --limit=5
gh run watch <run-id> --repo <owner>/<repo>
```

A successful run ends with:

```
Done. moat-attestation branch updated.
```

---

## Verify the attestation

### Check the branch exists

```bash
git fetch origin moat-attestation
git show origin/moat-attestation:moat-attestation.json | python3 -m json.tool
```

Or via the GitHub API:

```bash
gh api repos/<owner>/<repo>/contents/moat-attestation.json \
  --header "X-GitHub-Raw" \
  --raw \
  | python3 -m json.tool
```

Wait — the file is on the `moat-attestation` branch, not `main`. Use:

```bash
gh api "repos/<owner>/<repo>/contents/moat-attestation.json?ref=moat-attestation" \
  --jq '.content' | base64 -d | python3 -m json.tool
```

### What a valid `moat-attestation.json` looks like

```json
{
  "schema_version": 1,
  "attested_at": "2026-04-11T04:30:00Z",
  "publisher_workflow_ref": ".github/workflows/moat-publisher.yml@refs/heads/main",
  "private_repo": false,
  "items": [
    {
      "name": "my-summarizer",
      "content_hash": "sha256:abc123...",
      "source_ref": "def456...",
      "rekor_log_id": "24296fb24b8ad77a...",
      "rekor_log_index": 12345678
    }
  ],
  "revocations": []
}
```

Check each field:

| Field | Expected |
|---|---|
| `schema_version` | `1` |
| `publisher_workflow_ref` | Your workflow path + ref, e.g. `.github/workflows/moat-publisher.yml@refs/heads/main` |
| `private_repo` | `false` for public repos; `true` only if you set `ALLOW_PRIVATE_REPO: 'true'` |
| `items[].name` | Matches your content directory names |
| `items[].rekor_log_index` | A positive integer (the Rekor entry index) |

### Verify the Rekor entry directly

For each item, confirm the Rekor entry covers the expected content hash:

```bash
LOG_INDEX=12345678   # from moat-attestation.json items[].rekor_log_index
CONTENT_HASH="sha256:abc123..."  # from items[].content_hash

# Fetch the Rekor entry
curl -s "https://rekor.sigstore.dev/api/v1/log/entries?logIndex=${LOG_INDEX}" \
  | python3 -c "
import sys, json, base64, hashlib

entry = next(iter(json.load(sys.stdin).values()))
body = json.loads(base64.b64decode(entry['body']))
spec = body['spec']

# Check payload hash
entry_hash = spec['data']['hash']['value']
content_hash = '${CONTENT_HASH}'
canonical = json.dumps({'_version': 1, 'content_hash': content_hash},
                       separators=(',', ':'), sort_keys=True).encode('utf-8')
canonical_hash = hashlib.sha256(canonical).hexdigest()

print('Entry hash:    ', entry_hash[:16] + '...')
print('Expected hash: ', canonical_hash[:16] + '...')
print('Match:', entry_hash == canonical_hash)
"
```

Expected output:
```
Entry hash:     <first 16 hex chars>...
Expected hash:  <same first 16 hex chars>...
Match: True
```

### Verify the OIDC subject

The certificate in the Rekor entry must show your repo and workflow path:

```bash
LOG_INDEX=12345678

curl -s "https://rekor.sigstore.dev/api/v1/log/entries?logIndex=${LOG_INDEX}" \
  | python3 -c "
import sys, json, base64
from cryptography import x509

entry = next(iter(json.load(sys.stdin).values()))
body = json.loads(base64.b64decode(entry['body']))
cert_b64 = body['spec']['signature']['publicKey']['content']
cert = x509.load_pem_x509_certificate(base64.b64decode(cert_b64))
san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
uris = san.value.get_values_for_type(x509.UniformResourceIdentifier)
print('OIDC subject:', uris[0] if uris else '(none)')
"
```

Expected:
```
OIDC subject: https://github.com/<owner>/<repo>/.github/workflows/moat-publisher.yml@refs/heads/main
```

---

## Getting to Dual-Attested

Once your `moat-attestation.json` is published, any registry that includes your repo as a source will see it on the next crawl. What the registry checks:

1. Fetches `moat-attestation.json` from your `moat-attestation` branch
2. For each item, fetches the Rekor entry at `rekor_log_index`
3. Reconstructs `{"_version":1,"content_hash":"<hash>"}` and confirms it matches the Rekor entry hash
4. Confirms the OIDC subject in the certificate matches your repo and workflow path (read from `publisher_workflow_ref`)

If all four pass, your item is indexed as `Dual-Attested` and the `signing_profile` field is written to the manifest entry.

You don't need to notify registries — they crawl on schedule. If the registry supports the optional webhook, you can configure it for faster propagation (see `registry-webhook` in the [Publisher Action spec](../../specs/github/publisher-action.md)).

---

## Workflow filename

The Publisher Action can be named anything — the actual filename is recorded automatically in `publisher_workflow_ref` in `moat-attestation.json`, and registries read this field to derive the expected OIDC subject. The recommended filename is `.github/workflows/moat-publisher.yml`.

If you rename the workflow file after your first run, the existing Rekor entries in `moat-attestation.json` were signed with the old filename and will fail verification with registries that have already crawled you. To fix: retrigger the Publisher Action (which creates new Rekor entries with the new filename) and wait for registries to re-crawl.

---

## Troubleshooting

**Run succeeds but `moat-attestation` branch doesn't exist**

The action only creates the branch if it finds content items. Check:
- Your repo has at least one content directory (`skills/`, `subagents/`, `rules/`, `commands/`) or a `.moat/publisher.yml` config
- Content directories are not empty

**`rekor_log_index` is missing from an item**

The Sigstore signing step failed for that item. Check the workflow run log for `cosign sign-blob failed:` output.

**Items show as `Signed` instead of `Dual-Attested` at a registry**

The registry ran publisher verification and it failed. Common causes:
1. The `publisher_workflow_ref` in your `moat-attestation.json` does not match the OIDC subject in the Rekor entry — this happens if you renamed the workflow file after signing
2. The registry is using an old `moat-attestation.json` — wait for the next crawl or use the webhook to notify

Check the registry's action log for a `Publisher Rekor verification failed` message — it will show the expected vs. observed OIDC subject.

**Private repository error**

```
error: repository visibility is 'private'. Set ALLOW_PRIVATE_REPO: 'true' to attest private repositories.
```

Set `ALLOW_PRIVATE_REPO: 'true'` in the workflow env block and re-read the warning about Rekor permanence before proceeding.
