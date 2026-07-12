"""
pipeline/extractor.py
Owner: Phuc (C)
Task : F3+F4 — soup → sections.csv and links.csv
"""

import pandas as pd
from bs4 import BeautifulSoup
from pipeline.link_classifier import classify_link
from shared.constants import SECTION_COLS
from pipeline.parser import extract_section_tree, HEADING_TAGS

def run_extraction():
    print("Bắt đầu tiến trình trích xuất dữ liệu...")
    
    # 1. Đọc file HTML raw đã được tải về
    html_path = "data/raw/beautifulsoup_doc.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy {html_path}. Hãy chạy 'python -m pipeline.collector' trước.")
        return
    
    # ---------------------------------------------------------
    # PHẦN 1: TẠO FILE sections.csv
    # ---------------------------------------------------------
    print("1. Đang trích xuất sections...")
    sections_data = extract_section_tree(soup)
    df_sections = pd.DataFrame(sections_data, columns=SECTION_COLS)
    df_sections.to_csv("data/processed/sections.csv", index=False)
    print(f"   -> Đã lưu {len(df_sections)} sections.")
    
    # ---------------------------------------------------------
    # PHẦN 2: TẠO FILE links.csv
    # ---------------------------------------------------------
    print("2. Đang trích xuất links...")
    links_data = []
    
    # Lấy danh sách các thẻ heading (h1, h2, h3) từ biến của Đạt
    heading_tags_list = list(HEADING_TAGS.keys())
    
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href")
        link_type = classify_link(href)

        link_text = a_tag.get_text(strip=True)
        
        # Logic đi ngược lên tìm heading gần nhất phía trên thẻ <a>
        nearest_heading_tag = a_tag.find_previous(heading_tags_list)
        nearest_heading = nearest_heading_tag.get_text(strip=True) if nearest_heading_tag else "No Heading"

        links_data.append({
            "href": href,
            "link_type": link_type,
            "link_text": link_text,
            "section_title": nearest_heading
        })

    df_links = pd.DataFrame(links_data)
    df_links.to_csv("data/processed/links.csv", index=False)
    print(f"   -> Đã phân loại và lưu {len(df_links)} links.")
    
    print("Hoàn thành trích xuất! Các file đã được lưu vào thư mục data/processed/")

if __name__ == "__main__":
    run_extraction()