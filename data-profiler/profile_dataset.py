import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
import glob

import pandas as pd
import sweetviz as sv
from dotenv import load_dotenv

# Import snowflake connector lazily
try:
    import snowflake.connector
except Exception:
    snowflake = None


ROOT_DIR = Path('.').resolve()
INPUT_DIR = ROOT_DIR / 'input'
OUTPUT_DIR = ROOT_DIR / 'output'
DEFAULT_SQL_FILE = ROOT_DIR / 'query.sql'
DEMO_FILENAME = 'demo_data.csv'


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Generate a Sweetviz report from demo_data.csv (root), ./input, or Snowflake via ./query.sql')
    p.add_argument(
        '--mode',
        choices=['local', 'snowflake'],
        required=True,
        help='local: read demo_data.csv (root) or CSV/Parquet from ./input; snowflake: run ./query.sql against Snowflake',
    )
    p.add_argument('--input', default=None, help="Filename for local mode. Use 'demo_data.csv' (root) or a file under ./input (e.g., mydata.csv).")
    p.add_argument('--limit', type=int, default=None, help='Optional LIMIT (applied to SQL mode)')
    p.add_argument('--target', default=None, help='Optional target column for Sweetviz target analysis')
    p.add_argument('--sample', type=int, default=None, help='Optional random row sample size after fetch')
    p.add_argument('--output-name', default=None, help='Output HTML filename (written to ./output)')
    return p.parse_args()


def ensure_dirs():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def resolve_output_path(output_name: str | None) -> Path:
    if output_name:
        name = output_name if output_name.endswith('.html') else f'{output_name}.html'
    else:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        name = f'profile_{ts}.html'
    return OUTPUT_DIR / name


def find_local_file(user_filename: str | None) -> Path:
    """
    Resolution rules:
      - If user_filename is provided:
          * If it's exactly 'demo_data.csv' and exists in ROOT, use ROOT/demo_data.csv.
          * If it's an absolute or relative path that exists, use it as-is.
          * Otherwise try INPUT_DIR/user_filename.
      - If user_filename is not provided:
          * If ROOT/demo_data.csv exists, use it (demo default).
          * Else auto-detect the first CSV/Parquet in INPUT_DIR.
    """
    # If an explicit filename was given
    if user_filename:
        # Special-case: demo_data.csv from project root
        if Path(user_filename).name == DEMO_FILENAME:
            demo_root = ROOT_DIR / DEMO_FILENAME
            if demo_root.exists():
                return demo_root

        # If the user gave a path (absolute or relative) that exists, use it
        p_given = Path(user_filename)
        if p_given.exists():
            return p_given.resolve()

        # Otherwise, treat it as a filename in ./input
        candidate = INPUT_DIR / user_filename
        if candidate.exists():
            return candidate.resolve()
        print(f"[ERROR] File not found: {user_filename} (checked '{p_given}' and '{candidate}')", file=sys.stderr)
        sys.exit(4)

    # No filename provided: prefer demo_data.csv in root if present
    demo_root = ROOT_DIR / DEMO_FILENAME
    if demo_root.exists():
        print(f"[INFO] Auto-selected demo file in root: {demo_root}")
        return demo_root.resolve()

    # Otherwise auto-detect first CSV/Parquet in ./input
    candidates = []
    candidates += glob.glob(str(INPUT_DIR / '*.csv'))
    candidates += glob.glob(str(INPUT_DIR / '*.parquet'))
    if not candidates:
        print(f"[ERROR] No CSV or Parquet files found in {INPUT_DIR.resolve()}, and '{DEMO_FILENAME}' not present in {ROOT_DIR}.", file=sys.stderr)
        sys.exit(4)
    candidates.sort()
    print(f"[INFO] Auto-selected input file: {candidates[0]}")
    return Path(candidates[0]).resolve()


def read_local_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == '.csv':
        # Try to sniff delimiter & encoding
        try:
            import csv, chardet
            raw = path.read_bytes()
            enc_guess = (chardet.detect(raw).get('encoding') or 'utf-8')
            try:
                sample = raw[:100000].decode(enc_guess, errors='ignore')
            except Exception:
                enc_guess = 'utf-8'
                sample = raw[:100000].decode(enc_guess, errors='ignore')
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                sep = dialect.delimiter
            except Exception:
                sep = ','
            print(f"[INFO] Reading CSV: {path} (encoding={enc_guess}, sep='{sep}')")
            return pd.read_csv(path, encoding=enc_guess, sep=sep)
        except Exception as e:
            print(f"[WARN] Sniff failed, falling back to default read_csv: {e}")
            return pd.read_csv(path)
    elif suffix == '.parquet':
        print(f"[INFO] Reading Parquet: {path}")
        return pd.read_parquet(path)
    else:
        print(f"[ERROR] Unsupported file extension: {suffix}", file=sys.stderr)
        sys.exit(4)


