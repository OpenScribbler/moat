---
title: Self-publishing guide
description: How to run both the Publisher Action and the Registry Action from the same repository.
---

> For operators who run the Publisher Action and the Registry Action from the same repository. Covers the combined setup, what to expect on the first push, end-to-end verification, and the limits of same-repo independence.

This guide assumes you have already read the [Publisher guide](/guides/publishers) and the [Registry operator guide](/guides/registry-operators). Those cover each action in isolation. This page covers what changes when both run in one repo.

---

## What self-publishing means

A self-publishing repository runs both workflows:

- **Publisher Action** — `.github/workflows/moat-publisher.yml` signs each content item and pushes `moat-attestation.json` to the `moat-attestation` branch.
- **Registry Action** — `.github/workflows/moat-registry.yml` crawls the same repo, reads `moat-attestation.json`, verifies the publisher's Rekor entries, and publishes a signed `registry.json` manifest to the `moat-registry` branch.

The content items, the publisher attestation, and the registry manifest all live in the same repository. This is valid — two distinct GitHub Actions OIDC identities are involved (one per workflow file), producing two independently verifiable Rekor entries per item.

**The `self_published` flag.** The Registry Action detects when a source URI matches the registry's own repository and sets `self_published: true` in `registry.json`. This surfaces same-repo origin to clients and conforming tools.

The MOAT spec repository (`OpenScribbler/moat`) is itself a live, working example of self-publishing.

---

## Prerequisites

