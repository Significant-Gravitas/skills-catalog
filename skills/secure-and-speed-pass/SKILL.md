---
name: secure-and-speed-pass
description: Use for a dedicated security-basics and performance audit only, when no full correctness or test-coverage diff review is needed. For a full PR/diff review, use Review code instead.
version: '1'
---

# Secure and speed pass

Inputs: the diff or service, its data sensitivity, and any existing profiling or monitoring output. Output: ranked findings with severity, evidence, and fixes — or a clean bill with what was actually checked. Fallbacks: without production access, review code and config only and label runtime claims UNKNOWN; never invent timings, scores, or scan results.

1. Security basics, in order: auth and authorization on every path, input validation, secrets out of code and logs, dependency risk in the diff, and fail-closed behavior on sensitive paths.
2. Flag risks plainly with FACT, INFERENCE, or UNKNOWN. A plausible risk is reported, not silently shipped.
3. Performance: look for N+1 queries, unbounded lists, missing indexes, synchronous work that should be a job, and payload bloat. Measure before optimizing; quote the source and time of every number.
4. Fix blockers, file the rest as named follow-ups with owners. Never weaken a security check for speed.
5. Re-run tests and checks after fixes; show real output.
6. Deliver the four-part contract. Partner- or customer-facing disclosure waits for the owner's yes.

<!-- Reuse: security/perf checklist methods from upstream packs, rewritten in own words; no numbers without a measured source. -->