def build_sql(limit: int | None) -> str:
    if not DEFAULT_SQL_FILE.exists():
        print(f"[ERROR] SQL file not found: {DEFAULT_SQL_FILE.resolve()}", file=sys.stderr)
        sys.exit(5)
    sql = DEFAULT_SQL_FILE.read_text(encoding='utf-8').strip()
    if not sql:
        print(f"[ERROR] SQL file is empty: {DEFAULT_SQL_FILE.resolve()}", file=sys.stderr)
        sys.exit(5)
    if limit is not None:
        sql = f"WITH src AS ({sql}) SELECT * FROM src LIMIT {limit}"
    return sql


def get_snowflake_connection():
    load_dotenv()  # loads .env

    required = {
        'SNOWFLAKE_ACCOUNT': os.getenv('SNOWFLAKE_ACCOUNT'),
        'SNOWFLAKE_USER': os.getenv('SNOWFLAKE_USER'),
        'SNOWFLAKE_PASSWORD': os.getenv('SNOWFLAKE_PASSWORD'),  # replace with key-pair if preferred
        'SNOWFLAKE_WAREHOUSE': os.getenv('SNOWFLAKE_WAREHOUSE'),
        'SNOWFLAKE_DATABASE': os.getenv('SNOWFLAKE_DATABASE'),
        'SNOWFLAKE_SCHEMA': os.getenv('SNOWFLAKE_SCHEMA'),
        'SNOWFLAKE_ROLE': os.getenv('SNOWFLAKE_ROLE'),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"[ERROR] Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)

    if snowflake is None:
        print('[ERROR] snowflake-connector-python not installed; check requirements.txt', file=sys.stderr)
        sys.exit(2)

    return snowflake.connector.connect(
        account=required['SNOWFLAKE_ACCOUNT'],
        user=required['SNOWFLAKE_USER'],
        password=required['SNOWFLAKE_PASSWORD'],
        warehouse=required['SNOWFLAKE_WAREHOUSE'],
        database=required['SNOWFLAKE_DATABASE'],
        schema=required['SNOWFLAKE_SCHEMA'],
        role=required['SNOWFLAKE_ROLE'],
        client_session_keep_alive=True,
    )


def fetch_df_snowflake(sql: str) -> pd.DataFrame:
    print('[INFO] Connecting to Snowflake…')
    conn = get_snowflake_connection()
    cur = conn.cursor()
    try:
        print('[INFO] Running query from ./query.sql…')
        cur.execute(sql)
        df = cur.fetch_pandas_all()
    finally:
        cur.close()
        conn.close()
    return df


def maybe_sample(df: pd.DataFrame, n: int | None) -> pd.DataFrame:
    if n is None or n <= 0 or n >= len(df):
        return df
    print(f'[INFO] Sampling {n} rows from {len(df)}…')
    return df.sample(n=n, random_state=42).reset_index(drop=True)


def main():
    ensure_dirs()
    args = parse_args()

    # Acquire DataFrame
    if args.mode == 'local':
        input_path = find_local_file(args.input)
        df = read_local_dataframe(input_path)
    else:  # snowflake
        sql = build_sql(args.limit)
        df = fetch_df_snowflake(sql)

    if df.empty:
        print('[ERROR] No data returned.', file=sys.stderr)
        sys.exit(3)

    print(f'[INFO] Loaded {len(df):,} rows × {len(df.columns)} columns.')
    df = maybe_sample(df, args.sample)

    # Generate Sweetviz report
    print('[INFO] Generating Sweetviz report…')
    if args.target and args.target in df.columns:
        report = sv.analyze(df, target_feat=args.target)
    else:
        report = sv.analyze(df)

    out_path = resolve_output_path(args.output_name)
    # Avoid auto-opening browser in WSL
    report.show_html(str(out_path), open_browser=False)
    print(f'[INFO] Done. Wrote report to: {out_path.resolve()}')


if __name__ == '__main__':
    main()
