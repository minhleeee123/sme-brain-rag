import streamlit as st
import os
from pathlib import Path
from src.ingestion import run_ingestion
from src.llm_service import generate_answer
from src.config import BASE_DIR

# 1. Cấu hình giao diện Streamlit (phải ở đầu trang)
st.set_page_config(
    page_title="SME-Brain - Trợ lý tri thức doanh nghiệp",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Định nghĩa Custom CSS để UI có tính thẩm mỹ cao
st.markdown("""
<style>
    .main {
        background-color: #f9fafd;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    .role-badge {
        padding: 6px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 15px;
        text-align: center;
    }
    .role-hr { background-color: #ffe6e6; color: #cc0000; border: 1px solid #ffa3a3; }
    .role-sales { background-color: #e6f7ff; color: #0050b3; border: 1px solid #91d5ff; }
    .role-tech { background-color: #f6ffed; color: #389e0d; border: 1px solid #b7eb8f; }
    .role-admin { background-color: #f9f0ff; color: #531dab; border: 1px solid #d3adf7; }
</style>
""", unsafe_allow_html=True)

# ----------------- THANH BÊN (SIDEBAR) -----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1786/1786971.png", width=70)
    st.title("SME-Brain v1.0")
    st.caption("Hệ thống quản trị tri thức & bảo mật thông tin AI-Native cho SME.")
    st.write("---")
    
    # Thiết lập bộ chọn quyền hạn người dùng (mô phỏng RBAC)
    st.subheader("🔑 Vai trò người dùng")
    role_options = {
        "Hành chính / Nhân sự (HR)": "HR",
        "Kinh doanh / CSKH (Sales)": "Sales",
        "Kỹ thuật / DevOps (Tech)": "Tech",
        "Quản trị viên (Admin - Toàn quyền)": None
    }
    selected_role_label = st.selectbox(
        "Chọn vị trí/phòng ban của bạn:",
        options=list(role_options.keys()),
        index=3  # Mặc định là Admin để dễ test
    )
    current_dept = role_options[selected_role_label]
    
    # Hiển thị Badge phòng ban hiện tại để chỉ rõ vai trò bảo mật
    if current_dept == "HR":
        st.markdown('<span class="role-badge role-hr">Phòng ban hiện tại: HR</span>', unsafe_allow_html=True)
    elif current_dept == "Sales":
        st.markdown('<span class="role-badge role-sales">Phòng ban hiện tại: Sales</span>', unsafe_allow_html=True)
    elif current_dept == "Tech":
        st.markdown('<span class="role-badge role-tech">Phòng ban hiện tại: Tech</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="role-badge role-admin">Vai trò hiện tại: Admin (Toàn quyền)</span>', unsafe_allow_html=True)
        
    st.write("---")
    
    # Quản lý nạp dữ liệu vào Vector DB
    st.subheader("📂 Quản lý Dữ liệu")
    st.write("Đồng bộ hóa các thay đổi tài liệu thô trong thư mục `data/` vào cơ sở dữ liệu Vector.")
    
    if st.button("🔄 Nạp/Cập nhật dữ liệu vào DB", type="primary"):
        with st.spinner("Đang phân tích tài liệu và sinh vector..."):
            try:
                run_ingestion()
                st.success("Đã đồng bộ dữ liệu vào Qdrant thành công!")
                st.toast("Cơ sở dữ liệu đã cập nhật xong!", icon="✅")
            except Exception as e:
                st.error(f"Lỗi nạp dữ liệu: {e}")
                
    st.write("---")
    st.caption("VAIC 2026 - SME Productivity Track")

# ----------------- KHU VỰC CHÁT CHÍNH (MAIN CHAT) -----------------
st.title("🧠 SME-Brain: Trợ lý Tri thức Doanh nghiệp")
st.write(
    "Hệ thống hỏi đáp thông tin nội bộ thông minh áp dụng kỹ thuật RAG nâng cao (Parent-Child) "
    "và phân quyền bảo mật cấp thư mục."
)

# Cảnh báo nếu thư mục DB chưa tồn tại
db_path = Path(BASE_DIR / "qdrant_db")
if not db_path.exists() or not os.listdir(db_path):
    st.warning("⚠️ Cơ sở dữ liệu Vector đang trống! Vui lòng nhấp vào nút **'Nạp/Cập nhật dữ liệu vào DB'** ở thanh menu bên trái trước khi bắt đầu.")

# Khởi tạo hoặc duy trì lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Hiển thị Nguồn trích dẫn
        if message.get("sources"):
            with st.expander("📚 Xem nguồn trích dẫn"):
                for src in message["sources"]:
                    st.write(f"- {src}")
                    
        # Hiển thị nhật ký RAG chi tiết
        if message.get("steps"):
            with st.expander("⚙️ Nhật ký RAG Runtime Workflow (Chi tiết quá trình xử lý)"):
                for step in message["steps"]:
                    icon = "✅" if step.get("status") == "success" else "⚠️"
                    st.markdown(f"##### {icon} {step.get('title')}")
                    st.markdown(step.get("details", ""))
                    st.markdown("---")

# Xử lý tin nhắn mới từ người dùng
if prompt := st.chat_input("Nhập câu hỏi tra cứu chính sách..."):
    # 1. Hiển thị câu hỏi của người dùng
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Xử lý RAG và hiển thị câu trả lời của AI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Tạo hiệu ứng tiến trình RAG theo thời gian thực (Real-time Status Log)
        with st.status("🔍 Đang chạy RAG Runtime Workflow...", expanded=True) as status:
            st.write("🔄 1. Đang khởi tạo kết nối và mã hóa câu hỏi...")
            
            # Gọi API RAG sinh câu trả lời
            response = generate_answer(prompt, department_filter=current_dept)
            
            # Ghi lại trạng thái các bước đã chạy
            for step in response.get("steps", []):
                status.write(f"✓ {step.get('title')}")
                
            status.update(label="RAG Workflow hoàn tất!", state="complete", expanded=False)
            
        # Hiển thị câu trả lời của LLM
        message_placeholder.markdown(response.get("answer", ""))
        
        # Hiển thị nguồn trích dẫn tài liệu
        if response.get("sources"):
            with st.expander("📚 Xem nguồn trích dẫn"):
                for src in response["sources"]:
                    st.write(f"- {src}")
                    
        # Hiển thị nhật ký RAG chi tiết cho câu hỏi vừa rồi
        if response.get("steps"):
            with st.expander("⚙️ Nhật ký RAG Runtime Workflow (Chi tiết quá trình xử lý)"):
                for step in response["steps"]:
                    icon = "✅" if step.get("status") == "success" else "⚠️"
                    st.markdown(f"##### {icon} {step.get('title')}")
                    st.markdown(step.get("details", ""))
                    st.markdown("---")
                        
        # Lưu câu trả lời vào lịch sử chat
        st.session_state.messages.append({
            "role": "assistant",
            "content": response.get("answer", ""),
            "sources": response.get("sources", []),
            "steps": response.get("steps", [])
        })
