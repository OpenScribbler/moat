# Use Cases

Who does what in MOAT, and what each actor actually has to do.

---

## "I share skills on GitHub. I don't want to run a registry."

**You are: a publisher.**

You keep your content in a public GitHub repo — skills, rules, sub-agents, whatever. You want people to use them. You have no interest in running infrastructure, managing keys, or learning a new protocol.

**What you do:** Nothing.

MOAT does not require publishers to participate. If a registry operator decides your content is worth indexing, they add your repo URL to their registry config. Their CI crawls your repo on a schedule, computes content hashes from your directories, signs them with the registry's identity, and publishes a manifest. Your content appears in their index as **Signed** — tamper-evident, with a Rekor transparency log entry proving the registry attested it.

You don't set up GitHub Actions. You don't install tools. You don't create accounts. You don't even need to know MOAT exists.

**What the end user sees:** Your content listed in a registry manifest with a `Signed` trust tier. If they install it through a conforming client, the client verifies the content hash matches what the registry signed. If anything was tampered with in transit, the hash breaks and the install fails.

---

## "I want extra assurance on my content."

**You are: a publisher who wants Dual-Attested.**

You've heard about MOAT and you want the strongest trust signal available. You want both the registry *and* your own CI to independently attest the same content hash — so even if a registry is compromised, your independent attestation survives.

**What you do:** Copy one workflow file into `.github/workflows/moat.yml`. That's it.

On every push to your default branch, the Publisher Action:

1. Discovers your content items automatically
2. Computes content hashes
3. Signs them using Sigstore keyless OIDC — no keys to manage, no secrets to configure
4. Writes `moat-attestation.json` to a dedicated branch

When a registry crawls your repo next, it finds your attestation, verifies it against the Rekor transparency log, and promotes your content from Signed to **Dual-Attested**.

**What the end user sees:** Your content listed with a `Dual-Attested` trust tier. This means two independent parties — you and the registry — attested the same content hash in separate Rekor entries. Neither can tamper with the other's entry.

**What if you don't do this?** Nothing bad happens. Your content stays at Signed tier, which is the standard. Dual-Attested is additive confidence, not a requirement. Its absence is not a negative signal.

---

## "I want to run a curated content index."

**You are: a registry operator.**

You want to offer a curated collection of AI agent content — maybe you run a community hub, maybe you're a company distributing approved content to your team. You want to vouch for the content you index and give end users a way to verify your claims.

**What you do:** Create a GitHub repo with two files:

1. **`registry.yml`** — a config listing the source repos you want to index
2. **`.github/workflows/moat-registry.yml`** — the Registry Action workflow (copy from the reference template)

The Registry Action runs on a daily schedule. For each source repo in your config, it:

1. Crawls the repo and discovers content items
2. Computes content hashes
3. Signs each item with your registry's CI identity (Sigstore keyless — no keys)
4. Checks for publisher attestations and determines trust tiers
5. Publishes a signed `registry.json` manifest

You decide what to include. You can add or remove sources at any time by editing `registry.yml`. Publishers don't submit to you — you choose what to index, like a search engine choosing what to crawl.

**What the end user sees:** Your manifest, listing every content item you've indexed with its content hash, trust tier, source URI, and attestation timestamp. They add your registry to their install tool, and the tool verifies everything on install.

---

## "I write content and distribute it myself."

**You are: a self-publisher (publisher + registry operator).**

You create AI agent content and you want to distribute it directly — no third-party registry involved. You run both the Publisher Action and the Registry Action from the same repository.

**What you do:** Add both workflow files to your repo:

- `.github/workflows/moat.yml` (Publisher Action)
- `.github/workflows/moat-registry.yml` (Registry Action)

Both workflows run on push. The Publisher Action attests your content from one CI identity; the Registry Action crawls the same repo, verifies the publisher attestation, and publishes a signed manifest from a different CI identity.

**Why this is valid Dual-Attested:** The two workflows have different OIDC subjects (different workflow file paths), so they produce distinct Rekor entries. The independence comes from the OIDC subject binding, not from organizational separation. The manifest's `self_published: true` field discloses this to end users transparently.

**What the end user sees:** A registry manifest with `self_published: true` and content at the Dual-Attested tier. End users know it's the same operator wearing both hats — the disclosure is built into the manifest.

---

## "I'm installing content and my tool supports MOAT."

**You are: the end user.**

You find a skill or rule you want to use. It's listed in a MOAT registry. Your install tool — a conforming client like a CLI, package manager, or IDE extension — understands the MOAT protocol.

**What happens when you install it:**

