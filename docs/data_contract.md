# Data contract: StreamVault TMDb acquisition and analytical data

**Parties:** StreamVault analysis team (receives and processes data) and The Movie Database (TMDb) API (source provider).
**Version:** 0.1 - Initial draft
**Status:** Draft; transformation rules and analytical output schemas require validation.
**Changes:** Changes to source handling, schema, validation rules, or output grain must be documented, tested, and recorded in an ADR before implementation.

## Delivery

| Rule | If it's broken | Where |
|---|---|---|
| Candidate IDs are read from `data/raw/id_list.csv`. | The ingestion step stops if the input file cannot be read. | `pipeline/ingest.py` |
| The input contains a `tmdb_id` column. | The ingestion step stops if the required column is absent. | `pipeline/ingest.py` |
| Original candidate rows and raw ID values are preserved for reconciliation. | The run must not silently discard invalid or duplicate source records. | `pipeline/ingest.py`, `pipeline/extract.py` |
| Only unique, valid, positive numeric TMDb IDs are submitted for extraction. | Invalid IDs are retained in the reconciliation output and excluded from API requests. | `pipeline/ingest.py`, `pipeline/extract.py` |
| Movie details and credits are acquired separately for each candidate ID. | Each endpoint outcome is recorded independently; one endpoint's failure must not be represented as the other's result. | `pipeline/extract.py` |
| Successful API responses are cached as raw responses. | Failed responses are reported; they must not be treated as successful cached data. | `pipeline/extract.py` |
| Cached successful responses are reused on subsequent runs. | A missing cache entry triggers an API request. | `pipeline/extract.py` |
| API credentials are loaded from the project's environment configuration. | The run stops if the API key is unavailable. | `pipeline/config.py` |
| API requests use configured connection and response timeouts and retry handling. | Request failures are recorded with their outcome; the pipeline must not silently treat them as successful acquisitions. | `pipeline/extract.py` |

## Source observations

The initial input contained 127 candidate rows.

| Observation | Current result | Handling |
|---|---:|---|
| Unique valid positive numeric IDs | 117 | Extract once per unique ID |
| Missing IDs | 1 | Preserve and report |
| Non-numeric IDs | 2 | Preserve and report |
| Non-positive IDs | 1 | Preserve and report |
| Rows belonging to duplicate groups | 12 | Preserve original rows; extract unique IDs once |
| Unique IDs returning 404 | 5 | Record as `not_found`; do not invent replacements |

The five unresolved numeric IDs returned 404 from both the details and credits endpoints. These are acquisition outcomes, not proof that the original source records should be deleted.

The acquisition run processed 117 unique valid IDs. For each endpoint, the run recorded 111 new successful responses, one cache hit, and five not_found outcomes.

## Acquired data

| Dataset | Grain | Key | Rule |
|---|---|---|---|
| Candidate input | One row per original source record | `source_row` | Preserve every original row, including duplicates and invalid IDs. |
| Movie details | One record per successfully acquired TMDb movie | `id` | Retain the raw TMDb response. |
| Movie credits | One record per successfully acquired movie | `id` | Retain cast and crew as separate collections within the raw response. |
| Acquisition reconciliation | One row per original candidate record | `source_row` | Link source records to validation and endpoint outcomes. |

## Analytical datasets

The following are the proposed normalized outputs. Their schemas will be finalized during transformation design and verified against the acquired data.

| Dataset | Grain | Key | Purpose |
|---|---|---|---|
| `films` | One row per movie | `movie_id` | Film-level attributes used for analysis and licensing comparisons. |
| `cast` | One row per cast credit per movie | Provisional: `movie_id` + `credit_id` | Actor and character-level analysis. |
| `crew` | One row per crew credit per movie | Provisional: `movie_id` + `credit_id` | Director and other crew/talent analysis. |
| `film_genres` | One row per movie-genre association | Provisional: `movie_id` + `genre_id` | Genre-level analysis. |
| `film_companies` | One row per movie-production-company association | Provisional: `movie_id` + `company_id` | Production-company analysis. |

Composite keys are provisional until duplicate and uniqueness checks are completed. Cast and crew must remain separate from the film-level dataset to avoid multiplying film rows when a movie has multiple credits.

## Columns and handling rules

