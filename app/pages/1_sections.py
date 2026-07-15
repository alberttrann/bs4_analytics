"""
app/pages/1_sections.py
Owner: Phuc (C)
Task : Section explorer — searchable table, expandable text, calls GET /sections
"""

import streamlit as st
import requests
import os
import pandas as pd

# Lấy URL của API từ biến môi trường
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Sections Analytics", page_icon="📑")
st.title("📑 Phân tích Sections")

@st.cache_data(ttl=60)
def fetch_sections():
    """Gọi API để lấy danh sách các sections"""
    try:
        response = requests.get(f"{API_BASE_URL}/sections")
        if response.status_code == 200:
            data = response.json()
            
            # Xử lý trường hợp API trả về kiểu phân trang (pagination)
            if isinstance(data, dict):
                # Thường dữ liệu thật sẽ nằm trong key 'items' hoặc 'data'
                if "items" in data:
                    return data["items"]
                elif "data" in data:
                    return data["data"]
                
            return data # Trả về nguyên gốc nếu nó đã là một list
    except Exception as e:
        st.error(f"Lỗi kết nối API: {e}")
    return []

sections_data = fetch_sections()

if not sections_data:
    st.warning("⚠️ Không có dữ liệu. Vui lòng đảm bảo API server đang chạy và dữ liệu đã được trích xuất.")
else:
    df = pd.DataFrame(sections_data)
    
    # Tính năng tìm kiếm
    search_term = st.text_input("🔍 Tìm kiếm section theo tiêu đề:")
    if search_term:
        df = df[df['section_title'].str.contains(search_term, case=False, na=False)]
        
    st.markdown(f"**Hiển thị {len(df)} sections:**")
    
    # Hiển thị bảng tóm tắt
    cols_to_show = ['section_level', 'section_title', 'word_count', 'code_block_count', 'link_count']
    st.dataframe(df[cols_to_show], use_container_width=True)
    
    st.markdown("---")
    st.subheader("📖 Chi tiết nội dung")
    
    # Tính năng mở rộng từng hàng để xem text
    for _, row in df.iterrows():
        with st.expander(f"{row['section_title']} (Level {row['section_level']})"):
            st.markdown(f"**Số từ:** {row['word_count']} | **Code blocks:** {row['code_block_count']} | **Links:** {row['link_count']}")
            st.markdown("---")
            st.write(row['section_text'])