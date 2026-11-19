# StreamVault Intelligence System

A Python data engineering pipeline and Streamlit dashboard for analysing film licensing opportunities using TMDb data.

## 1. Setup

Clone the repository:

```bash
git clone https://github.com/grant-darkwah/StreamVault-Intelligence-system.git
cd StreamVault-Intelligence-system
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
TMDB_API_KEY=your_tmdb_api_key
```

## 2. Run the Data Pipeline

```bash
python3 run_pipeline.py
```

The pipeline performs:
- Candidate ID ingestion and validation.
- TMDb movie details and credits extraction.
- API response caching and candidate reconciliation.
- Data transformation and validation.
- Analytical ranking and export.

Generated datasets are saved in `out/`.

## 3. Launch the Dashboard

After the pipeline completes successfully:

```bash
streamlit run dashboard.py
```

Open the URL displayed in the terminal, usually:

```text
http://localhost:8501
```

Dashboard sections:
- Executive Overview
- Franchise Opportunities
- Standalone Films
- Data Quality
- Deal Assessment

## 4. Run Tests

```bash
python3 -m pytest -v
```

## Project Structure

```text
StreamVault-Intelligence-system/
│
├── .vscode/                 # Editor configuration
├── dashboard/              # Streamlit dashboard modules and pages
├── data/                   # Input datasets
├── demos/                  # Demonstration materials
├── docs/                   # Project documentation
├── explore/                # Exploratory data analysis
├── out/                    # Generated analytical datasets
├── pipeline/               # Data pipeline modules
├── source_system/           # Source system components
├── tests/                   # Automated tests
│
├── .env                     # Environment variables
├── .gitignore               # Git exclusions
├── dashboard.py             # Dashboard entry point
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
└── run_pipeline.py          # Pipeline entry point
```

**Note:** Keep `.env` private and never commit API credentials. Movie metadata is sourced from [TMDb](https://developer.themoviedb.org/).