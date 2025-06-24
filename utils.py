import pandas as pd

def clean_mapping_headers(mapping_df: pd.DataFrame) -> pd.DataFrame:
    mapping_df = mapping_df.rename(columns=lambda x: str(x).strip())
    mapping_df = mapping_df.rename(columns={
        "旧品名": "旧品名", "新品名": "新品名"
    })
    mapping_df["旧品名"] = mapping_df["旧品名"].astype(str).str.strip()
    mapping_df["新品名"] = mapping_df["新品名"].astype(str).str.strip()
    return mapping_df.dropna(subset=["旧品名", "新品名"])

def apply_name_mapping(df: pd.DataFrame, name_col: str, mapping_df: pd.DataFrame) -> pd.DataFrame:
    df[name_col] = df[name_col].astype(str).str.strip()
    merged = df.merge(mapping_df, how="left", left_on=name_col, right_on="旧品名")
    df["_替换后品名"] = merged["新品名"].where(merged["新品名"].notna(), df[name_col])
    return df

def merge_files(dfs: list[pd.DataFrame], name_col: str, value_cols: list[str]) -> pd.DataFrame:
    combined = pd.concat(dfs, axis=0, ignore_index=True)
    result = combined.groupby("_替换后品名")[value_cols].sum(min_count=1).reset_index()
    return result
