import os
from pathlib import Path
import datetime
import pandas as pd
from dotenv import load_dotenv
from utils.logging_config import setup_logging

logger = setup_logging()

load_dotenv()
data_dir = os.getenv("DATA_DIR", "main/data")
max_files = int(os.getenv("MAX_DATA_FILES", "30"))


def save_df_daily(df: pd.DataFrame) -> None:
    """
    Append DataFrame rows to a daily CSV (YYYY-MM-DD.csv) in data_dir.
    If the day's file doesn't exist it will be created. Keeps at most max_files csvs
    in the folder by removing the oldest files.

    Returns the Path to the file written.
    """
    if df is None or df.empty:
        return Path(data_dir)  # nothing to do

    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    date_obj = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"csfloat_filtered_listings_{date_obj}.csv"
    file_path = data_path / filename

    write_header = not file_path.exists()
    df.to_csv(file_path, mode="a", header=write_header, index=False)
    logger.info(f"Saved {len(df)} rows to {file_path}")

    # prune old csv files (by modification time) until at most max_files remain
    csv_files = sorted(data_path.glob("*.csv"), key=lambda p: p.stat().st_mtime)
    while len(csv_files) > max_files:
        oldest = csv_files.pop(0)
        try:
            oldest.unlink()
        except Exception:
            # ignore failures to delete a file; proceed with others
            pass