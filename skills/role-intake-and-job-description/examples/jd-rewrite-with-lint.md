# Hard case: rewriting a legacy Denver posting

Fictional company and people, for shape only. The files used here are in
`examples/jd-rewrite/`: `old-posting.md` (input), `requirements.csv` and
`jd-v1.md` (output). Every script output below is real output from those files.

## The ask

> Sam Ortiz (Head of Sales): "Can you rewrite this posting? We've had it up for
> two months and nobody good applies." (uploads `cs-rockstar.docx`)

The hiring plan exists (`~/workspace/hiring/cs-manager/hiring-plan.md`):
Sam is hiring manager and final decision-maker; hiring jurisdiction Colorado;
pay range OPEN; accommodation route and candidate AI-use policy OPEN.

## Step 0: bring the posting in

```
read_workspace_file(file_id="<upload>", save_to_path="/home/user/in/old-posting.docx")
$ python3 ~/skills/role-intake-and-job-description/scripts/extract_text.py /home/user/in/old-posting.docx > /home/user/old.md
```

The extracted text is `examples/jd-rewrite/old-posting.md`.

## Step 1: lint the old posting first (so Sam sees why it underperforms)

```
$ python3 ~/skills/role-intake-and-job-description/scripts/jd_lint.py /home/user/old.md
L1:20 "Rockstar" [label/flag] -> describe the work and the result expected (unsourced practitioner judgement)
L3:11 "young" [age/flag] -> remove; describe the work instead ([45])
L3:18 "hungry" [label/flag] -> describe the target or result expected (unsourced practitioner judgement)
L3:25 "self-starter" [label/flag] -> describe what the person decides without being asked (unsourced practitioner judgement)
L3:51 "dominate" [masculine-coded/suggest] -> excellence ([31])
L3:120 "competitive" [masculine-coded/suggest] -> keep 'competitive pay' if pay is stated; otherwise 'high standard' ([31])
L3:133 "aggressive" [masculine-coded/suggest] -> proactive ([31])
L6:36 "ninja" [label/flag] -> describe the work and the result expected (unsourced practitioner judgement)
L7:3 "Lead" [masculine-coded/suggest] -> keep in a job title or when the role leads people; otherwise 'guide' or 'own' ([31])
L11:3 "Bachelor's" [requirement-check/check] -> keep only if a job-related reason is recorded; otherwise 'or equivalent experience', or remove ([111][36])
L11:14 "degree" [requirement-check/check] -> keep only if a job-related reason is recorded; otherwise 'or equivalent experience', or remove ([111][36])
L12:3 "5+ years of experience" [requirement-check/check] -> keep only if the four-way sort says the years are what the work needs; otherwise name the outcome behind them ([36])
L13:3 "Recent graduates" [age/flag] -> early-career, or name the skill needed ([45])
L13:50 "digital native" [age-proxy/flag] -> name the tools or skills needed ([34])
L14:3 "Must live within" [location-proxy/flag] -> state work terms instead: onsite days, hours, travel ([72])
L15:3 "Must be able to lift" [disability/check] -> keep only if essential; add 'with or without reasonable accommodation' ([35][46])
L16:9 "culture fit" [proxy/flag] -> name the job-related behaviour (for example 'writes decisions down for the team') ([79])
L16:30 "work hard play hard" [label/flag] -> describe hours and pace plainly (unsourced practitioner judgement)
L19:1 "Competitive" [masculine-coded/suggest] -> keep 'competitive pay' if pay is stated; otherwise 'high standard' ([31])
L19:41 "salary history" [pay/flag] -> remove; ask for pay expectations only ([56][75])
L21:1 "Open until filled" [posting-field/check] -> state how and when to apply, with a date (Colorado postings may need it) ([57])
Summary: age 2, age-proxy 1, disability 1, label 5, location-proxy 1, masculine-coded 5, pay 1, posting-field 1, proxy 1, requirement-check 3
Gender-coded balance: masculine 5, feminine 0 (masculine-leaning) [31]
```

## Step 2: the requirement sort, with Sam

