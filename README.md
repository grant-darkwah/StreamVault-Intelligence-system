<div align="center">

# 🎬 StreamVault Intelligence System

**Data engineering and decision-support platform for film licensing analysis, powered by TMDb.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Data](https://img.shields.io/badge/Data-TMDb%20API-01B4E4)
![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white)

</div>

---

## Table of Contents

1. [Overview](#overview)
2. [Installation and Setup](#1-installation-and-setup)
3. [Run the Data Pipeline](#2-run-the-data-pipeline)
4. [Launch the Dashboard](#3-launch-the-dashboard)
5. [Run Tests](#4-run-tests)
6. [Project Structure](#5-project-structure)
7. [Data Source](#data-source)

---

## Overview

StreamVault Intelligence System analyses film licensing opportunities using movie metadata and credits from TMDb.

The project collects information about selected films, organises it for analysis, checks the quality of the data, and identifies promising franchise collections and individual films for licensing.

The accompanying Streamlit dashboard presents the results through an interactive, stakeholder-friendly interface: an executive overview of key findings, franchise and standalone film opportunities, data quality and candidate retrieval monitoring, and deal assessment insights to support content acquisition decisions.

The system is designed to be **reproducible**, **transparent**, and **easy to maintain** as the candidate catalogue grows.

---

## 1. Installation and Setup

Choose your operating system to view the instructions.

<details>
<summary>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/windows8/windows8-original.svg" width="20" height="20" alt="Windows logo">
  <strong>&nbsp;Windows</strong>
</summary>

### Prerequisites

- [Git for Windows](https://git-scm.com/downloads/win)
- [Python 3.10 or later](https://www.python.org/downloads/windows/) (enable **Add Python to PATH** during installation)

#### Step 1: Clone the repository

Open PowerShell:

```powershell
git clone https://github.com/grant-darkwah/StreamVault-Intelligence-system.git
cd StreamVault-Intelligence-system
```

#### Step 2: Create a virtual environment

```powershell
py -3 -m venv .venv
```

#### Step 3: Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run the following, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

#### Step 4: Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5: Configure environment variables

Create a `.env` file in the project root:

```env
TMDB_API_KEY=your_tmdb_api_key
```

</details>

<details>
<summary>
  <img src="https://cdn.simpleicons.org/apple/999999" width="20" height="20" alt="Apple logo">
  <strong>&nbsp;macOS</strong>
</summary>

### Prerequisites

- [Git](https://git-scm.com/downloads/mac)
- [Python 3.10 or later](https://www.python.org/downloads/macos/)

#### Step 1: Clone the repository

Open Terminal:

```bash
git clone https://github.com/grant-darkwah/StreamVault-Intelligence-system.git
cd StreamVault-Intelligence-system
```

#### Step 2: Create a virtual environment

```bash
python3 -m venv .venv
```

#### Step 3: Activate the environment

```bash
source .venv/bin/activate
```

#### Step 4: Install dependencies

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5: Configure environment variables

Create a `.env` file in the project root:

```env
TMDB_API_KEY=your_tmdb_api_key
```

</details>

<details>
<summary>
  <img src="https://cdn.simpleicons.org/linux/FCC624" width="20" height="20" alt="Linux logo">
  <strong>&nbsp;Linux</strong>
</summary>

### Prerequisites

Git, Python 3.10 or later, and Python virtual environment support.

On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-pip
```

#### Step 1: Clone the repository

```bash
git clone https://github.com/grant-darkwah/StreamVault-Intelligence-system.git
cd StreamVault-Intelligence-system
```

#### Step 2: Create a virtual environment

```bash
python3 -m venv .venv
```

#### Step 3: Activate the environment

```bash
source .venv/bin/activate
```

#### Step 4: Install dependencies

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5: Configure environment variables

Create a `.env` file in the project root:

```env
TMDB_API_KEY=your_tmdb_api_key
```

</details>

> [!WARNING]
> Never commit your `.env` file or expose your TMDb API key.

---

## 2. Run the Data Pipeline

Once setup is complete, run the command for your operating system:

| | OS | Command |
|---|---|---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/windows8/windows8-original.svg" width="18" alt="Windows"> | Windows | `python run_pipeline.py` |
| <img src="https://cdn.simpleicons.org/apple/999999" width="18" alt="macOS"> <img src="https://cdn.simpleicons.org/linux/FCC624" width="18" alt="Linux"> | macOS and Linux | `python3 run_pipeline.py` |

The pipeline performs:

- Candidate ID ingestion and validation
- TMDb movie details and credits extraction
- API response caching and candidate reconciliation
- Data transformation and validation
- Analytical ranking and export

Generated datasets are saved in the `out/` directory.

---

## 3. Launch the Dashboard

After the pipeline completes successfully:

| | OS | Command |
|---|---|---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/windows8/windows8-original.svg" width="18" alt="Windows"> | Windows | `python -m streamlit run dashboard.py` |
| <img src="https://cdn.simpleicons.org/apple/999999" width="18" alt="macOS"> <img src="https://cdn.simpleicons.org/linux/FCC624" width="18" alt="Linux"> | macOS and Linux | `python3 -m streamlit run dashboard.py` |

Open the local URL shown in your terminal, usually `http://localhost:8501`.

**Dashboard sections:**

| Section | Purpose |
|---|---|
| Executive Overview | Key findings at a glance |
| Franchise Opportunities | Promising franchise collections |
| Standalone Films | Individual film licensing candidates |
| Data Quality | Data quality and candidate retrieval monitoring |
| Deal Assessment | Insights to support acquisition decisions |

---

## 4. Run Tests

| | OS | Command |
|---|---|---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/windows8/windows8-original.svg" width="18" alt="Windows"> | Windows | `python -m pytest -v` |
| <img src="https://cdn.simpleicons.org/apple/999999" width="18" alt="macOS"> | macOS | `python3 -m pytest -v` |
| <img src="https://cdn.simpleicons.org/linux/FCC624" width="18" alt="Linux"> | Linux | `python3 -m pytest -v` |

---

## 5. Project Structure

```text
StreamVault-Intelligence-system/
│
├── .vscode/            # Editor configuration
├── dashboard/          # Streamlit dashboard modules and pages
├── data/               # Input datasets
├── demos/              # Demonstration materials
├── docs/               # Project documentation
├── explore/            # Exploratory data analysis
├── out/                # Generated analytical datasets
├── pipeline/           # Data pipeline modules
├── source_system/      # Source system components
├── tests/              # Automated tests
│
├── .env                # Environment variables (create locally; do not commit)
├── .gitignore          # Git exclusions
├── dashboard.py        # Dashboard entry point
├── README.md           # Project documentation
├── requirements.txt    # Python dependencies
└── run_pipeline.py     # Pipeline entry point
```

---

## Data Source

Movie metadata and credits are retrieved from the [TMDb API](https://developer.themoviedb.org/).

This project uses TMDb data but is not endorsed or certified by TMDb.