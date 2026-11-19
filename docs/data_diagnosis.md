# StreamVault - Data Diagnosis

## 1. Executive summary

The initial candidate list contained **127 records**. After validation and duplicate handling, **117 unique valid TMDb IDs** remained. The acquisition pipeline successfully retrieved matching movie details and credits for **112 titles**, which form the final analytical dataset.

This means:

- 6 excess duplicate occurrences were identified.
- 4 records were invalid.
- 5 valid IDs could not be retrieved.
- 112 unique titles were successfully analysed.

The final analysis therefore covers 112 of the 117 unique valid candidates (95.7%). The five unretrieved titles represent 4.3% of the valid candidate list.

The most important risks are incomplete candidate coverage and the comparability of historical financial figures. These issues matter because a missing title could change a shortlist, while unadjusted historical financial values could distort comparisons between older and newer films.

## 2. Ranked data-quality issues

Risk is ranked according to the potential effect on acquisition decisions, not simply the number of missing fields.

| Rank | Issue | Severity | Detection and evidence | Impact on Kwame's decision |
|---:|---|---|---|---|
| 1 | Five valid candidates not retrieved | High | Compared unique valid input IDs with successfully retrieved details and credits. Five IDs returned 404 responses on both endpoints. | The missing titles could include a strong standalone candidate or a member of a valuable franchise. Their absence could change the shortlist and the apparent strength of a bundle. |
| 2 | Historical financial values are not normalized | High | Inspected release years, budgets, revenues, and calculated revenue-to-budget ratios. Release years range from 1966 to 2019. | Older and newer financial figures are not directly comparable without inflation, currency, and reporting adjustments. This weakens conclusions based on all-years financial comparisons. |
| 3 | Candidate-list duplicates | Medium | Counted repeated valid IDs in the original list and compared raw row count with unique ID count. | Duplicate records could inflate candidate counts or distort analysis if not removed. Six excess occurrences were removed from the unique candidate population. |
| 4 | Invalid candidate identifiers | Medium | Checked missing values, sentinel values, and identifier format. Four records were invalid: a blank value, `-1`, `tt0468569`, and `N/A`. | These records could not be used as valid TMDb IDs. The IMDb-style identifier `tt0468569` requires source correction or an explicit cross-reference before retrieval. |
| 5 | Franchise membership is an incomplete bundle proxy | Medium | Inspected collection IDs and names, then counted sampled titles by collection. | A collection in the retrieved data may not represent every title in the licensable bundle. The ranking identifies promising collections but cannot establish complete bundle value or cost. |
| 6 | Missing descriptive metadata | Low | Profiled nullable fields in details, cast, crew, company, and language records. | Missing profile images, homepages, and some descriptive fields reduce presentation quality and talent-profile completeness, but do not invalidate the core film-level ranking metrics. |
| 7 | Candidate source provenance is unavailable | Medium | Reviewed the supplied candidate-list structure: it contains TMDb IDs, while the brief identifies three contributing sources. No per-record source attribution is available in the supplied list. | We cannot reliably determine which source contributed a duplicate, invalid ID, or unretrieved candidate. This limits source-level accountability and makes correction workflows less direct. |

## 3. Detailed findings

### 3.1 Candidate identifier quality

The original list contained 127 rows. Validation identified four invalid records:

- One blank identifier.
- `-1`, a sentinel value rather than a usable TMDb ID.
- `tt0468569`, which follows an IMDb-style identifier format rather than the expected TMDb numeric ID format.
- `N/A`, a text placeholder rather than a valid identifier.

Six excess duplicate occurrences were also identified. These are repeated rows beyond the first occurrence of each valid ID; they do not represent six additional unique films.

**Decision impact:** Without validation and deduplication, repeated candidates could be counted more than once, while invalid identifiers could cause failed API requests or interrupt acquisition. The pipeline preserves a reconciliation record so these cases are visible rather than silently discarded.

