from pathlib import Path
import pandas as pd

def safe_csv_read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()
