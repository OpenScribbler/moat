# 0006. Materialization-boundary anchor — "Before any byte written outside the package manager's content cache" vs "Before fetch" vs "Before unpack"

Date: 2026-05-09
Status: Accepted
Feature: npm-distribution-spec

## Context

Streaming installers — npm's `pacote` is the canonical example — interleave fetch and unpack: bytes flow in via HTTPS, are decompressed on the fly, and may be tee'd into both a content-addressable cache and an extraction directory. A "before fetch" rule is too strict (it forbids ever caching a revoked tarball, even for forensic analysis after the fact, and it fights pacote's streaming architecture). A "before unpack" rule is too loose (it doesn't say where the cache lives — bytes might already be on disk inside the install target if the cache is the install target itself). The chosen anchor names the moment that matters: bytes inside the package manager's content cache are still under the package manager's control and can be discarded (pacote can abort mid-stream and delete the partial cache entry); bytes outside the cache (in the install target, in node_modules, in a workspace) are materialized — they may be loaded by an AI Agent Runtime, copied by a downstream tool, or surface elsewhere. The cache boundary is the protocol-meaningful boundary because it is the last point at which a Conforming Client can refuse without already having published bytes. This anchor lets a streaming installer comply by aborting mid-stream and discarding the partial cache entry, and lets a non-streaming installer comply by checking before fetch — both implementation choices are conformant.

## Decision

Chose **"Before any byte of the tarball is written outside the package manager's content cache" (B-1)** over **"Before fetch" (block at HTTP request time — refuse to download); "Before unpack" (allow fetch into local cache, refuse unpack to install target)**.

## Consequences

The pre-materialization MUST in `specs/npm-distribution.md:31` is rephrased to anchor at the cache boundary, naming the three sub-operations (resolve, fetch, unpack) and stating that whichever operation the Conforming Client chooses to refuse at, no extracted bytes may land outside the cache. A Conforming Client that fetches a revoked tarball into its content cache and then discards it on unpack-refusal is conformant; a Conforming Client that writes a revoked tarball to `node_modules/` and then deletes it is non-conformant (bytes briefly existed outside the cache, which means a parallel reader could have observed them). This phrasing also future-proofs against installers that don't have a cache-then-extract architecture (Yarn Plug'n'Play, pnpm content-addressable store) — each can map the cache-boundary concept onto its own architecture without rewording the MUST.
