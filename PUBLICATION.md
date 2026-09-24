# Publishing safely

## Hosted marketplace

Only entries with `distribution_status: approved` may appear in the hosted
marketplace. The platform seed must filter on this field before it writes any
listing.

Changing a skill to a review status does not remove an existing live listing.
Withdraw that listing from every environment as a separate release step.

## Public GitHub repository

Do not change this repository from private to public. Its Git history contains
skills that have not been cleared.

Build a clean tree instead:

```sh
python tools/export_public.py /path/to/empty/output
cd /path/to/empty/output
python tools/check.py
```

Create a new repository from that output with new Git history. Check that it
contains only approved skill folders before publishing it.

## Approval

A reviewer may set `distribution_status: approved` only after recording:

- the original source;
- a full pinned commit;
- a source URL pinned to that commit;
- the license and copyright notice;
- proof that the source can grant all rights needed for redistribution;
- copyright and trademark review for named books, courses, standards, and
  commercial methods.

Every approved package must contain `LICENSE` and `NOTICE`.
