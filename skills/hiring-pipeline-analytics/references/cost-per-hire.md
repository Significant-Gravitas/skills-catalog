# Cost per hire

## Formula

Cost per hire = (total internal recruiting costs + total external
recruiting costs) / total hires in the same period. This is the ANSI/SHRM
06001.2012 standard as summarised by Integral Recruiting Design [38][39].
The standard also defines a **"comparable" cost per hire** for benchmarking
across organisations [38]. Per [38], the comparable variant excludes
signing bonuses, relocation and immigration costs. The standard text itself
is paywalled [39], so before calling a number "comparable" the owner
confirms with finance which lines they include; otherwise report the
standard variant and say so.

## Cost lines

- **External** (examples): job boards and ads, agency fees,
  background-check fees, recruiting software, candidate travel,
  relocation paid to hires.
- **Internal** (examples): recruiting team pay and overhead, referral
  programme bonuses (listed under internal costs in [38]), hiring-manager
  and panel time if finance costs it, internal events.

Apart from referral programmes [38], the examples are practitioner
judgement (unsourced) to help the owner find their lines; the owner
decides what is in. The internal/external split does not change the total.

## Rules for the skill

1. Cost per hire only when the owner supplies cost lines
   (templates/cost-lines.csv): line, type (internal|external), amount,
   currency, and optional estimate (yes|no). Otherwise it is UNKNOWN -
   never estimated.
2. Same period for costs and hires; one currency (the script refuses mixed
   currencies).
3. Show the formula, the variant and every line with the number.
4. A line the owner marks `estimate=yes` stays labelled as one in the
   report ("[ESTIMATE]" on the line), and the cost per hire built on it is
   INFERENCE, not FACT, with the estimated lines named in its basis. Ask
   the owner which lines are estimates when the file does not say.

## Hiring-manager satisfaction (optional line)

Only from survey results the owner supplies (templates/hm-survey.csv: role,
score, scale_max). Reported as percent of scale maximum with n. No survey,
no line. Hiring-manager satisfaction appears as a recruiter KPI in some
2026 postings [5].
