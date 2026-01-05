# Health Graduate Gender Inequality Dashboard

Streamlit dashboard exploring gender patterns, occupations, and earnings of health graduates. Currently hosted at https://ethos-ai.10eden.com for quick viewing.

## Running locally
- Install dependencies: `pip install -r requirements.txt`
- Start the app: `streamlit run data/app.py`
- The dashboard expects the cleaned CSVs at `data/cleaned/rq1/cleaned_gender_pivot.csv`, `data/cleaned/rq2/cleaned_graduate_gender_ocupations.csv`, and `data/cleaned/rq3/rq3_earnings_clean.csv`. Adjust paths in `data/app.py` if you relocate files.

## Repository layout
- `data/app.py` – main Streamlit app.
- `data/cleaned/` – cleaned datasets used in the app, grouped by RQ (`rq1`, `rq2`, `rq3`).
- `data/map_data/` – shapefiles for HSE regions.
- `data/notebooks/` – exploratory and dashboard notebooks. Paths inside may need updating to the new `data/cleaned/` locations before re-running.
- `data/raw/` – original and alternative dataset formats (CSV, XLSX, PX) and exploratory files.
- `data/archive/` – older working copies.

I did some tidying since creating the notebooks so there could be some errors and you may have update file paths accordingly before wrangling or re-running notebooks.
