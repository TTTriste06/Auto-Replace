import streamlit as st
import pandas as pd
from utils import clean_mapping_headers, apply_name_mapping, merge_files

st.set_page_config("📊 品名合并工具", layout="wide")

st.title("📦 多文件品名识别合并工具")

# 上传多个数据文件
uploaded_files = st.file_uploader("📂 上传需要处理的 Excel 文件（支持多个）", type=["xlsx"], accept_multiple_files=True)

# 上传新旧料号表
mapping_file = st.file_uploader("🧭 上传新旧料号对照表（必须包含“旧品名”和“新品名”）", type="xlsx")

if uploaded_files and mapping_file:
    mapping_df = pd.read_excel(mapping_file)
    mapping_df = clean_mapping_headers(mapping_df)

    dfs = []
    st.markdown("### 🛠️ 请为每个文件选择字段")

    for file in uploaded_files:
        df = pd.read_excel(file)
        st.markdown(f"#### 📄 文件：{file.name}")

        name_col = st.selectbox(f"🧾 请选择品名字段（{file.name}）", options=df.columns.tolist(), key=f"name_{file.name}")
        value_cols = st.multiselect(f"🔢 请选择需要合并的数值列（{file.name}）", options=df.columns.tolist(), key=f"value_{file.name}")

        if name_col and value_cols:
            df = apply_name_mapping(df, name_col, mapping_df)
            dfs.append(df[["_替换后品名"] + value_cols])

    if st.button("🚀 开始合并"):
        result_df = merge_files(dfs, "_替换后品名", value_cols)
        st.success("✅ 合并成功！预览如下：")
        st.dataframe(result_df)

        # 下载按钮
        @st.cache_data
        def convert_df(df):
            return df.to_excel(index=False, engine="openpyxl")

        output = convert_df(result_df)
        st.download_button(
            label="📥 下载合并结果 Excel",
            data=output,
            file_name="品名合并结果.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.warning("请上传数据文件和新旧料号对照表")
