# Aadhar Datasets

This repository analyzes Aadhar Datasets provided by UIDAI for **UIDAI Data Hackathon** and extracts useful insights which may be further used to improve Aadhar services.

# Installation

- Clone this repository
```bash
git clone https://github.com/SurfyPenguin/aadhar-datasets.git
```
# Usage
### For UV:
This is an uv project, standalone uv installation is recommended please follow uv standalone [installation](https://docs.astral.sh/uv/getting-started/installation/).
1. Create virtual environment:
```bash
uv venv
```
2. Sync dependencies
```bash
uv sync
```
3. Run `main.py`
```bash
uv run streamlit run main.py # if venv not activated
streamlit run main.py # if venv activated
```

## For PIP:
1. Create virtual environment:
```bash
python -m venv .venv
```
2. Switch to virtual environment:
```bash
source .venv/bin/activate # linux/mac

.\.venv\Scripts\Activate.ps1 # windows
```
3. Install dependencies using
```bash
pip install .
```
4. Run `main.py`:
```bash
streamlit run main.py
```
