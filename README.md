Here is a comprehensive, production-ready `README.md` file designed for your project. You can copy and paste this directly into your repository.

---

# Air Quality Data Pipeline: Cleaning, Transformation & Data Modeling

This repository contains the core data engineering and preparation pipeline for processing high-frequency Delhi air quality and meteorological monitoring data. The pipeline is designed to transform complex, multi-station raw metrics into a structured, highly optimized star-schema database ready for analysis and dashboarding (via a companion Streamlit app).

## Project Overview

* **Dataset:** `team_1.parquet` (Delhi Air-Quality + Meteorological monitoring metrics)
* **Data Volume:** 3,495,959 rows × 22 columns (Raw shape)
* **Temporal Coverage:** January 2024 – December 2025 (15-minute sampling frequency)
* **Geospatial Coverage:** 6 monitoring stations across Delhi
* **Feature Breadth:** 13 key pollutants alongside 8 core meteorological dimensions

> **Scope Note:** This subsystem focuses purely on **data engineering, validation, advanced feature engineering, and dimensional modeling**. No predictive machine learning modeling is performed in this step.

---

## Data Pipeline Architecture

The pipeline processes data sequentially through 11 major stages, implemented programmatically for reproducible execution:

```
[Raw Parquet] ──> [Profiling & Validation] ──> [Missing Value/Outlier Filtering]
                       │
                       ▼
[SQLite DB Fact/Dims] <── [Star Schema Modeling] <── [Long-to-Wide Transformation]

```

### 1. Setup & Environment

The project relies on highly efficient columnar data engines and data manipulation ecosystems to process millions of rows seamlessly.

* **Engines:** `pyarrow` for fast parquet parsing.
* **Libraries:** `pandas`, `numpy`, `sqlite3`, `matplotlib`, `seaborn`.

### 2. Loading & Column Profiling

* Ingests data while preserving native timezone-aware timestamps (UTC converted to local where applicable).
* Tracks standard structural metadata (`df.info()`, descriptive summary statistics) to baseline the initial quality of raw attributes.

### 3. Core Structural Audit

* **Station Integrity:** Mapping and verifying relationships between redundant metadata pools (`station_id`, `station`, and `station_name`). Confirms a 1:1 consistent match across 6 explicit locations.
* **Pollutant Auditing:** Verifying value distributions across all 13 mapped pollutants (including $PM_{2.5}$, $PM_{10}$, $NO_2$, $CO$, and volatile organic compounds like benzene, toluene, and xylene).

### 4. Advanced Missing Value Treatment

* Identifies heavy missingness on meteorological factors such as vertical wind speed (`vws_m_s` at 100% missing), standard wind speed (`ws_m_s`), and ambient temperatures.
* **Strategic Resolution:** Analytical isolation reveals that DPCC stations suffer minor sensor drops, while IMD stations completely lack meteorological components. The pipeline leaves IMD weather records explicitly as `NaN` to maintain historical reality, while interpolating short DPCC sensor dropouts.

### 5. Outlier Detection & Continuous Validation

* Establishes physical and analytical thresholds for real-world environmental bounds (e.g., preventing relative humidity values from exceeding 100% or falling below 0%).
* Leverages statistical validation window criteria to filter anomalous sensor spikes without erasing genuine extreme environmental episodes (such as heavy seasonal smog peaks).

### 6. Feature Engineering

* **Temporal Splits:** Extracts granular index flags including `year`, `month`, `day`, `hour`, `day_of_week`, and `is_weekend` from raw 15-minute intervals.
* **Sub-Index Formulation:** Translates raw component mass measurements into normalized categorical values (such as calculating standard safety thresholds for individual pollutant indices).

### 7. Long-to-Wide Schema Transformation

* Reshapes the dataset from a narrow transactional log format into a clean tabular layout, where every distinct timestamp/station combination forms a single unique row, and pollutants represent independent columns. This structural adjustment simplifies aggregations.

### 8. Star-Schema Dimensional Modeling

To support analytical indexing and fast querying, the wide dataset is mapped into a relational data warehouse model:

* **`Fact_AirQuality`:** Central table holding time-series continuous pollutant metrics, weather metrics, and composite identifiers.
* **`Dim_Station`:** Station properties, geographical metadata mappings, and operational agency data.
* **`Dim_Time`:** Calendar features, hour blocks, and seasonal flags.

### 9. SQLite Persistence DB Storage

* Initializes a local relational database storage schema (`air_quality.db`).
* Configures index keys, primary constraints, and table definitions to optimize database storage footprints.

### 10. Analytical Exploration

* Generates comprehensive base visualizations tracking distribution skewness, seasonal variations, and station correlation matrices using `matplotlib` and `seaborn`.

### 11. Downstream Target Export

* Saves the refined, clean parquet frames into the workspace. These files are optimized for fast loading into the interactive Streamlit user dashboard application.

---

## Directory Schema

```text
├── air_quality_pipeline.ipynb   # Master interactive cleaning & modeling notebook
├── air_quality.db               # Output generation SQLite DB (created upon run)
├── README.md                    # Project documentation
└── requirements.txt             # Environment dependency manifests

```

## Quick Start & Execution

1. **Clone the repository and install dependencies:**
```bash

```



pip install -r requirements.txt

```

2. **Configure Data Access Paths:**
   Open `air_quality_pipeline.ipynb` and confirm the path pointer macro matches your local file directory layout:
   ```python
   RAW_PATH = 'path/to/your/team_1.parquet'

```

3. **Run the Pipeline:**
Execute all cells within `air_quality_pipeline.ipynb` to clean the raw parquet file, build the relational tables, and generate the structured SQLite database file.
