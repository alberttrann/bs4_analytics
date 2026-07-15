"""
pipeline/analyzer.py
Owner: Duong (D)
Task : F6 — 10 analytics questions using Pandas/NumPy → summary_stats.json
"""
import os
import json
import pandas as pd
import numpy as np

# ==============================================================================
# CẤU HÌNH ĐƯỜNG DẪN TỰ ĐỘNG
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

os.makedirs(PROCESSED_DIR, exist_ok=True)

sections_path = os.path.join(PROCESSED_DIR, 'sections.csv')
links_path = os.path.join(PROCESSED_DIR, 'links.csv')
code_path = os.path.join(PROCESSED_DIR, 'code_examples.csv')
json_path = os.path.join(PROCESSED_DIR, 'summary_stats.json')

# --- TỰ ĐỘNG SINH DỮ LIỆU GIẢ LẬP (MOCK DATA) ---
if not os.path.exists(sections_path) or os.stat(sections_path).st_size < 10:
    with open(sections_path, 'w', encoding='utf-8') as f:
        f.write("section_id,section_level,section_title,section_text,word_count,code_block_count,link_count\n")
        f.write("1,1,BeautifulSoup Documentation,This is the official documentation for Beautiful Soup.,7,1,2\n")
        f.write("2,2,Quick Start,Let us look at a quick code sample now with soup.find_all.,8,3,1\n")

if not os.path.exists(links_path) or os.stat(links_path).st_size < 10:
    with open(links_path, 'w', encoding='utf-8') as f:
        f.write("link_text,href,link_type,section_title\n")
        f.write("BeautifulSoup Official,https://www.crummy.com/software/BeautifulSoup/bs4/doc/,external_link,BeautifulSoup Documentation\n")
        f.write("Quick Start,#quick-start,internal_anchor,BeautifulSoup Documentation\n")
        f.write("Link lỗi,,empty_or_invalid,Troubleshooting\n")

if not os.path.exists(code_path) or os.stat(code_path).st_size < 10:
    with open(code_path, 'w', encoding='utf-8') as f:
        f.write("example_id,section_title,code_text,line_count,contains_find_all,contains_find,contains_select,contains_requests,contains_get_text\n")
        f.write("1,BeautifulSoup Documentation,soup = BeautifulSoup(html_doc),3,False,False,False,False,False\n")
        f.write("2,Quick Start,soup.find_all('a'),2,True,True,False,False,False\n")
        f.write("3,Kinds of objects,tag.get_text(),2,False,False,True,False,True\n")

# --- ĐỌC DỮ LIỆU ---
df_sections = pd.read_csv(sections_path)
df_links = pd.read_csv(links_path)
df_code = pd.read_csv(code_path)


# ==============================================================================
# FEATURE 6: DOCUMENTATION ANALYTICS
# ==============================================================================
print("==================================================")
print("PERFORMING FEATURE 6: DOCUMENTATION ANALYTICS")
print("==================================================")

num_sections = len(df_sections)
print(f"1. Số lượng sections: {num_sections}")

max_word_idx = df_sections['word_count'].idxmax()
best_word_section = df_sections.loc[max_word_idx, 'section_title']
max_words = df_sections.loc[max_word_idx, 'word_count']
print(f"2. Section nhiều từ nhất: '{best_word_section}' ({max_words} từ)")

max_code_idx = df_sections['code_block_count'].idxmax()
best_code_section = df_sections.loc[max_code_idx, 'section_title']
max_codes = df_sections.loc[max_code_idx, 'code_block_count']
print(f"3. Section nhiều code ví dụ nhất: '{best_code_section}' ({max_codes} đoạn)")

max_link_idx = df_sections['link_count'].idxmax()
best_link_section = df_sections.loc[max_link_idx, 'section_title']
max_links = df_sections.loc[max_link_idx, 'link_count']
print(f"4. Section nhiều liên kết nhất: '{best_link_section}' ({max_links} links)")

all_text = " ".join(df_sections['section_text'].dropna().astype(str)).lower()
words = pd.Series(all_text.replace('.', ' ').replace(',', ' ').split())
tech_keywords = words[words.str.len() > 3].value_counts().head(10)
print("\n5. Top 10 từ khóa xuất hiện nhiều nhất:")
print(tech_keywords.to_string())

