# 🌍 Air Quality Data Engineering Project

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10-blue.svg)](https://www.python.org/)
[![Git LFS](https://img.shields.io/badge/Git_LFS-Enabled-orange.svg)](https://git-lfs.github.com/)
[![Streamlit App](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end data engineering pipeline designed to ingest, clean, store, and visualize large-scale ambient air quality datasets. This project processes raw complex data chunks, structures them into an optimized localized data warehouse schema, and exposes an interactive analytics dashboard for real-time insights.

---

## 🚀 Key Features
* **Robust ETL Pipeline:** Formats messy raw data inputs into standardized data structures.
* **Large-Scale Data Support:** Implements **Git LFS** and **Apache Parquet / SQLite (`.db`)** optimizations to manage files exceeding standard GitHub thresholds securely.
* **Interactive Analytics UI:** A fast, responsive dashboard built with **Streamlit** to filter and track key air quality metrics (PM2.5, PM10, $CO_2$) over time.
* **High-Performance Storage:** Leverages columnar data formats (`.parquet`) for optimized query speeds and efficient data compression.

---

## 🏗️ System Architecture & Data Flow

```mermaid
graph TD
    A[Raw Complex Data] -->|Python Extraction| B(ETL Data Cleaning & Imputation)
    B -->|Metadata Generation| C[cleaning_summary.json]
    B -->|Serialized Data| D[(air_quality.db / Parquet Storage)]
    D -->|Optimized Queries| E[Streamlit Dashboard Web App]

📂 Project Repository Structure

├── .gitattributes          # Configuration for Git Large File Storage (LFS)
├── air_quality.db          # Unified SQLite Database Warehouse (~341 MB via LFS)
├── cleaning_summary.json   # Auto-generated ETL tracking & data anomaly logs
├── streamlit_app.py        # Frontend Dashboard UI entrypoint
├── requirements.txt        # Managed Python dependencies
└── README.md               # Project documentation

🛠️ Tech Stack & ToolingCategoryTechnology UsedPurposeLanguagePython 3.xCore programming language for processing & UIData Eng & ETLPandas / NumPyData manipulation, cleanup, and aggregationStorage EngineSQLite / ParquetHigh-capacity data warehouse layerLarge File StorageGit LFSTracks and pushes hefty dataset historiesVisualization UIStreamlit / PlotlyInteractive user graphs and KPI tracking dashboards⚡ Getting Started & Local Setup1. Clone the Repository (with LFS attached)Ensure you have Git LFS installed on your local machine before pulling the large files.Bashgit clone [https://github.com/deendayalmali2-byte/deen-dayal-data-engineering-project.git](https://github.com/deendayalmali2-byte/deen-dayal-data-engineering-project.git)
cd "air quality"
git lfs pull
2. Set Up a Virtual Environment & DependenciesBash# Create Environment
python -m venv venv

# Activate Environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install required frameworks
pip install -r requirements.txt
3. Run the Analytics DashboardLaunch the Streamlit web application interface locally:Bashstreamlit run streamlit_app.py
📊 Pipeline Insights & Data OptimizationBy converting unoptimized processing stages into streamlined .parquet and indices-backed relational databases, query execution rates for rendering dashboard visuals were reduced significantly.Check out cleaning_summary.json to inspect the structural changes, dropped anomalies, and data volume shifts executed during the automated ETL transformation pass.👤 AuthorDeveloper: @deendayalmali2-byteAcademic/Org Mail: zda23b002@iitmz.ac.inDeveloped as part of a modern data engineering pipeline assignment.
### Why this works for your project:
1. **Mermaid Diagram:** It automatically renders a neat flow chart on GitHub showing how your data transforms from raw files to the Streamlit app.
2. **Badges:** The colorful buttons at the top instantly make it look like a real production enterprise repo.
3. **Markdown Tables:** Neatly categorizes your skills (Python, SQLite, Parquet, Streamlit) so recruiters can scan them in under 2 seconds.
