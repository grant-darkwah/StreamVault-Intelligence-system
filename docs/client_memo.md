# Memo to Kwame

**From:** Grant Sarfo Darkwah
**Date:** 19 November 2026
**Subject:** StreamVault - $14M Content Licensing Decision

## What I found

The candidate list contains 127 records. After ID validation and duplicate handling, 117 unique valid IDs remained; details and credits were successfully retrieved for 112 titles.

The strongest franchise targets are:

1. The Avengers Collection
2. The Lord of the Rings Collection
3. The Dark Knight Collection

These rank in the same top-three order in both the all-years and 2000-onward analyses.

The strongest standalone titles in the all-years ranking are:

1. Interstellar
2. Inception
3. Spirited Away
4. Forrest Gump
5. The Shawshank Redemption

When restricted to titles released from 2000 onward, the top three remain unchanged. WALL·E and The Prestige replace Forrest Gump and The Shawshank Redemption.

The franchise results support prioritizing bundle diligence. The standalone results provide alternatives if individual licensing terms are more attractive than all-or-none bundle terms.

## What I built

| What you asked for | Status | Evidence |
|---|---|---|
| Diagnose and rank data quality issues | Complete | `docs/findings.md`; acquisition summary and candidate reconciliation |
| Reconcile candidate IDs against source records | Complete | 127 input rows, 117 unique valid IDs, 4 invalid records, 6 excess duplicate occurrences |
| Retrieve and transform film, cast, crew, genre, and company data | Complete | 112 films, 7,827 cast records, 24,932 crew records, 320 genre records, 307 company records |
| Validate analytical datasets | Complete | Pipeline validation passed; no missing or duplicate primary keys |
| Rank franchise bundles and standalone titles | Complete | Four ranking CSVs in `out/` |
| Compare all-years and 2000-onward results | Complete | Rankings exported separately for both periods |
| Identify director and lead-cast signals | Complete | Extracted from the credits datasets for the ranked standalone shortlists |
| Produce a reproducible pipeline | Complete | `run_pipeline.py`, modular pipeline code, cached API responses, Parquet datasets, and ranking exports |
| Test the implementation | Complete | 29 tests passed |
| Assess licensing economics | Partial | Candidate performance indicators available; commercial terms and streaming outcomes unavailable |

## What I recommend

Prioritize commercial diligence on **The Avengers Collection**, followed by **The Lord of the Rings Collection** and **The Dark Knight Collection**. Their top-three positions remain stable across both analysis periods.

The Avengers Collection is the strongest provisional target. It ranks first in both periods, with four sampled titles and a median reported revenue of approximately $1.79B. This is a reason to investigate the bundle first, not a basis for accepting an asking price.

Retain the five all-years standalone titles as negotiating alternatives. If Finance prefers a shortlist that excludes pre-2000 titles, use Interstellar, Inception, Spirited Away, WALL·E, and The Prestige.

The credits also show a recurring director signal: Christopher Nolan directed Interstellar, Inception, and The Prestige. Michael Caine appears among the first three cast credits in Interstellar and The Prestige. These are descriptive patterns, not proof of independent commercial draw.

I recommend approving diligence on the three franchise bundles while retaining standalone options. Do not commit the full $14M until title-level rights and expected licensing economics have been assessed.

## What I could not stand behind

- **Licensing price and ROI:** No asking prices, minimum guarantees, contract terms, or title-level streaming outcomes were supplied. I cannot calculate a defensible bid, payback period, or return on the $14M.
- **Rights and availability:** Territory, exclusivity, duration, platform restrictions, and current rights availability remain unverified.
- **Completeness of franchise bundles:** TMDb collection membership is used as a franchise proxy. The sampled titles do not establish that every title in a licensable bundle is represented.
- **Historical financial comparability:** Budget and revenue figures are reported values. They have not been adjusted for inflation, currency differences, or changes in box-office reporting. Revenue-to-budget ratios are not profit or ROI.
- **Talent as a demand predictor:** Director and cast credits identify recurring names but do not establish that those people caused audience engagement or revenue.
- **Missing and invalid source records:** Four candidate records were invalid, six excess duplicate occurrences were identified, and five valid IDs were not retrieved. The analysis is based on the 112 titles with both details and credits.
- **Older-title recommendation:** The all-years and 2000-onward comparisons preserve the top three standalone titles, but positions four and five change. Finance should review older-title financial figures before acquisition decisions.