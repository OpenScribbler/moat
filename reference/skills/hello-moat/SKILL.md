---
name: hello-moat
display_name: Hello MOAT
description: A minimal test skill that verifies the MOAT registry pipeline is working end-to-end.
version: 0.1.0
---

# Hello MOAT

This skill exists to test the MOAT registry action. It verifies that:

- Content discovery finds items in the `skills/` directory
- Content hashing produces a stable hash
- Registry signing produces a valid Rekor entry
- The manifest is committed and accessible

It has no real functionality. If you're looking at the MOAT spec and wondering what this is, see [moat-spec.md](../../moat-spec.md).
