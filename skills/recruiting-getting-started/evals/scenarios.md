# Eval scenarios

"Pass" is what a reviewer checks. Each runs `scripts/policy_flags.py --locations "<location>" --ai-screening yes --background-check no --talent-pool no --video-interviews no --federal-contractor no`.

| # | Location | Pass |
| --- | --- | --- |
| 1 | "Sydney, New South Wales" | No UK flags; a NOTE that the location is not recognised, asking the people lead which rules apply |
| 2 | "Birmingham, AL" and "Manchester, NH" | US flags only; a NOTE that the city name also exists in the UK and the country should be confirmed |
| 3 | "Dublin, OH" and "Paris, TX" | US flags only; no EU AI Act or GDPR Art. 22 flag; a NOTE to confirm the country |
| 4 | "Brooklyn Park, MN" | US flags only; no New York City flag |
| 5 | "Tbilisi, Georgia" | No US flags; a NOTE that the location is not recognised |
| 6 | "Georgia" | US flags plus a NOTE asking whether it is the US state or the country |
| 7 | "London", "Dublin", "Brooklyn, NY", "New York, NY", "Remote (UK)" | UK, EU, NYC + US, NYC + US and UK as before |
| 8 | "Chicago, London" | Two places: IL + US flags and UK flags |
| 9 | "Chicago IL, London UK" | IL + US flags (including the Illinois AI notice) and UK flags |
| 10 | "Boston, MA and London" | US flags and UK flags; no confirm-country NOTE |
| 11 | "Austin, TX / Dublin" | US flags and EU flags; no confirm-country NOTE |
| 12 | "Portugal, Spain (EU)" | EU flags |
| 13 | "Chicago, Germany" | EU flags plus a NOTE that the Chicago match was not counted and the place should be confirmed |
