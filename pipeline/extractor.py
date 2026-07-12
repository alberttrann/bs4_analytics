"""
pipeline/extractor.py
Owner: Phuc (C)
Task : F3+F4 — soup → sections.csv and links.csv
"""

import pandas as pd
from bs4 import BeautifulSoup
from pipeline.link_classifier import classify_link

# TODO: Sẽ mở comment các dòng import dưới đây sau khi Hùng và Đạt đẩy code lên nhánh main
# from shared.constants import SECTION_COLS
# from pipeline.parser import extract_section_tree

def run_extraction():
    print("Bắt đầu tiến trình trích xuất dữ liệu...")
    
    # Giả lập việc đọc file HTML đã được tải về (do file collector của Đạt thực hiện)
    # with open("data/raw/beautifulsoup_doc.html", "r", encoding="utf-8") as f:
    #     soup = BeautifulSoup(f, "html.parser")
    
    # ---------------------------------------------------------
    # PHẦN 1: TẠO FILE sections.csv
    # ---------------------------------------------------------
    print("1. Đang trích xuất sections...")
    # sections_data = extract_section_tree(soup)
    # df_sections = pd.DataFrame(sections_data, columns=SECTION_COLS)
    # df_sections.to_csv("data/processed/sections.csv", index=False)
    
    # ---------------------------------------------------------
    # PHẦN 2: TẠO FILE links.csv
    # ---------------------------------------------------------
    print("2. Đang trích xuất links...")
    # links_data = []
    # for a_tag in soup.find_all("a"):
    #     href = a_tag.get("href")
    #     link_type = classify_link(href)
    #     
    #     # TODO: Viết logic đi ngược lên DOM (sử dụng .find_parents hoặc .find_previous) 
    #     # để tìm heading (h1, h2, h3) gần nhất chứa thẻ <a> này.
    #     nearest_heading = "Chưa xác định"
    #
    #     links_data.append({
    #         "href": href,
    #         "link_type": link_type,
    #         "section": nearest_heading
    #     })
    #
    # df_links = pd.DataFrame(links_data)
    # df_links.to_csv("data/processed/links.csv", index=False)
    
    print("Hoàn thành trích xuất! Các file đã được lưu vào thư mục data/processed/")

if __name__ == "__main__":
    run_extraction()