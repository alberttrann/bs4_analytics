"""
api/routes/analytics.py
Owner: Duong (D)
Task : GET /analytics/summary, /charts, /link-types
"""
import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

# Khởi tạo APIRouter cho module analytics
router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Định nghĩa đường dẫn động tới thư mục chứa dữ liệu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
json_path = os.path.join(PROCESSED_DIR, 'summary_stats.json')

def load_summary_data():
    """Hàm bổ trợ để đọc file JSON một cách an toàn"""
    if not os.path.exists(json_path):
        raise HTTPException(
            status_code=404, 
            detail="Không tìm thấy dữ liệu thống kê. Vui lòng chạy pipeline phân tích trước!"
        )
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ==============================================================================
# 1. GET /analytics/summary
# ==============================================================================
@router.get("/summary")
async def get_summary():
    """Trả về toàn bộ nội dung thống kê chi tiết từ file JSON"""
    data = load_summary_data()
    return data

# ==============================================================================
# 2. GET /analytics/link-types
# ==============================================================================
@router.get("/link-types")
async def get_link_types():
    """Trả về riêng số liệu thống kê về các loại liên kết (internal vs external)"""
    data = load_summary_data()
    return {
        "status": "success",
        "link_counts": data.get("link_counts", {}),
        "invalid_links_pct": data.get("additional_metrics", {}).get("invalid_links_pct", 0)
    }

# ==============================================================================
# 3. GET /analytics/charts
# ==============================================================================
@router.get("/charts")
async def get_charts(chart_name: str = "link_distribution"):
    # Đảm bảo tên file truyền vào hợp lệ, tránh lỗi bảo mật đường dẫn
    valid_charts = ["link_distribution", "top_keywords", "section_word_count", "code_method_usage"]
    
    if chart_name not in valid_charts:
        raise HTTPException(
            status_code=400, 
            detail=f"Tên biểu đồ không hợp lệ. Vui lòng chọn một trong các loại: {', '.join(valid_charts)}"
        )
        
    chart_file_path = os.path.join(PROCESSED_DIR, f"{chart_name}.png")
    
    if not os.path.exists(chart_file_path):
        raise HTTPException(
            status_code=404, 
            detail=f"Không tìm thấy file ảnh biểu đồ '{chart_name}.png'. Hãy chạy file visualizer.py trước!"
        )
        
    # Trả về file ảnh trực tiếp để hiển thị trên trình duyệt/giao diện web
    return FileResponse(chart_file_path, media_type="image/png")