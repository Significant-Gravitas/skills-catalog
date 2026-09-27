# Exception BX-7: supplier bank details changed before a payment run

Entity: Northgate Joinery Ltd. Account: business current, ending 4411. Period: May 2026.
Class: bank-detail-change; suspected, not confirmed, payment redirection.

**Facts (from records):** Bill 8812 from Kestrel Timber, 4,960.00 GBP, due 6 June
(bills export, 31 May, row 2). Kestrel's email of 28 May gives new bank details
ending 0937. The previous three payments went to the account ending 2210 (bank
statements Feb to Apr, rows 1-3), which is also the account verified by phone on
14 Nov 2025 (vendor master).

**Mismatch:** the payee account on bill 8812 differs from every earlier payment
and from the verified vendor record. No call-back to a known Kestrel number is on file.

**Amount and affected totals:** 4,960.00 GBP, the whole of bill 8812. No
materiality claimed (no threshold supplied).

**Done so far:** checked the vendor master and the last three statements. That did
not settle it because nothing independent confirms the change.

**Deadline:** payment run 5 June (payment calendar).

**Decision requested from Alex (finance owner):** confirm the change by calling
Kestrel on the number already on file (vendor master, not the email), or hold
bill 8812 out of the 5 June run.

**Safe interim state:** bill 8812 left unapproved in the draft run here. No one has
contacted Kestrel from here. Recommend Alex also tells whoever releases payments.
