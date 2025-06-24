import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

from excel_utils import adjust_column_width
from github_utils import load_file_with_github_fallback
from mapping_utils import (
    clean_mapping_headers,
    apply_mapping_and_merge,
    apply_extended_substitute_mapping,
    load_file_with_github_fallback
)

st.set_page_config("🔁 品名替换合并工具", layout="wide")
st.title("📊 多文件品名替换与合并工具")

uploaded_files = st.file_uploader("📂 上传 Excel 数据文件（多个）", type="xlsx", accept_multiple_files=True)
mapping_file = st.file_uploader("📘 上传新旧料号对照表", type="xlsx")
start = st.button("🚀 开始处理")

if start:
    if not uploaded_files or mapping_file is None:
        st.warning("请上传需要处理的 Excel 文件和新旧料号对照表")
        st.stop()

    try:
        mapping_df = load_file_with_github_fallback("mapping", mapping_file)
        mapping_df = clean_mapping_headers(mapping_df)

        # 主替换表
        mapping_new = mapping_df[
            ["旧晶圆品名", "旧规格", "旧品名", "新晶圆品名", "新规格", "新品名"]
        ]
        mapping_new = mapping_new[
            ~mapping_new["新品名"].astype(str).str.strip().replace("nan", "").eq("")
        ]
        mapping_new = mapping_new[
            ~mapping_new["旧品名"].astype(str).str.strip().replace("nan", "").eq("")
        ]

        # 替代料号表（统一列名）
        def extract_sub_mapping(df, n):
            sub = df[
                ["新晶圆品名", "新规格", "新品名", f"替代晶圆{n}", f"替代规格{n}", f"替代品名{n}"]
            ]
            sub = sub[
                ~df[f"替代品名{n}"].astype(str).str.strip().replace("nan", "").eq("")
            ].copy()
            sub.columns = ["新晶圆品名", "新规格", "新品名", "替代晶圆", "替代规格", "替代品名"]
            return sub

        mapping_sub1 = extract_sub_mapping(mapping_df, 1)
        mapping_sub2 = extract_sub_mapping(mapping_df, 2)
        mapping_sub3 = extract_sub_mapping(mapping_df, 3)
        mapping_sub4 = extract_sub_mapping(mapping_df, 4)

    except Exception as e:
        st.error(f"❌ 映射表加载失败：{e}")
        st.stop()

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for file in uploaded_files:
            try:
                df = pd.read_excel(file)
                df.columns = df.columns.astype(str).str.strip()
                if df.empty:
                    st.warning(f"⚠️ 文件 `{file.name}` 内容为空，跳过")
                    continue

                st.subheader(f"📄 文件：{file.name}")
                name_col = st.selectbox(f"请选择品名列：", options=df.columns.tolist(), key=f"name_{file.name}")
                value_cols = st.multiselect(f"请选择要合并的数值列：", options=df.columns.tolist(), key=f"val_{file.name}")

                if not name_col or not value_cols:
                    st.warning(f"❗ 文件 `{file.name}` 未选择品名列或数值列，跳过")
                    continue

                # 替换逻辑
                df = apply_mapping_and_merge(df, mapping_new, name_col=name_col)
                for mapping_sub in [mapping_sub1, mapping_sub2, mapping_sub3, mapping_sub4]:
                    df = apply_extended_substitute_mapping(df, mapping_sub, name_col=name_col)

                for col in value_cols:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                grouped = df.groupby(name_col, as_index=False)[value_cols].sum(min_count=1)

                st.success(f"✅ `{file.name}` 数值列识别为：{value_cols}")
                st.dataframe(grouped.head())

                sheet_name = file.name[:31]
                grouped.to_excel(writer, sheet_name=sheet_name, index=False)
                adjust_column_width(writer.book[sheet_name])

            except Exception as e:
                st.error(f"❌ 处理文件 `{file.name}` 失败：{e}")

    buffer.seek(0)
    filename = f"品名合并_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    st.download_button("📥 下载合并结果 Excel", data=buffer, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
