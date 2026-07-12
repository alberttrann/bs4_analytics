"""
pipeline/link_classifier.py
Owner: Phuc (C)
Task : F4 — classify_link(href) → one of 5 LINK_TYPES
"""

import re

def classify_link(href: str) -> str:
    """
    Phân loại href của thẻ <a> thành 1 trong 5 loại cố định.
    """
    # 1. Check for empty or invalid links
    if not href or not isinstance(href, str):
        return "empty_or_invalid"
    
    href = href.strip()
    if href == "":
        return "empty_or_invalid"

    # 2. Check for image links (.png, .jpg, .jpeg, .gif, .svg)
    # Dùng regex để tìm phần đuôi mở rộng của file ảnh
    if re.search(r'\.(png|jpe?g|gif|svg)$', href, re.IGNORECASE):
        return "image_link"

    # 3. Check for internal anchor links (bắt đầu bằng dấu #)
    if href.startswith("#"):
        return "internal_anchor"

    # 4. Check for documentation links (chứa domain của doc là crummy.com)
    if "crummy.com" in href:
        return "documentation_link"

    # 5. Everything else is an external link
    return "external_link"

# --- Khối code này giúp bạn test nhanh ngay trên terminal ---
if __name__ == "__main__":
    test_links = [
        None,                                       # empty_or_invalid
        "",                                         # empty_or_invalid
        "#quick-start",                             # internal_anchor
        "https://www.crummy.com/software/",         # documentation_link
        "https://github.com/alberttrann",           # external_link
        "images/bs4_logo.png",                      # image_link
        "http://python.org"                         # external_link
    ]
    
    for link in test_links:
        print(f"'{link}' -> {classify_link(link)}")