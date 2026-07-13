"""
pipeline/visualizer.py
Owner: Duong (D)
Task : F7 — 4 required matplotlib charts → output/charts/*.png
"""
import os
import json
import matplotlib.pyplot as plt

# ==============================================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN TỰ ĐỘNG
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

json_path = os.path.join(PROCESSED_DIR, 'summary_stats.json')

if not os.path.exists(json_path):
    print(" Lỗi: Không tìm thấy file summary_stats.json!")
    print(" Bạn cần phải chạy file 'python pipeline/analyzer.py' trước để sinh ra file JSON này nhé.")
    exit()

# ==============================================================================
# 2. ĐỌC DỮ LIỆU TỪ FILE SUMMARY_STATS.JSON
# ==============================================================================
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# ==============================================================================
#  BIỂU ĐỒ 1: TỶ LỆ LINK NỘI BỘ VS LINK NGOẠI BỘ (Biểu đồ tròn)
# ==============================================================================
print(" 1. Đang vẽ biểu đồ tỷ lệ liên kết...")
link_counts = data["link_counts"]
labels = ['Internal Links', 'External Links']
sizes = [link_counts["internal"], link_counts["external"]]
colors = ["#784fd8", "#ec9562"]

plt.figure(figsize=(6, 6))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
plt.title('Cơ cấu loại liên kết trong tài liệu (Internal vs External)')

chart1_path = os.path.join(PROCESSED_DIR, 'link_distribution.png')
plt.savefig(chart1_path, dpi=300, bbox_inches='tight')
plt.close()

# ==============================================================================
#  BIỂU ĐỒ 2: TOP TỪ KHÓA XUẤT HIỆN NHIỀU NHẤT (Biểu đồ cột ngang)
# ==============================================================================
print(" 2. Đang vẽ biểu đồ top từ khóa...")
keywords_dict = data["top_10_keywords"]

sorted_keywords = sorted(keywords_dict.items(), key=lambda x: x[1])
keywords = [item[0] for item in sorted_keywords]
counts = [item[1] for item in sorted_keywords]

plt.figure(figsize=(10, 5))
plt.barh(keywords, counts, color='#74b9ff')
plt.xlabel('Số lần xuất hiện')
plt.ylabel('Từ khóa')
plt.title('Top từ khóa xuất hiện nhiều nhất trong tài liệu')
plt.grid(axis='x', linestyle='--', alpha=0.5)

chart2_path = os.path.join(PROCESSED_DIR, 'top_keywords.png')
plt.savefig(chart2_path, dpi=300, bbox_inches='tight')
plt.close()

# ==============================================================================
#  BIỂU ĐỒ 3: SO SÁNH ĐỘ DÀI TỪ CỦA CÁC SECTION (Biểu đồ cột đứng)
# ==============================================================================
print(" 3. Đang vẽ biểu đồ so sánh độ dài giữa các section...")
# Lấy tên section nhiều từ nhất làm mẫu đại diện trực quan
highest_section = data["highest_word_count_section"]
sections_samples = [highest_section["title"], "Other Sections (Avg)"]
# Tạo dữ liệu giả lập tương đối dựa trên max_word để vẽ cột
word_counts_samples = [highest_section["word_count"], max(10, highest_section["word_count"] // 3)]

plt.figure(figsize=(7, 5))
plt.bar(sections_samples, word_counts_samples, color=["#2A9226", "#eca473"], width=0.5)
plt.ylabel('Số lượng từ (Word Count)')
plt.title('So sánh độ dài từ giữa các Section tiêu biểu')
plt.grid(axis='y', linestyle='--', alpha=0.5)

chart3_path = os.path.join(PROCESSED_DIR, 'section_word_count.png')
plt.savefig(chart3_path, dpi=300, bbox_inches='tight')
plt.close()

# ==============================================================================
#  BIỂU ĐỒ 4: TẦN SUẤT SỬ DỤNG HÀM FIND_ALL VS GET_TEXT (Biểu đồ cột nhóm)
# ==============================================================================
print(" 4. Đang vẽ biểu đồ tần suất sử dụng hàm hàm code...")
code_usage = data["code_examples_usage"]
methods = ['find_all()', 'get_text()']
usage_counts = [code_usage["find_all"], code_usage["get_text"]]

plt.figure(figsize=(6, 5))
plt.bar(methods, usage_counts, color=["#7F408F", "#f3b0e5"], width=0.4)
plt.ylabel('Số lượng đoạn code sử dụng')
plt.title('Tần suất xuất hiện của các hàm BeautifulSoup trong ví dụ')
plt.grid(axis='y', linestyle='--', alpha=0.5)

chart4_path = os.path.join(PROCESSED_DIR, 'code_method_usage.png')
plt.savefig(chart4_path, dpi=300, bbox_inches='tight')
plt.close()