# Data contract: StreamVault TMDb acquisition and analytical data

**Parties:** StreamVault analysis team (receives and processes data) and The Movie Database (TMDb) API (source provider).
**Version:** 0.2
**Status:** Implemented for the current transformation scope; acquisition and analytical outputs remain subject to source-data limitations.
**Decision record:** [ADR-004](adr/ADR-004.md) records the analytical normalization and Parquet persistence decision.

**Change control:** Changes to source handling, schema, validation rules, output grain, or persistence format must be documented, tested, and recorded in an ADR before implementation.

---

## Delivery

| Rule | If it's broken | Where |
|---|---|---|
| Candidate IDs are read from `data/raw/id_list.csv`. | Ingestion stops if the input file cannot be read. | `pipeline/ingest.py` |
| The input contains a `tmdb_id` column. | Ingestion stops if the required column is absent. | `pipeline/ingest.py` |
| Original candidate rows and raw ID values are preserved for reconciliation. | The run must not silently discard invalid or duplicate source records. | `pipeline/ingest.py`, `pipeline/extract.py` |
| Only unique, valid, positive numeric TMDb IDs are submitted for extraction. | Invalid IDs are retained in reconciliation output and excluded from API requests. | `pipeline/ingest.py`, `pipeline/extract.py` |
| Movie details and credits are acquired separately for each candidate ID. | Each endpoint outcome is recorded independently. | `pipeline/extract.py` |
| Successful API responses are cached as raw responses. | Failed responses are reported and must not be treated as successful cached data. | `pipeline/extract.py` |
| Cached successful responses are reused on subsequent runs. | A missing cache entry triggers an API request. | `pipeline/extract.py` |
| API credentials are loaded from project environment configuration. | The run stops if the API key is unavailable. | `pipeline/config.py` |
| API requests use configured connection and response timeouts and retry handling. | Request failures are recorded and are not treated as successful acquisitions. | `pipeline/extract.py` |
| Analytical outputs are generated from paired details and credits cache records. | Transformation stops if the details and credits movie-ID populations do not match. | `pipeline/transform.py` |
| Analytical outputs are validated before persistence. | Persistence stops when required tables, keys, uniqueness, or movie relationships fail validation. | `pipeline/checks.py`, `pipeline/load.py` |
| Analytical datasets are persisted as Parquet files. | The load step raises an error if a dataset cannot be written. | `pipeline/load.py` |

## Source observations

The initial acquisition record captured 127 candidate rows.

| Observation | Initial acquisition result | Handling |
|---|---:|---|
| Unique valid positive numeric IDs | 117 | Extract once per unique ID |
| Missing IDs | 1 | Preserve and report |
| Non-numeric IDs | 2 | Preserve and report |
| Non-positive IDs | 1 | Preserve and report |
| Rows belonging to duplicate groups | 12 | Preserve original rows; extract unique IDs once |
| Unique IDs returning 404 | 5 | Record as `not_found`; do not invent replacements |

The five unresolved numeric IDs returned 404 from both the details and credits endpoints. These are acquisition outcomes, not proof that the original source records should be deleted.

The initial acquisition run processed 117 unique valid IDs. For each endpoint, it recorded 111 new successful responses, one cache hit, and five `not_found` outcomes.

**Source-version note:** A later EDA read of the candidate CSV contained 126 rows and three invalid values, with no blank row. The initial acquisition record above reflects an earlier 127-row snapshot. These counts are retained as observations from different source snapshots; they must not be silently combined or treated as one identical file version.

## Acquired data

| Dataset | Grain | Key | Rule |
|---|---|---|---|
| Candidate input | One row per original source record | `source_row` | Preserve every original row, including duplicates and invalid IDs. |
| Movie details cache | One raw record per successfully acquired TMDb movie | `movie_id` in cache wrapper; payload `id` | Retain the raw TMDb response in `data/cache/details/`. |
| Movie credits cache | One raw record per successfully acquired movie | `movie_id` in cache wrapper; payload `id` | Retain cast and crew collections in the raw response in `data/cache/credits/`. |
| Acquisition reconciliation | One row per original candidate record | `source_row` | Link source records to validation and endpoint outcomes. |

Each cache record uses a wrapper containing `movie_id`, `endpoint`, `fetched_at`, and `data`. The transformation checks that the wrapper movie ID agrees with the payload `data.id`.

## Analytical datasets

The transformation currently produces five normalized pandas DataFrames. The current cache population contains 112 movies with matching details and credits records.