One `ask_question` card with four questions: what fails without the degree,
what the 5 years stand for, whether the role lifts anything, and what "culture
fit" means in behaviour. Sam's answers: no reason for the degree; the years
meant "has carried a renewal book"; no lifting; "fit" meant "writes up every
escalation".

`requirements.csv` (in `examples/jd-rewrite/`) records R1-R4 kept and R5-R9
removed, each with its reason. "Digital native", "young" and "recent
graduates" are never kept, whatever the reason given [45][34].

```
$ python3 ~/skills/role-intake-and-job-description/scripts/req_check.py ~/workspace/hiring/cs-manager/requirements.csv --jd ~/workspace/hiring/cs-manager/jd-v1.md
Counts: must-show 2, test-in-process 1, learn-after-hire 1, removed 5
OK
```

## Step 3: the rewrite and its checks

The new draft is `examples/jd-rewrite/jd-v1.md`. Location is written as work
terms ("Denver office on Tuesday and Thursday") in place of the commute radius.

```
$ python3 ~/skills/role-intake-and-job-description/scripts/jd_lint.py ~/workspace/hiring/cs-manager/jd-v1.md
Summary: no hits
Gender-coded balance: masculine 0, feminine 0 (balanced) [31]
```

## Step 4: what changed (abridged)

```
$ python3 ~/skills/role-intake-and-job-description/scripts/diff_postings.py /home/user/old.md ~/workspace/hiring/cs-manager/jd-v1.md
Sections removed: Customer Success Rockstar (Denver), Requirements, Pay
Sections added: Customer Success Manager (Denver, onsite Tuesday and Thursday), What we need to see, Useful, and we will help you build it, How you will work, Our process, Pay and benefits

[What you'll do]
- Crush renewals and upsell like a ninja.
~ Lead onboarding calls for new accounts.
    -> Run onboarding calls for new accounts.
- Handle escalations.

[Requirements]
- Bachelor's degree in business or a related field.
- 5+ years of experience in customer success.
- Recent graduates welcome to apply if you are a digital native.
- Must live within 15 miles of our Denver office.
- Must be able to lift 25 lbs.
- Great culture fit with our work hard play hard team.

[Pay]
- Competitive salary.
- Please include your salary history with your application.
- Open until filled.
...
32 change(s); 0 sentence(s) unchanged
```

## Step 5: posting fields for Colorado

From `references/posting-law-fields.md`, Colorado lists pay as a closed range,
a general benefits description, and how and when to apply [57]. All three stay
`[OWNER TO CONFIRM]`; no figure is proposed. Three lines go on the approval
checklist for the people lead, each "may be required for Colorado; confirm".
The salary-history request is removed and never replaced [56][75].

## Reply to Sam (shape)

> Rewrite ready: [jd-v1.md] [jd-cs-manager-v1.docx]. Three things likely kept
> good people away: requirements nobody needed (degree, 5+ years, lifting,
> living within 15 miles), wording that reads as age-limited ("young",
> "recent graduates", "digital native"), and a request for salary history.
> I've listed every change with its reason. Nothing is posted.
>
> Before this goes live: pay range, benefits and an apply-by date may be
> required for a Colorado posting, so the people lead should confirm. Your
> accommodation contact and your policy on candidates using AI are still open.

## Approval checklist

- [ ] Outcomes and duties: Sam Ortiz
- [ ] Removed requirements R5-R9: Sam Ortiz
- [ ] Language flags (21 in the old posting; 0 in the draft): Sam Ortiz
- [ ] Pay range (may be required for Colorado; confirm): pay approver, people lead
- [ ] Benefits summary (may be required for Colorado; confirm): people lead
- [ ] How and when to apply, with a date (may be required for Colorado; confirm): Sam Ortiz
- [ ] Accommodation line and candidate AI-use line: people lead
- [ ] Every must-show requirement maps to a rubric criterion: next, hiring-rubric-design

## Why this is the hard case

- The owner asked for a rewrite, not a review. The skill still shows every
  change and the reason, so nothing is silently dropped.
- "5+ years" was not simply deleted: the sort found the outcome behind it (R1).
- Pay is the owner's lever to fix the response rate, and the skill still does
  not suggest a number.
