# StreamVault — Working Analysis

## 1. Objective

Evaluate 127 candidate film records to support StreamVault's $14M licensing decision.

The analysis compares franchise bundles and standalone titles across:

- All release years.
- Titles released from 2000 onward.

## 2. Execution and reproducibility

**Requirements:** Python 3, Git, TMDb API key, and dependencies in `requirements.txt`.

Clone the repository:

```bash
git clone https://github.com/grant-darkwah/StreamVault-Intelligence-system.git
cd StreamVault-Intelligence-system
```

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Configure the TMDb API key using the environment variable defined in `pipeline/config.py`.

Run the pipeline:

```bash
python3 run_pipeline.py
```

Run tests:

```bash
python3 -m pytest -v
```

The test suite contains 29 passing tests.

## 3. Pipeline workflow

| Component | Responsibility |
|---|---|
| `pipeline/config.py` | Configuration and paths |
| `pipeline/ingest.py` | Candidate ID ingestion |
| `pipeline/extract.py` | TMDb data extraction and caching |
| `pipeline/transform.py` | JSON transformation |
| `pipeline/checks.py` | Data validation |
| `pipeline/load.py` | Parquet generation |
| `pipeline/analyze.py` | Metrics and rankings |
| `run_pipeline.py` | End-to-end orchestration |

## 4. Candidate reconciliation

| Category | Records |
|---|---:|
| Original records | 127 |
| Excess duplicate occurrences | 6 |
| Invalid identifiers | 4 |
| Unique valid IDs | 117 |
| Valid IDs not retrieved | 5 |
| Successfully analysed titles | 112 |

The four invalid records were blank, `-1`, `tt0468569`, and `N/A`.

Five valid IDs returned 404 responses on both TMDb endpoints.

The final analysis covers 112 titles, representing 95.7% of unique valid candidates.

## 5. Transformation and validation

The pipeline generated five analytical datasets:

| Dataset | Records |
|---|---:|
| Films | 112 |
| Cast | 7,827 |
| Crew | 24,932 |
| Film genres | 320 |
| Film companies | 307 |

Film-level records are separated from cast, crew, genre, and company relationships to prevent duplicated financial values during analysis.

Validation confirmed required tables, unique keys, and valid film references. All datasets passed structural checks.

## 6. Analytical methodology

### Franchise classification

| Classification | Film records |
|---|---:|
| Multi-film collections | 87 |
| Single-film collections | 9 |
| Standalone titles | 16 |

Only collections containing at least two sampled titles qualify for franchise ranking. Single-film collections are not treated as standalone titles.

### Ranking indicators

Standalone titles use:

- Vote average
- Vote count
- Popularity
- Reported revenue

Franchise collections use the median of these indicators across sampled titles.

All four indicators receive equal weight through percentile ranking. Composite scores are relative ranking indicators, not profitability estimates.

### Time periods

The same ranking methods are applied independently to all years and 2000 onward. Franchise sample counts are recalculated within each period.

## 7. Results: all years

### Top franchise collections

| Rank | Collection | Sampled titles | Median revenue |
|---:|---|---:|---:|
| 1 | The Avengers Collection | 4 | $1.786B |
| 2 | The Lord of the Rings Collection | 3 | $926.29M |
| 3 | The Dark Knight Collection | 3 | $1.008B |
| 4 | Harry Potter Collection | 8 | $936.09M |
| 5 | Pirates of the Caribbean Collection | 5 | $961.69M |

### Top standalone titles

| Rank | Title | Release year |
|---:|---|---:|
| 1 | Interstellar | 2014 |
| 2 | Inception | 2010 |
| 3 | Spirited Away | 2001 |
| 4 | Forrest Gump | 1994 |
| 5 | The Shawshank Redemption | 1994 |

## 8. Results: 2000 onward

### Top franchise collections

| Rank | Collection | Sampled titles | Median revenue |
|---:|---|---:|---:|
| 1 | The Avengers Collection | 4 | $1.786B |
| 2 | The Lord of the Rings Collection | 3 | $926.29M |
| 3 | The Dark Knight Collection | 3 | $1.008B |
| 4 | Harry Potter Collection | 8 | $936.09M |
| 5 | Toy Story Collection | 2 | $1.071B |

### Top standalone titles

| Rank | Title | Release year |
|---:|---|---:|
| 1 | Interstellar | 2014 |
| 2 | Inception | 2010 |
| 3 | Spirited Away | 2001 |
| 4 | WALL·E | 2008 |
| 5 | The Prestige | 2006 |

## 9. Period comparison

The top three franchise targets remain unchanged:

1. The Avengers Collection
2. The Lord of the Rings Collection
3. The Dark Knight Collection

The top three standalone titles also remain unchanged:

1. Interstellar
2. Inception
3. Spirited Away

Only the fourth and fifth standalone positions change. Therefore, the core shortlist is stable across both periods.

## 10. Director and cast observations

- Christopher Nolan directed Interstellar, Inception, and The Prestige.
- Michael Caine appears among the first three cast credits in Interstellar and The Prestige.
- Other directors include Hayao Miyazaki, Robert Zemeckis, Frank Darabont, and Andrew Stanton.

WALL·E contains voice/performance credits, so its cast should not be interpreted as conventional live-action star billing.

These are descriptive observations, not proof of commercial influence.

## 11. Generated outputs

The `out/` directory contains:

- `acquisition_summary.json`
- `candidate_reconciliation.csv`
- `films.parquet`
- `cast.parquet`
- `crew.parquet`
- `film_genres.parquet`
- `film_companies.parquet`
- `franchise_rankings_all_years.csv`
- `franchise_rankings_2000_onward.csv`
- `standalone_rankings_all_years.csv`
- `standalone_rankings_2000_onward.csv`

These outputs can also supply data to the proposed acquisition dashboard.

## 12. Limitations

- Five valid candidates could not be retrieved.
- Historical financial figures are not inflation- or currency-adjusted.
- Revenue-to-budget ratios do not represent profit or ROI.
- TMDb collections do not verify complete commercial bundle contents.
- Licensing prices, rights, territories, and contract periods are unavailable.
- Audience metrics do not establish expected StreamVault streaming performance.
- Equal weighting is an analytical assumption, not a validated commercial prediction.

## 13. Conclusion

The pipeline successfully analysed 112 titles and generated rankings for both required periods.

The top three franchise and standalone candidates remain stable across both comparisons. The results provide a shortlist for acquisition diligence, but final decisions require verified bundle contents, licensing terms, and StreamVault-specific financial assumptions.