### 3.2 Retrieval coverage and the five missing candidates

After removing invalid records and excess duplicate occurrences, 117 unique valid IDs remained.

The acquisition process retrieved both movie details and credits for 112 titles. Five valid IDs returned 404 responses on both endpoints and were not included in the final analytical datasets.

| Reconciliation stage | Records |
|---|---:|
| Original candidate rows | 127 |
| Less: excess duplicate occurrences | -6 |
| Less: invalid records | -4 |
| Unique valid candidate IDs | 117 |
| Less: valid IDs not retrieved | -5 |
| **Final analysed titles** | **112** |

Coverage:

- 95.7% of unique valid candidates were analysed.
- 4.3% of unique valid candidates were not retrieved.
- 88.2% of the original 127 input rows correspond to successfully analysed titles.

The six duplicate occurrences and four invalid records are not missing unique valid films. The five unretrieved IDs are the actual gap in valid candidate coverage.

**What this costs Kwame:** The five unavailable candidates cannot be ranked against the retrieved titles. If one is a high-performing standalone film or an important franchise entry, the current shortlist may omit an acquisition opportunity or understate the value of a bundle. The available evidence does not identify their titles or commercial value, so this opportunity cost cannot be quantified in dollars.

### 3.3 Financial-data comparability

The film details contain budget and revenue values, and the retrieved records have nonzero values for these fields. However, the dataset does not establish that these values are consistently comparable across release periods.

The release-year range is 1966–2019. Historical figures may reflect different currencies, inflation levels, markets, and box-office reporting practices.

The analysis calculates:

`revenue_budget_ratio = revenue / budget`

This is a descriptive ratio of reported revenue to reported budget. It is **not profit, margin, or return on investment**. It excludes marketing, distribution, licensing costs, and other expenses. It also inherits any inconsistencies in the underlying financial figures.

The period comparison shows:

| Median metric | Pre-2000 | 2000 onward |
|---|---:|---:|
| Reported revenue | $321.37M | $738.60M |
| Reported budget | $30M | $150M |
| Revenue-to-budget ratio | 9.54× | 4.92× |
| Vote average | 7.97 | 7.49 |
| Vote count | 15,210 | 16,955 |
| Popularity | 14.88 | 16.80 |

These are medians, selected to reduce the influence of highly skewed financial and audience metrics. They do not make historical financial values directly comparable.

**Decision impact:** Finance should not interpret the higher pre-2000 median ratio as proof that older titles are more profitable or better licensing investments. The 2000-onward analysis is an important sensitivity check, particularly given Finance's stated concerns about older films.

### 3.4 Franchise classification limitations

TMDb collection membership is used as a proxy for franchise grouping.

The 112 retrieved films classify as:

| Classification | Film records |
|---|---:|
| Multi-film sampled collections | 87 |
| Single-film sampled collections | 9 |
| No collection association | 16 |
| **Total** | **112** |

There are 32 unique collection IDs:

- 23 collections contain at least two sampled titles.
- 9 collections contain only one sampled title in this candidate dataset.

A single-film collection is not automatically a standalone title. Likewise, a multi-film sampled collection does not prove that every film in the commercial bundle is present in the candidate list.

**Decision impact:** The ranking can prioritize collections for diligence, but cannot establish the complete contents, price, or economics of an all-or-none franchise deal. Bundle completeness must be verified against studio licensing schedules.

### 3.5 Missing descriptive metadata

The metadata profile identified the following gaps:

| Field | Missing or incomplete records | Significance |
|---|---:|---|
| Film homepage | 15 missing | Limits direct reference links and presentation completeness. |
| Company logo path | 55 missing | Affects visual presentation, not financial ranking. |
| Company origin country | 5 blank | Limits geographic company profiling. |
| Spoken-language names | 3 blank | Language codes remain available in raw data. |
| Cast profile path | 2,190 null | Limits cast-image availability. |
| Crew profile path | 18,811 null | Limits crew-image availability. |
| Crew known-for department | 1 null | Minor descriptive metadata gap. |

