---
name: build-an-assembly
description: 'Use when several parts must fit, seat, or move together: enclosures with lids, hinged mechanisms, and multi-part products composed from part models with explicit placements and joints.'
version: '1'
---

# Build an assembly

Inputs: the part models (or briefs for them), mating interfaces, and required motion if any. Output: an assembly model returning a labelled compound, seating and interference checks, and posed snapshots for each mechanism state. Fallbacks: a missing mating dimension stops the affected joint, not the whole assembly — build the rest and list the blocked interface as UNKNOWN.

1. Model or import each part first; the assembly calls part models and composes their shapes. Vendor files are converted once to xbf and read back, keeping the vendor origin until measured offsets are written in source.
2. Place parts with explicit placements that share geometry where they seat. Mirroring creates new geometry — never pretend a mirrored placement is the same part.
3. Where motion is required, author joints in the assembly body (rigid, revolute, linear, cylindrical, ball) so the joints are the mechanism; named poses capture open, closed, and service states.
4. Verify fit numerically: seating pairs must touch (distance 0), and no pair may interfere except named press-fits. Report every pair, not a sample.
5. Snapshot each named pose and any view where a part hides the interface under discussion. For large assemblies, isolate the touched parts instead of rendering the whole.
6. Keep showcase motion (explode, reveal) separate from mechanism motion: an explode is presentation, never a substitute for joint truth.
7. Close with the interface table: each mate, its measured clearance, and which side owns the datum. Interface changes need the owner's yes.

<!-- Reuse: positioning, kinematics, and animation guidance adapted from earthtojake/text-to-cad@4d42cb0 skills/cad/references/positioning.md, kinematics.md, animation.md (MIT) — joints-as-mechanism and pose checks rewritten for this package. -->
