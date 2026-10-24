# 0016. Signer subject is the Fulcio certificate SAN, not the OIDC `sub` claim

Date: 2026-10-24
Status: Accepted
Feature: signer-subject

## Context

`moat-spec.md` defined the keyless `subject` field of `signing_profile` and `registry_signing_profile` as "the OIDC subject claim as produced by the CI provider's token", and every example used the GitHub token's `sub` form, `repo:owner/repo:ref:refs/heads/main`. The known-provider table gave the same `sub` form for GitHub Actions and the `project_path:…:ref_type:branch:ref:…` form for GitLab CI. The sub-specs disagreed: `specs/github/publisher-action.md`, `specs/github/registry-action.md`, and `specs/moat-verify.md` all compared against a URL of the form `https://github.com/{owner}/{repo}/.github/workflows/{file}@refs/heads/{branch}`, as the reference workflows do.

The sub-specs are right. For GitHub Actions and GitLab CI, Fulcio does not copy the token's `sub` claim into the signing certificate; some other issuer types do derive the SAN from `sub`. For each issuer, Fulcio's issuer configuration ([`config/identity/config.yaml`](https://github.com/sigstore/fulcio/blob/main/config/identity/config.yaml)) and its OIDC documentation ([`docs/oidc.md`](https://github.com/sigstore/fulcio/blob/main/docs/oidc.md)) name the claim that becomes the certificate's Subject Alternative Name (SAN) URI. For GitHub Actions it is `https://github.com/` followed by `job_workflow_ref`; for GitLab CI it is `https://` followed by `ci_config_ref_uri`. A client that compared a certificate against a `subject` in the `sub` form could never match a real certificate, so the core text could not be implemented as written.

## Decision

Chose **define the keyless `subject` value as the Fulcio certificate's SAN URI (the signer subject), keep the field name `subject`, and give the SAN form per provider in the known-provider table with Fulcio's configuration as its source** over **keep the `sub` form and require verifiers to reconstruct it from certificate extensions; add a separate `san` field beside `subject`; rename `subject` to `san`**.

## Consequences

Every `subject` example in `moat-spec.md` and its website mirror now uses the SAN form, the known-provider table gives the GitHub (`job_workflow_ref`) and GitLab (`ci_config_ref_uri`) forms and the claim each comes from, and a provider joins the table only when its SAN form is verified against Fulcio's issuer configuration. The spec states two consequences of Fulcio's mapping that implementers trip on: a job that runs in a reusable workflow gets the reusable workflow's SAN, not the caller's, and the GitLab form keeps its double slash before the CI config path.

Reconstructing `sub` from certificate extensions was rejected because the reconstruction would be provider-specific code with no Fulcio-defined contract behind it. A separate `san` field would leave two fields that must agree, and renaming the field would change the manifest schema for no gain in meaning, since cosign and Sigstore tooling already treat the SAN as the certificate's identity.

The field's type is unchanged (a string), so no `schema_version` changes. No conforming deployment depended on the old form, because no real certificate could match it. The rename-attack binding (numeric repository and owner IDs for the GitHub issuer) is unchanged and still applies alongside the SAN match. The npm sub-spec's `publisherSigning.subject` already used the SAN form and needs no change.
