"""
app/pages/2_links.py
Owner: Phuc (C)
Task : Link explorer — type filter, pie chart, calls GET /links
"""

import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Links Analytics", page_icon="🔗")
st.title("🔗 Phân tích Links")

# 1. Gọi API và vẽ biểu đồ tròn (Pie Chart)
st.subheader("📊 Phân bố các loại liên kết")
try:
    res_stats = requests.get(f"{API_BASE_URL}/links/stats")
    if res_stats.status_code == 200:
        stats = res_stats.json()
        df_stats = pd.DataFrame(list(stats.items()), columns=['Loại Link', 'Số lượng'])
        
        # Vẽ biểu đồ bằng Plotly
        fig = px.pie(df_stats, values='Số lượng', names='Loại Link', hole=0.3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Lỗi khi lấy dữ liệu thống kê.")
except Exception as e:
    st.error(f"Lỗi kết nối API: {e}")

st.markdown("---")

# 2. Bảng danh sách liên kết có chức năng lọc
st.subheader("📋 Chi tiết các liên kết")
link_types = ["Tất cả", "internal_anchor", "external_link", "documentation_link", "image_link", "empty_or_invalid"]
selected_type = st.selectbox("Lọc theo loại link:", link_types)

# Thiết lập URL gọi API tùy theo bộ lọc
api_url = f"{API_BASE_URL}/links"
if selected_type != "Tất cả":
    api_url += f"?link_type={selected_type}"

try:
    res_links = requests.get(api_url)
    if res_links.status_code == 200:
        links_list = res_links.json()
        if links_list:
            df_links = pd.DataFrame(links_list)
            # Chỉ hiển thị các cột quan trọng
            st.dataframe(df_links[['section_title', 'link_text', 'link_type', 'href']], use_container_width=True)
        else:
            st.info("Không có liên kết nào phù hợp với bộ lọc.")
except Exception as e:
    st.error("Lỗi khi lấy danh sách liên kết.")