1. Your tool fetches the registry manifest and verifies its signature
2. It downloads the content and computes the content hash locally
3. It checks the hash against what the registry attested — if they don't match, the install fails
4. It verifies the Rekor transparency log entry for that item
5. It shows you the trust tier (Dual-Attested, Signed, or Unsigned) before you confirm
6. On install, it writes a lockfile entry with the verified hash and attestation bundle

**What you decide:** Which registries to trust. MOAT doesn't make that decision for you. Adding a registry is an explicit action — nothing is trusted by default.

**What you get going forward:** Your tool checks for revocations on every sync. If a registry revokes something you installed, you're notified. The lockfile means you can also verify offline — proving the content matches what was verified at install time, even without network access.

---

## "I copied content straight from a GitHub repo."

**You are: the end user — but without a conforming client.**

You found a skill in someone's repo and copied the directory into your local setup. No install tool involved — you just cloned or downloaded the files.

**What MOAT can do for you:** You can run `moat-verify` yourself to check whether the content you copied matches what a registry has attested. Point it at the directory and a registry manifest URL:

```
moat-verify ./my-skills/summarizer --registry https://example.com/registry.json
```

If the content hash matches a registry entry, you get the same trust signal a conforming client would show — the registry attested this content, the attestation is logged in Rekor, and nothing was tampered with between the registry's crawl and your copy.

**What you don't get:** Automatic revocation checks, a lockfile, or ongoing monitoring. You verified a point-in-time snapshot. If the registry revokes this content tomorrow, nothing notifies you unless you run `moat-verify` again.

**What if the content isn't in any registry?** `moat-verify` reports that the hash wasn't found. That doesn't mean the content is bad — it means no registry has attested it. You're in the same position as every end user of AI agent content today: trusting the source repo directly, with no independent verification layer.

---

## "My tool doesn't know about MOAT, but I still want to verify."

**You are: the end user — using a non-MOAT tool alongside `moat-verify`.**

Your IDE, CLI, or agent runtime installs content but doesn't implement MOAT. Maybe it has its own marketplace, maybe it just pulls from GitHub. Either way, the content lands on your machine without MOAT verification.

**What you do:** After installation, run `moat-verify` against the installed content directory:

```
moat-verify ~/.local/share/my-tool/skills/summarizer \
  --registry https://example.com/registry.json
```

This gives you an independent check: does the content on disk match what a MOAT registry attested? If yes, you know it hasn't been tampered with since the registry signed it. If no — either the content was modified, or it's not in that registry.

**The gap:** Your non-MOAT tool doesn't maintain a lockfile, so there's no install-time record of what was verified. Each `moat-verify` run is a standalone check against current registry state. You also won't get automatic revocation alerts — you'd need to re-run `moat-verify` periodically or check the registry manifest yourself.

**This is a valid workflow.** MOAT is designed so that verification doesn't require your install tool to understand the protocol. `moat-verify` is a standalone script — it works with any content directory regardless of how it got there. The conforming client path is better (automatic verification, lockfile, revocation monitoring), but the manual path still gives you the core guarantee: tamper evidence against a registry's attestation.

---

## Edge cases

### "Someone forked my content and a registry indexed the fork."

The fork produces a different content hash if anything changed. If the content is identical, the hash is identical — that's by design. The registry manifest records `source_uri` (pointing to the fork) and can include `derived_from` (pointing to your original). End users see the lineage.

### "A registry indexed my content and I don't want them to."

Your content is public — anyone can read it, and MOAT registries index public content like search engines index public websites. If you want to signal that you don't endorse a particular registry's use of your content, you can post a publisher revocation via the Publisher Action. Publisher revocations are warnings to end users, not hard blocks — only registry revocations are hard blocks.

This is a deliberate design choice. Allowing publishers to hard-block content across registries they don't control would create an abuse vector — a compromised publisher account could revoke content across every registry that indexed it.

### "None of my content is in any registry."

It still works. Content without MOAT attestation is Unsigned tier. MOAT doesn't gate unsigned content — it labels it clearly so end users can make informed decisions. Unsigned content is the entire ecosystem today; MOAT adds trust signals on top, it doesn't remove what already exists.

### "I'm not on GitHub."

The Publisher Action currently requires GitHub Actions for the OIDC signing identity. GitLab CI support is planned. Forgejo/Codeberg OIDC support is not yet shipped. However: the Signed tier doesn't require the publisher to be on any specific platform — the registry does the signing. Only Dual-Attested requires the publisher's CI to support OIDC.

Registry operators currently need GitHub Actions for the Registry Action. This is a practical limitation of the current version, not a protocol constraint — the signing model is platform-agnostic (any CI with OIDC support works), but the reference implementations target GitHub Actions.