These are missing descriptive fields, not missing film records. They should not be treated as evidence that the corresponding titles, companies, cast, or crew do not exist.

**Decision impact:** These gaps do not directly invalidate the current film-level ranking metrics. They do limit the completeness of talent presentation and any future analysis that depends on profile imagery or descriptive metadata.

### 3.6 Source provenance

The candidate list was assembled over approximately four years from three sources: an evaluation tracker, an inherited spreadsheet, and a studio licensing submission. The supplied list contains identifiers but no source-level provenance.

As a result, the analysis cannot attribute an invalid identifier, duplicate, or unretrieved record to a particular source.

**Decision impact:** Kwame and Adjoa cannot use the current reconciliation to identify which upstream source requires correction. For future submissions, each candidate should retain a source name, source record reference, and ingestion timestamp.

## 4. Structural validation and analytical integrity

The pipeline transforms the retrieved nested API responses into separate analytical datasets:

| Dataset | Rows |
|---|---:|
| Films | 112 |
| Cast | 7,827 |
| Crew | 24,932 |
| Film genres | 320 |
| Film companies | 307 |

The transformation keeps film-level data separate from one-to-many cast, crew, genre, and company relationships. This avoids multiplying film-level financial values when joining child records.

Validation checks confirmed:

- The expected analytical tables and key columns exist.
- Film primary keys are present and unique.
- Child-table keys are present and unique within their defined key structure.
- Child movie IDs reference existing film records.
- Details and credits contain matching movie ID sets before transformation.
- The transformed datasets passed validation with no missing or duplicate keys.

The test suite reported 29 passing tests.

These checks support the structural integrity of the 112-title analytical dataset. They do not establish the factual accuracy of every value returned by the external API.

## 5. What the diagnosis means for the acquisition recommendation

The diagnosis does not invalidate the entire analysis. It defines the conditions under which the rankings can be used.

1. The 112 retrieved titles provide a substantial basis for preliminary comparison, but the five unretrieved candidates must remain visible as unresolved opportunities.
2. The top-three franchise and standalone rankings remain consistent between the all-years and 2000-onward comparisons. This supports the stability of those shortlists within the retrieved candidate population.
3. Historical financial figures should not be used as direct evidence of current licensing profitability.
4. Franchise rankings identify collections for commercial diligence, not verified all-or-none bundle economics.
5. The current dataset does not support a defensible $14M allocation or bid without licensing prices, rights, territories, contract windows, and expected streaming outcomes.

The appropriate recommendation is therefore to use the rankings to prioritize diligence and negotiation, not to authorize a purchase price.

## 6. Remediation priorities

| Priority | Action | Expected benefit |
|---|---|---|
| 1 | Investigate and resolve the five valid IDs that returned 404 responses. | Restores candidate coverage and tests whether the shortlist changes. |
| 2 | Obtain currency, inflation, and financial-source context for historical values. | Makes period comparisons more defensible to Finance. |
| 3 | Obtain complete studio bundle schedules and title-level rights information. | Confirms whether ranked collections match actual licensable bundles. |
| 4 | Preserve source provenance for every future candidate. | Makes duplicate resolution, corrections, and source accountability traceable. |
| 5 | Enrich missing descriptive metadata where needed. | Improves talent research and dashboard presentation without blocking the current analysis. |

## 7. Conclusion

The final analytical dataset contains 112 successfully retrieved titles from 117 unique valid candidates. The reconciliation accounts for all 127 input rows: six excess duplicate occurrences, four invalid records, five valid but unretrieved IDs, and 112 analysed titles.

The most consequential limitations are the five unavailable candidates, unnormalized historical financial figures, and the inability to verify complete franchise bundle contents or licensing terms. The rankings are useful for prioritizing commercial diligence, but they are not a substitute for title-level rights verification and financial underwriting.