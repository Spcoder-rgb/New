# Food Inventory Management: Analysis and Comparison

Analyze and compare university food outlet inventory data with NumPy, Pandas, Matplotlib, and Plotly. Includes holding cost analysis, EOQ estimation, event-driven demand, packaged vs raw comparisons, expiry risk, and outlet comparisons.

## Project Structure

- `data/raw`: CSV datasets (generated synthetic data)
- `notebooks/analysis.ipynb`: Main analysis notebook
- `src/generate_sample_data.py`: Numpy/Pandas data generator
- `src/generate_sample_data_basic.py`: Stdlib-only generator (no external deps)
- `requirements.txt`: Python dependencies

## Setup

Option A: Local Python

1. Install Python 3.10+
2. Create a virtual environment
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Generate data (optional, already included):
   ```bash
   python src/generate_sample_data.py
   # or (no third-party deps)
   python src/generate_sample_data_basic.py
   ```
5. Open the notebook:
   ```bash
   jupyter lab notebooks/analysis.ipynb
   ```

Option B: Google Colab

- Upload the project or mount your repo, then run:
  ```python
  !pip install -r requirements.txt
  ```

## What’s Inside

- Holding costs per outlet/university
- EOQ across outlets and categories
- Event uplift analysis
- Packaged vs raw revenue comparison
- Expiry risk and wastage
- Interactive Plotly comparisons (if Plotly available)

## Notes

- EOQ uses classical formula \( EOQ = \sqrt{\frac{2DS}{H}} \) with daily-to-annual scaling.
- Synthetic data is randomized; replace CSVs in `data/raw` with real exports from POS/inventory systems to analyze your outlets.
