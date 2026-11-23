import subprocess
import zipfile
from pathlib import Path

import duckdb
import pandas as pd
from sklearn.model_selection import train_test_split

from src import config


def render_sql(sql_file: Path, **params) -> str:
    return sql_file.read_text().format(**params)


def find_raw_file() -> Path:
    matches = sorted(
        p for p in config.RAW_DIR.rglob("accepted_2007_to_2018*")
        if p.is_file() and p.suffix in {".csv", ".gz"}
    )
    if not matches:
        raise FileNotFoundError(f"No accepted-loans file in {config.RAW_DIR}; run download() first.")
    return matches[0]


def download() -> Path:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = config.RAW_DIR / "lending-club.zip"
    if not zip_path.exists():
        subprocess.run(
            ["kaggle", "datasets", "download", config.KAGGLE_DATASET, "-p", str(config.RAW_DIR)],
            check=True,
        )
    try:
        return find_raw_file()
    except FileNotFoundError:
        pass
    with zipfile.ZipFile(zip_path) as zf:
        members = [n for n in zf.namelist() if "accepted" in n.lower() and not n.endswith("/")]
        # The gzipped copy is smaller to store; DuckDB reads both.
        member = sorted(members, key=lambda n: not n.endswith(".gz"))[0]
        zf.extract(member, config.RAW_DIR)
    return find_raw_file()


def extract(force: bool = False) -> Path:
    if config.LOANS_PATH.exists() and not force:
        return config.LOANS_PATH
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    sql = render_sql(
        config.SQL_DIR / "01_extract.sql",
        raw_path=find_raw_file().as_posix(),
        out_path=config.LOANS_PATH.as_posix(),
    )
    duckdb.connect().execute(sql)
    return config.LOANS_PATH


def quality_connection() -> duckdb.DuckDBPyConnection:
    return sql_connection(config.SQL_DIR / "02_data_quality.sql", processed_path=config.LOANS_PATH.as_posix())


def sql_connection(sql_file: Path, **params) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(render_sql(sql_file, **params))
    return con


def load_model_data() -> pd.DataFrame:
    """Resolved, individual loans in the modelling samples, with invalid values set to missing."""
    df = pd.read_parquet(extract())
    df = df[
        df[config.TARGET].notna()
        & (df["application_type"] == "Individual")
        & df["sample"].isin(config.SAMPLES)
    ].copy()
    df[config.TARGET] = df[config.TARGET].astype(int)
    df.loc[df["annual_inc"] <= 0, "annual_inc"] = pd.NA
    df.loc[(df["dti"] < 0) | (df["dti"] > 100), "dti"] = pd.NA
    return df.reset_index(drop=True)


def split_development(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    dev = df[df["sample"] == "development"]
    return train_test_split(
        dev, test_size=config.VALID_SHARE, stratify=dev[config.TARGET], random_state=config.RANDOM_STATE,
    )


def classify_columns(columns: list[str]) -> pd.DataFrame:
    """Assign each column to one audit group; unlisted columns become candidate features."""
    owner = {}
    for group, cols in config.COLUMN_GROUPS.items():
        for col in cols:
            if col in owner:
                raise ValueError(f"{col} is listed in both {owner[col]} and {group}")
            owner[col] = group
    audit = pd.DataFrame({"column": columns})
    audit["group"] = audit["column"].map(owner).fillna("candidate_feature")
    return audit


if __name__ == "__main__":
    print("raw file:", download())
    print("processed:", extract())
