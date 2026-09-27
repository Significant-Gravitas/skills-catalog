# Hard case: "catch up my books", two entities in one upload (fictional)

Request: "I'm six months behind. Here's everything: catch up my books." The
upload holds 14 files: bank exports for Harbour Florists Ltd (Jan to Jun) and
for the owner's side business, Harbour Events (Mar to Jun), plus a Square POS
export covering both shop tills and a personal credit card.

## What the skill does

1. Profiles every file. Two bank exports have different masked account numbers
   (****2201 and ****7780), so they are different accounts. The Square export
   has a `Location` column with two values.
2. Asks one card:
   - Q1. Which entity does account ****7780 belong to? Harbour Florists Ltd ·
     Harbour Events · Personal · Not sure
   - Q2. The Square export has two locations (Quay St, Market Hall). Which
     entity owns each? Both Harbour Florists Ltd · Market Hall is Harbour Events ·
     I will explain · Not sure
   - Q3. The personal credit card: is it used for business spending? No, remove
     it from this work · Yes, some business items · Not sure
   - Q4. Which month should we start from? January (oldest first) · Other: I will type it · Not sure
3. Creates one intake per entity once Q1 to Q2 are answered, under separate
   folders (`harbour-florists/`, `harbour-events/`). Nothing is merged.
4. Treats the personal card as a source of possible owner items only if the owner says
   yes to Q3; its rows are never read into the business intake otherwise.
5. Plans the catch-up oldest period first, one period at a time: January must
   have an approved closing before February's reconciliation starts. Each month
   gets its own intake period block.

## Output (abridged)

- Harbour Florists Ltd, January 2026: Ready: bank ****2201 (Jan). Blocked:
  December 2025 closing balance (no prior approved figure; ask the accountant).
- Harbour Events: Blocked until Q1 is answered.
- Personal card: set aside, not profiled beyond row count, pending Q3.

## Traps avoided

- Summing both bank accounts into one "cash" total.
- Starting with June because it is the most recent.
- Coding personal-card lines as business expenses.
- Carrying one entity's approvers or basis into the other intake.