| Dataset | Grain | Key | Current rows | Columns | Purpose |
|---|---|---|---:|---:|---|
| `films` | One row per movie | `movie_id` | 112 | 17 | Film-level attributes used for analysis and licensing comparisons. |
| `cast` | One row per cast credit per movie | `movie_id` + `credit_id` | 7,827 | 13 | Actor and character-level analysis. |
| `crew` | One row per crew credit per movie | `movie_id` + `credit_id` | 24,932 | 12 | Director and other crew/talent analysis. |
| `film_genres` | One row per movie-genre association | `movie_id` + `id` (TMDb genre ID) | 320 | 3 | Genre-level analysis. |
| `film_companies` | One row per movie-production-company association | `movie_id` + `id` (TMDb company ID) | 307 | 5 | Production-company analysis. |

The composite keys above were checked against the current transformed population: all five tables had zero missing key values and zero duplicate keys. `cast` and `crew` remain separate from the film-level dataset to avoid multiplying film rows when a movie has multiple credits.

### Analytical schemas

Column order below follows the current transformation output. Nested source objects are retained in the relevant output column where stated.

| Dataset | Columns |
|---|---|
| `films` | `movie_id`, `title`, `original_title`, `release_date`, `release_year`, `budget`, `revenue`, `popularity`, `vote_average`, `vote_count`, `runtime`, `original_language`, `status`, `homepage`, `collection_id`, `collection_name`, `belongs_to_collection` |
| `cast` | `movie_id`, `adult`, `gender`, `id`, `known_for_department`, `name`, `original_name`, `popularity`, `profile_path`, `cast_id`, `character`, `credit_id`, `order` |
| `crew` | `movie_id`, `adult`, `gender`, `id`, `known_for_department`, `name`, `original_name`, `popularity`, `profile_path`, `credit_id`, `department`, `job` |
| `film_genres` | `movie_id`, `id`, `name` |
| `film_companies` | `movie_id`, `id`, `logo_path`, `name`, `origin_country` |

### Transformation rules

- `movie_id` is taken from the cache wrapper and checked against the response payload ID.
- A movie is transformed only when both details and credits records exist for it.
- `release_date` is retained as supplied by TMDb. `release_year` is derived from the first four characters when they are numeric; otherwise it is nullable.
- `belongs_to_collection` is retained as a nested object or null. `collection_id` and `collection_name` are extracted for convenient analysis.
- Cast, crew, genres, and production companies are expanded into separate relationship tables. They are not joined into `films`.
- Missing optional source attributes are retained as missing; the transformation does not fabricate values.
- The raw API responses remain available in the cache. The analytical `films` table is a selected 17-column projection, not a replacement for the raw details response.

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

The current five analytical tables do not include separate spoken-language or production-country relationship tables. Those nested attributes remain available in the raw details cache and are not represented as separate analytical outputs in this transformation version.

## Run-level quality rules

| Rule | If it's broken | Where |
|---|---|---|
| Details and credits cache populations contain the same movie IDs. | Transformation stops and reports IDs missing from either endpoint population. | `pipeline/transform.py` |
| Cache wrapper IDs agree with payload IDs. | Transformation stops with a cache ID mismatch error. | `pipeline/transform.py` |
| All five analytical tables are present. | Validation fails. | `pipeline/checks.py` |
| Required key columns exist in each table. | Validation fails and identifies missing columns. | `pipeline/checks.py` |
| Key values are non-null and unique at the declared grain. | Validation fails when missing or duplicate keys are found. | `pipeline/checks.py` |
| Every child-table `movie_id` exists in `films`. | Validation fails when orphan movie IDs are found. | `pipeline/checks.py` |
| Each film appears once in `films`. | Validation fails if `movie_id` is duplicated. | `pipeline/checks.py` |
| Data is validated before persistence. | `save_datasets` raises an error rather than writing invalid analytical data. | `pipeline/load.py`, `pipeline/checks.py` |
| Each analytical dataset is written without a pandas index. | The load step raises an error if Parquet persistence fails. | `pipeline/load.py` |

The current implementation passed validation on the 112-film cache population: zero missing keys, zero duplicate keys, and no orphan movie IDs in the child tables. The complete project test suite passed 25 tests at the time of this contract update.

## Persistence

The load module writes one Parquet file per analytical dataset under `out/`:

- `out/films.parquet`
- `out/cast.parquet`
- `out/crew.parquet`
- `out/film_genres.parquet`
- `out/film_companies.parquet`

Parquet is written using the PyArrow engine with `index=False`. The current files were read back successfully, and their row counts matched the transformed DataFrames.

## Reference data

TMDb genre, production-company, country, and language attributes are supplied within the acquired API responses. Their identifiers and source labels should be retained.

No external reference mapping or replacement for unresolved candidate IDs is currently authorized. Any additional mapping or business classification must be documented and justified before use.

## Related decisions

- [ADR-001: Preserve source records and deduplicate extraction](adr/ADR-001.md)
- [ADR-002: Cache successful endpoint responses](adr/ADR-002.md)
- [ADR-003: Track endpoint outcomes independently](adr/ADR-003.md)
- [ADR-004: Normalize analytical datasets and persist as Parquet](adr/ADR-004.md)