| Column or field | Type | Rule | Seen in the data | If a row or value breaks it | Where |
|---|---|---|---|---|---|
| `source_row` | Integer | Identifies the original input row. | 127 candidate rows. | Stop if row identity cannot be maintained for reconciliation. | `pipeline/ingest.py` |
| `tmdb_id_raw` | Text | Preserve the original input value without silently normalizing it. | Blank, non-numeric, non-positive, duplicate, and valid values occur. | Preserve and flag the original value. | `pipeline/ingest.py` |
| `tmdb_id` | String | Stores the candidate ID as text; missing values are represented by an empty string. | 117 unique valid IDs. | Keep invalid source records in reconciliation; do not send them to the API. | 117 unique valid IDs. | Keep invalid source records in reconciliation; do not send them to the API. | `pipeline/ingest.py` |
| `movie_id` | Integer | Identifies a TMDb movie in acquired and analytical datasets. | Present in successful details and credits responses. | Do not create a film record from an unresolved ID. | `pipeline/extract.py`, planned `pipeline/transform.py` |
| `title` | Text | Preserve the TMDb title value. | Present in the acquired details schema. | Validate before publishing analytical output. | Planned `pipeline/transform.py` |
| `release_date` | Date or nullable date | Parse without inventing missing dates. | Present in the acquired details schema. | Preserve unparseable source values for diagnosis; do not fabricate a date. | Planned `pipeline/transform.py` |
| `budget` | Numeric | Preserve the source value; confirm interpretation before financial use. | Present in the acquired details schema. | Do not infer a missing or zero value. | Planned `pipeline/transform.py` |
| `revenue` | Numeric | Preserve the source value; confirm interpretation before financial use. | Present in the acquired details schema. | Do not infer a missing or zero value. | Planned `pipeline/transform.py` |
| `belongs_to_collection` | Object or null | Preserve collection information where supplied. | 96 objects and 16 null values across 112 details records. | Null means no collection object was supplied; do not invent membership. | Planned `pipeline/transform.py` |
| `genres` | List of objects | Preserve movie-to-genre relationships. | Between 1 and 5 genres per movie in the acquired records. | Do not duplicate film-level records when expanding the list. | Planned `pipeline/transform.py` |
| `production_companies` | List of objects | Preserve movie-to-company relationships. | Between 1 and 7 companies per movie. Some logo paths and country values are missing. | Retain the company record and preserve missing optional attributes. | Planned `pipeline/transform.py` |
| `cast` | List of objects | Expand to one row per cast credit. | 7,827 cast records across 112 movies. | Preserve credits with missing profile paths. | Planned `pipeline/transform.py` |
| `crew` | List of objects | Expand to one row per crew credit. | 24,932 crew records across 112 movies. One `known_for_department` value is null. | Preserve the credit and its missing attribute. | Planned `pipeline/transform.py` |

## Missing and incomplete metadata

The initial profile found:

- 15 movie records with blank `homepage` values.
- 55 production-company records with null `logo_path` values.
- Five production-company records with blank `origin_country` values.
- Three spoken-language records with blank language names; language codes are available.
- 2,190 cast records with null `profile_path` values.
- 18,811 crew records with null `profile_path` values.
- One crew record with a null `known_for_department`.

**Rule:** Missing optional metadata is preserved as missing. It must not cause an otherwise valid film, cast credit, crew credit, or company record to be deleted. Missing profile images, homepages, or descriptive labels must not be replaced with invented values.

## Run-level quality rules

| Rule | If it's broken | Where |
|---|---|---|
| Every original candidate row is accounted for in reconciliation. | The run fails its reconciliation check. | Planned `pipeline/checks.py` |
| Each valid unique candidate ID has separate details and credits outcomes. | The run fails its acquisition completeness check. | `pipeline/extract.py`, planned `pipeline/checks.py` |
| Successful raw responses remain traceable to their movie IDs and endpoints. | The run fails its cache integrity check. | `pipeline/extract.py`, planned `pipeline/checks.py` |
| Each analytical dataset conforms to its declared grain and key. | The run fails validation before analytical outputs are accepted. | Planned `pipeline/validate.py` |
| Expanding nested arrays does not multiply film-level records. | The run fails transformation validation. | Planned `pipeline/validate.py` |

## Reference data

TMDb genre, production-company, country, and language attributes are supplied within the acquired API responses. Their identifiers and source labels should be retained.

No external reference mapping or replacement for unresolved candidate IDs is currently authorized. Any additional mapping or business classification must be documented and justified before use.