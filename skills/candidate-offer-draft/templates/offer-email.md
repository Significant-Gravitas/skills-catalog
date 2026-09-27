# Offer email (template)

Short and warm. The letter carries the terms. The email repeats at most the
title, base pay and start date, and only if the owner wants them in it.
Every figure and date must match `terms.json` (`check_terms.py --email`).
Dates are written as "6 January 2027", never 06/01/2027.

---

**Subject:** Your offer for <title> at <company>

Hi <chosen name>,

I'm delighted to share that we'd like to offer you the role of <title> at
<company>. The attached letter sets out the full terms<, including a base
salary of <currency symbol><base pay> a <pay period> and a start date of
<start date>>, and the letter is what counts if anything here differs.

<Contingency sentence only if the owner wants one, in the template's words:
"As the letter explains, the offer is conditional on <template wording>.">

We'd be grateful for your answer by <response-by date, or [OWNER TO CONFIRM]>.
I'm happy to talk through any questions before then.

<sender>

---
Status: DRAFT, not sent. Open terms: <list or "none">.

Never in the email: negotiation language ("we could stretch to..."),
promises beyond the letter, tax, equity or benefits explanations beyond the
approved text, references to the candidate's current or past pay, or legal wording.
