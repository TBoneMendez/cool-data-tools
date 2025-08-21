# 📊 Data Profiling Tool

Generate **Sweetviz** HTML data-profiling reports from:

- **Demo file** `demo_data.csv` placed in the **project root**
- **Local files** placed in `./input/` (CSV or Parquet), or
- **Snowflake** queries defined in `./query.sql`

Reports are always written to the `./output/` folder.

---

## 🚀 Features

- Works on **Python 3.13** (Sweetviz-based)
- Supports **CSV** (auto-detect encoding & delimiter) and **Parquet**
- Connects to **Snowflake** using credentials stored in `.env`
- Optionally apply **LIMIT** and **sampling** for faster reports
- Target-column support for classification datasets
- Clean folder layout: `input/`, `output/`, `query.sql`

---

## 📂 Project Structure

```
data-profiling/
├─ profile_dataset.py     # Main script
├─ query.sql              # SQL file for Snowflake profiling
├─ demo_data.csv          # Demo file (project root)
├─ input/                 # Put your own CSV/Parquet here
├─ output/                # Generated HTML reports go here
├─ .env.example           # Copy to .env and fill in Snowflake creds
├─ requirements.txt       # Python dependencies
└─ README.md              # This file
```

---

## ⚙️ Setup

1. **Create virtual environment**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**  
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure Snowflake credentials (if using Snowflake)**  
   Copy `.env.example` → `.env` and fill in your details.

---

## 🖥️ Usage

### Demo dataset (project root)
`demo_data.csv` lives in the project **root**. Run:
```bash
python profile_dataset.py --mode local --input demo_data.csv --output-name demo_report.html
```
The report will be saved to `./output/demo_report.html`.

---

### Local file profiling (`./input`)
1. Place your own CSV or Parquet file in the `./input/` folder.
2. Run auto-detection (first file found in `./input`):
   ```bash
   python profile_dataset.py --mode local
   ```
   or specify a file explicitly (resolved under `./input` unless you give an existing path):
   ```bash
   python profile_dataset.py --mode local --input mydata.csv --output-name local_report.html
   # also works:
   python profile_dataset.py --mode local --input ./input/mydata.csv
   python profile_dataset.py --mode local --input /full/path/to/mydata.csv
   ```

---

### Snowflake profiling (`./query.sql`)
1. Write your SQL in `query.sql`.
2. Run the profiler (with optional LIMIT and sampling):
   ```bash
   python profile_dataset.py --mode snowflake --limit 70000 --sample 30000 --output-name snowflake_profile.html
   ```

---

## 📑 Output

- A single **HTML file** report is generated in `./output/`.
- Open it directly in your browser (examples for WSL):
  ```bash
  wslview ./output/snowflake_profile.html   # if wslu is installed
  # or from Windows Explorer:
  explorer.exe .
  ```

---

## ⚠️ Notes

- Large datasets may take time; use `--limit` and `--sample` to reduce size.
- A harmless warning about `pkg_resources` may appear. We pin `setuptools<81` to avoid future breakage.
- For NumPy 2.x compatibility, `requirements.txt` pins `numpy<2.0` for Sweetviz.

---

✅ You can now profile either the **demo file in root**, your **own files in ./input**, or **Snowflake** data via `query.sql`.
