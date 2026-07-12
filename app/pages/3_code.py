"""
app/pages/3_code.py
Owner: Phuc (C)
Task : Code browser — method filter, st.code display, calls GET /code-examples
"""

import streamlit as st
import requests
import os
import pandas as pd

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Code Examples", page_icon="💻")
st.title("💻 Danh sách Code Examples")

st.markdown("Trang này giúp bạn nhanh chóng tra cứu các đoạn tài liệu có chứa ví dụ code.")

@st.cache_data(ttl=60)
def fetch_sections():
    try:
        response = requests.get(f"{API_BASE_URL}/sections")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                return data.get("items", []) or data.get("data", [])
            return data
    except Exception as e:
        st.error(f"Lỗi kết nối API: {e}")
    return []

sections_data = fetch_sections()

if sections_data:
    df = pd.DataFrame(sections_data)
    
    # Lọc ra những section có chứa ít nhất 1 code block
    df_code = df[df['code_block_count'] > 0].copy()
    
    # Sắp xếp để những phần nhiều code nhất lên đầu
    df_code = df_code.sort_values(by='code_block_count', ascending=False)
    
    st.success(f"🎯 Tìm thấy **{len(df_code)}** phần tài liệu có chứa ví dụ code.")
    
    st.markdown("---")
    
    # Hiển thị từng phần dưới dạng Expander (bấm vào để mở rộng)
    for _, row in df_code.iterrows():
        with st.expander(f"📌 {row['section_title']} (Có {row['code_block_count']} code blocks)"):
            st.markdown(f"**Level:** {row['section_level']} | **Số từ:** {row['word_count']}")
            st.markdown("---")
            # Hiển thị nội dung text
            st.write(row['section_text'])
else:
    st.warning("⚠️ Không có dữ liệu.")