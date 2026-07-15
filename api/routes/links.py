"""
api/routes/links.py
Owner: Phuc (C)
Task : GET /links (filtered), GET /links/stats
"""

from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd
from api.services.data_service import load_links
from shared.schemas import LinkModel

# Khởi tạo router
router = APIRouter(tags=["Links"])

@router.get("", response_model=list[LinkModel])
def get_all_links(
    link_type: Optional[str] = Query(None, description="Lọc theo loại link (vd: external_link)"),
    section: Optional[str] = Query(None, description="Lọc theo tên phần (section)")
):
    """Lấy danh sách các liên kết, hỗ trợ lọc theo loại và section."""
    df_links = load_links()
    
    # Lọc dữ liệu nếu user truyền tham số
    if link_type:
        df_links = df_links[df_links["link_type"] == link_type]
    if section:
        df_links = df_links[df_links["section"] == section]
        
    # FastAPI sẽ tự động validate dict này với LinkModel trong shared/schemas.py
    return df_links.to_dict(orient="records")

@router.get("/stats")
def get_link_stats():
    """Trả về thống kê số lượng của 5 loại link để vẽ biểu đồ tròn."""
    df_links = load_links()
    
    # Đếm số lượng mỗi loại
    counts = df_links["link_type"].value_counts().to_dict()
    
    # Đảm bảo trả về đủ 5 loại theo chuẩn, kể cả khi số lượng = 0
    all_types = [
        "internal_anchor", 
        "external_link", 
        "documentation_link", 
        "image_link", 
        "empty_or_invalid"
    ]
    
    stats = {link_t: counts.get(link_t, 0) for link_t in all_types}
    return stats