link_counts = df_links['link_type'].value_counts()
internal_count = link_counts.get('internal_anchor', 0)
external_count = link_counts.get('external_link', 0)
print(f"\n6. Link nội bộ: {internal_count} | Link ngoại bộ: {external_count}")

count_find_all = df_code['contains_find_all'].sum()
print(f"7. Số code ví dụ dùng find_all(): {count_find_all}")

count_get_text = df_code['contains_get_text'].sum()
print(f"8. Số code ví dụ dùng get_text(): {count_get_text}")

avg_lines = df_code['line_count'].mean()
max_lines = df_code['line_count'].max()
print(f"9. Số dòng code trung bình: {avg_lines:.2f} (Dài nhất: {max_lines})")

invalid_count = link_counts.get('empty_or_invalid', 0)
total_links = len(df_links)
invalid_pct = (invalid_count / total_links) * 100 if total_links > 0 else 0
print(f"10. Tỷ lệ link lỗi: {invalid_pct:.2f}%")

# Xuất JSON cho Feature 6
summary_data = {
    "total_sections": int(num_sections),
    "highest_word_count_section": {"title": str(best_word_section), "word_count": int(max_words)},
    "most_code_examples_section": {"title": str(best_code_section), "code_block_count": int(max_codes)},
    "most_links_section": {"title": str(best_link_section), "link_count": int(max_links)},
    "top_10_keywords": tech_keywords.to_dict(),
    "link_counts": {"internal": int(internal_count), "external": int(external_count)},
    "code_examples_usage": {"find_all": int(count_find_all), "get_text": int(count_get_text)},
    "additional_metrics": {"avg_code_lines": float(avg_lines), "max_code_lines": int(max_lines), "invalid_links_pct": float(invalid_pct)}
}
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(summary_data, f, ensure_ascii=False, indent=4)
print(f" Đã xuất thống kê JSON tại: {json_path}\n")


# ==============================================================================
# FEATURE 7: DOCUMENTATION SEARCH & FILTERING
# ==============================================================================
print("==================================================")
print(" PERFORMING FEATURE 7: SEARCH & FILTERING")
print("==================================================")

def search_sections_by_keyword(df, keyword):
    """Tìm kiếm các section có nội dung chứa từ khóa (không phân biệt hoa thường)"""
    result = df[df['section_text'].str.contains(keyword, case=False, na=False)]
    return result[['section_title', 'word_count']]

def filter_links_by_type(df, link_type):
    """Lọc ra các liên kết theo loại chỉ định"""
    return df[df['link_type'] == link_type][['link_text', 'href']]

def filter_complex_code_examples(df, min_lines=3):
    """Lọc các đoạn code phức tạp có số dòng lớn hơn hoặc bằng mức chỉ định"""
    return df[df['line_count'] >= min_lines][['section_title', 'line_count']]

# --- CHẠY THỬ NGHIỆM CÁC HÀM CỦA FEATURE 7 ---

# 1. Test thử tìm kiếm từ khóa 'soup'
keyword_test = "soup"
search_res = search_sections_by_keyword(df_sections, keyword_test)
print(f"1. Kết quả tìm kiếm từ khóa '{keyword_test}' trong các section:")
print(search_res.to_string(index=False) if not search_res.empty else " Không tìm thấy.")

# 2. Test thử lọc liên kết ngoại bộ (external_link)
link_type_test = "external_link"
links_res = filter_links_by_type(df_links, link_type_test)
print(f"\n2. Các liên kết thuộc loại '{link_type_test}':")
print(links_res.to_string(index=False) if not links_res.empty else " Không có liên kết nào thỏa mãn.")

# 3. Test thử lọc code ví dụ có từ 3 dòng trở lên
min_lines_test = 3
code_res = filter_complex_code_examples(df_code, min_lines=min_lines_test)
print(f"\n3. Các đoạn code dài và phức tạp (>= {min_lines_test} dòng):")
print(code_res.to_string(index=False) if not code_res.empty else " Không có đoạn code nào đủ dài.")