- A GitHub repository with content in a recognized layout (see [Publisher guide — Content discovery](/guides/publishers#content-discovery)).
- Repository visibility is `public`. If your repo is `private` or `internal`, see [Private repositories](#private-repositories) before continuing.
- No additional software — Python 3.9+ and `cosign` are installed by the workflows.

---

## Setup

The setup is three files. Add them in one commit and push.

### 1. `.github/workflows/moat-publisher.yml`

Copy the reference workflow from [`reference/moat-publisher.yml`](https://github.com/OpenScribbler/moat/blob/main/reference/moat-publisher.yml) verbatim.

The default trigger is push to `main`. If your default branch is named differently, update `branches:` accordingly.

### 2. `.github/workflows/moat-registry.yml`

Copy the reference workflow from [`reference/moat-registry.yml`](https://github.com/OpenScribbler/moat/blob/main/reference/moat-registry.yml) verbatim.

The default triggers are:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'   # daily
  push:
    paths:
      - '.moat/registry.yml'
  workflow_dispatch:
```

**Do not** add `push: branches: [main]` to the Registry Action. The Publisher Action runs on every push to `main` already; the Registry Action should run on schedule, on config changes, and on manual dispatch.

### 3. `.moat/registry.yml`

```yaml
schema_version: 1

registry:
  name: my-registry
  operator: Your Name or Org
  manifest_uri: https://raw.githubusercontent.com/<owner>/<repo>/moat-registry/registry.json

sources:
  - uri: https://github.com/<owner>/<repo>   # point at yourself

revocations: []
```

The `sources[].uri` should match the same repository. The Registry Action compares this against its own `GITHUB_REPOSITORY` to detect self-publishing and set `self_published: true`.

---

## What to expect on the first push

When you push all three files in a single commit, **both workflows trigger simultaneously**:

- The Publisher Action triggers because of the push to `main`.
- The Registry Action triggers because `.moat/registry.yml` is a new file matching its `paths:` trigger.

This is expected, but it has a consequence: the Registry Action will probably finish before the Publisher Action has created the `moat-attestation` branch. On that first run, your items will be indexed as `Signed`, not `Dual-Attested`, because the registry could not find a publisher attestation to verify against.

**Recovery is automatic.** Once the Publisher Action completes and `moat-attestation.json` exists on the `moat-attestation` branch, manually re-trigger the Registry Action:

```bash
gh workflow run moat-registry.yml --repo <owner>/<repo>
```

After this second run, items are promoted to `Dual-Attested`. From that point on, the daily schedule keeps everything in sync.

If you want to avoid the temporary `Signed` state on day one, push the workflows first, wait for the Publisher Action to finish, then push `.moat/registry.yml` in a follow-up commit.

---

## Run order in steady state

After initial setup, the sequence is automatic:

- Push to `main` → Publisher Action runs → updates `moat-attestation.json`.
- Registry Action runs on schedule (daily) → reads updated `moat-attestation.json` → items remain `Dual-Attested`.

For immediate promotion after a content change without waiting for the daily schedule, manually re-trigger the Registry Action after the Publisher Action completes:

```bash
gh workflow run moat-registry.yml --repo <owner>/<repo>
```

---

## End-to-end verification

### Step 1 — Verify the publisher attestation

```bash
gh api "repos/<owner>/<repo>/contents/moat-attestation.json?ref=moat-attestation" \
  --jq '.content' | base64 -d | python3 -m json.tool
```

Confirm:

- `publisher_workflow_ref` is `.github/workflows/moat-publisher.yml@refs/heads/main`.
- Each item under `items[]` has a `rekor_log_index`.

### Step 2 — Verify the registry manifest

```bash
gh api "repos/<owner>/<repo>/contents/registry.json?ref=moat-registry" \
  --jq '.content' | base64 -d | python3 -m json.tool
```

Confirm:

- `self_published` is `true`.
- `registry_signing_profile.subject` ends with `moat-registry.yml@refs/heads/main`.
- Items under `content[]` carry a `signing_profile` field, indicating `Dual-Attested`.

### Step 3 — Verify the manifest signature

```bash
gh api "repos/<owner>/<repo>/contents/registry.json?ref=moat-registry" \
  --jq '.content' | base64 -d > /tmp/registry.json

gh api "repos/<owner>/<repo>/contents/registry.json.sigstore?ref=moat-registry" \
  --jq '.content' | base64 -d > /tmp/registry.json.sigstore

cosign verify-blob \
  --bundle /tmp/registry.json.sigstore \
  --certificate-identity "https://github.com/<owner>/<repo>/.github/workflows/moat-registry.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  /tmp/registry.json
# Expected: Verified OK
```

### Step 4 — Verify a publisher Rekor entry

Pick an item from `moat-attestation.json` and confirm its Rekor entry. See [Publisher guide — Verify the Rekor entry directly](/guides/publishers#verify-the-rekor-entry-directly) for the full snippet.

### Step 5 — Verify a registry Rekor entry

Pick the same item's `rekor_log_index` from `registry.json` (this is a different entry — the registry's own signing). See [Registry operator guide — Verify a per-item Rekor entry](/guides/registry-operators#verify-a-per-item-rekor-entry).

Both entries should match. They cover the same canonical payload `{"_version":1,"content_hash":"<hex>"}` but were signed by two different OIDC identities (`moat-publisher.yml` vs. `moat-registry.yml`).

---

## What `self_published: true` means

`self_published: true` in `registry.json` signals that the same organization runs the registry and produced the content. Clients and conforming tools can surface this to end users.

The independence guarantee in self-publishing comes from OIDC subject binding, not organizational separation:

- Publisher OIDC subject: `https://github.com/<owner>/<repo>/.github/workflows/moat-publisher.yml@refs/heads/main`
- Registry OIDC subject: `https://github.com/<owner>/<repo>/.github/workflows/moat-registry.yml@refs/heads/main`

These are two distinct, independently verifiable Rekor entries. Compromising one workflow's execution context does not automatically compromise the other — a supply-chain attacker who can manipulate the Publisher Action cannot forge the registry's OIDC identity, and vice versa.

---

## Limits vs. cross-repo Dual-Attested

Self-publishing provides **integrity and tamper evidence** but not **organizational independence**. Anyone with push access to the repository can trigger both workflows. If a single attacker gains control of the repository, they can produce matching publisher and registry attestations.

Cross-repo `Dual-Attested` — where the publisher and registry are controlled by separate GitHub accounts or organizations — provides stronger independence. An attacker who compromises one organization's CI cannot produce matching attestations from the other organization's OIDC identity.

For content distributed to high-security environments, consider whether cross-repo attestation is required. The `self_published` flag in the manifest is the signal downstream clients use to make this distinction.

---

## Private repositories

If your repo is `private` or `internal`, both actions exit non-zero by default and refuse to run.

### What you'll see when the guards fire

When you push the workflows to a private repo without flipping the opt-in flags, both Actions runs fail. This is the spec's Private Repository Guard.

The Publisher Action prints (in the `Run MOAT publisher action` step):

```
error: repository visibility is 'private'. Set ALLOW_PRIVATE_REPO: 'true' to attest private repositories. Note: content hashes and repository identity will be permanently recorded in the public Rekor transparency log.
##[error]Process completed with exit code 1.
```

The Registry Action prints (in the `Run MOAT registry action` step):

```
Processing source: https://github.com/<owner>/<repo>
  Self-publishing detected.
  WARNING: Source is private; skipping (set allow-private-source: true to index).
error: all sources failed — no manifest update produced
##[error]Process completed with exit code 1.
```

No signing happens before either guard fires, so a failed first run does not leak anything to Rekor.

### Opting in

To opt in, you must flip **two independent guards** — one in each workflow:

1. In `.github/workflows/moat-publisher.yml`, set the env var:

   ```yaml
   env:
     ALLOW_PRIVATE_REPO: 'true'
   ```

2. In `.moat/registry.yml`, mark the source:

   ```yaml
   sources:
     - uri: https://github.com/<owner>/<repo>
       allow-private-source: true
   ```

Read [Publisher guide — Private repositories](/guides/publishers#private-repositories-optional) before flipping these. The summary: content bytes never leave your repo, but content hashes and the repository identity become a permanent public Rekor record. That decision is one-way.

---

## Troubleshooting

**Items stay `Signed` after multiple Registry Action runs.**

The Registry Action ran but publisher Rekor verification failed. Common causes:

1. The Publisher Action has not yet completed for the latest commit — wait, then re-trigger.
2. The publisher workflow filename was changed after first signing. The OIDC subject in old Rekor entries no longer matches `publisher_workflow_ref`. Re-trigger the Publisher Action; the next registry crawl will promote items back to `Dual-Attested`.

Check the Registry Action log for `Publisher Rekor verification failed` — it prints the expected and observed OIDC subjects.

**`self_published` is `false` in `registry.json`.**

The `sources[].uri` in `.moat/registry.yml` does not match the registry repository's own URI. Confirm it is exactly `https://github.com/<owner>/<repo>` with no trailing slash and no `.git` suffix.

**Publisher Action triggers Registry Action recursively.**

This cannot happen by design — the Publisher Action pushes to the `moat-attestation` branch, not to `main`. The Registry Action triggers only on `.moat/registry.yml` changes, on schedule, or via `workflow_dispatch`. If you see recursion, check that neither workflow has an accidental `push: branches: [main, moat-attestation]` trigger.

**Both workflows fail on first push with no obvious error.**

Check repository **Settings → Actions → General → Workflow permissions**. Both workflows need "Read and write permissions" to push to the `moat-attestation` and `moat-registry` branches.
