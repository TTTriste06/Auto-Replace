import pandas as pd
import streamlit as st

def clean_mapping_headers(mapping_df):
    """
    将新旧料号表的列名重命名为标准字段，按列数自动对齐；若列数超限则报错。
    """
    required_headers = [
        "旧晶圆品名", "旧规格", "旧品名", 
        "新晶圆品名", "新规格", "新品名", 
        "封装厂", "PC", "封装形式", "半成品", "备注",
        "替代晶圆1", "替代规格1", "替代品名1", 
        "替代晶圆2", "替代规格2", "替代品名2", 
        "替代晶圆3", "替代规格3", "替代品名3", 
        "替代晶圆4", "替代规格4", "替代品名4"
    ]

    if mapping_df.shape[1] > len(required_headers):
        raise ValueError(f"❌ 新旧料号列数超出预期：共 {mapping_df.shape[1]} 列，最多支持 {len(required_headers)} 列")

    # ✅ 重命名当前列
    mapping_df.columns = required_headers[:mapping_df.shape[1]]

    # ✅ 仅保留这些列
    return mapping_df[required_headers[:mapping_df.shape[1]]]

def apply_mapping_and_merge(df, mapping_df, verbose=True):
    """
    按品名字段替换主料号（新旧料号映射）
    对 df 中的品名列进行逐行检查：
        若该品名在 mapping_df 中的“旧品名”列中存在，且对应“新品名”非空，
        则将其替换为该新品名。
    返回修改后的 DataFrame 和所有成功替换的新品名集合。
    """
    name_col = df.columns[0]
    df = df.copy()
    df[name_col] = df[name_col].astype(str).str.strip()
    mapping_df = mapping_df.copy()
    mapping_df["旧品名"] = mapping_df["旧品名"].astype(str).str.strip()
    mapping_df["新品名"] = mapping_df["新品名"].astype(str).str.strip()

    # 构造旧 -> 新 的映射字典，排除新品名为空的行
    mapping_dict = dict(
        mapping_df[mapping_df["新品名"] != ""][["旧品名", "新品名"]].values
    )

    replaced_names = set()
    # 逐行替换
    df[name_col] = df[name_col].apply(lambda x: mapping_dict[x] if x in mapping_dict else x)

    # 记录被替换的新品名（即原品名 != 映射后的品名）
    replaced_names = set(mapping_dict.values()).intersection(set(df[name_col]))

    if verbose:
        st.write(f"✅ 新旧料号替换成功: {len(replaced_names)} 项")

    return df

def apply_extended_substitute_mapping(df, mapping_df, verbose=True):
    """
    替代料号品名替换（仅品名字段替换，无聚合合并）
    """
    name_col = df.columns[0]
    df = df.copy()
    df[name_col] = df[name_col].astype(str).str.strip().str.replace("\n", "").str.replace("\r", "")

    df = df[df[name_col] != ""].copy()

    # 清洗映射表中所有替代品名及新品名
    substitute_records = []
    for i in range(1, 5):
        sub_name = f"替代品名"
        for col in [sub_name, "新品名"]:
            if col not in mapping_df.columns:
                mapping_df[col] = ""
            mapping_df[col] = mapping_df[col].astype(str).str.strip().str.replace("\n", "").str.replace("\r", "")

        valid_rows = mapping_df[
            mapping_df[[sub_name, "新品名"]].notna().all(axis=1) &
            (mapping_df[sub_name] != "") &
            (mapping_df["新品名"] != "")
        ]

        for _, row in valid_rows.iterrows():
            substitute_records.append({
                "旧品名": row[sub_name],
                "新品名": row["新品名"]
            })

    # 替换品名
    matched_keys = set()
    for sub in substitute_records:
        mask = (df[name_col] == sub["旧品名"])
        if mask.any():
            """
            if verbose:
                st.write(f"🔁 替代品名: {sub['旧品名']} → {sub['新品名']}，行数: {mask.sum()}")
            """
            df.loc[mask, name_col] = sub["新品名"]
            matched_keys.update(df.loc[mask, name_col])

    if verbose:
        st.success(f"✅ 替代品名替换完成，共替换: {len(matched_keys)} 种")

    return df
    
