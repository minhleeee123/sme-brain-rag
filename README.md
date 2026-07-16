# SME-Brain 🧠 - Trợ lý Tri thức Doanh nghiệp AI-Native cho SME

Dự án **SME-Brain** được xây dựng để giải quyết bài toán quản trị tri thức nội bộ và tối ưu hóa năng suất vận hành cho các doanh nghiệp vừa và nhỏ (SME) trong khuôn khổ cuộc thi **Vietnam AI Innovation Challenge 2026**.

Dự án áp dụng kỹ thuật **RAG Nâng cao (Advanced RAG)** với các tính năng nổi bật:
1. **Parent-Child Chunking:** Cắt nhỏ tài liệu để tìm kiếm cực kỳ chính xác (Child), nhưng trả về ngữ cảnh rộng (Parent) cho LLM đọc để câu trả lời có tính logic cao.
2. **Metadata Filtering (RBAC):** Mô phỏng phân quyền truy xuất dữ liệu cấp doanh nghiệp. Nhân viên phòng nào chỉ được tìm kiếm và trả lời dựa trên tài liệu phòng đó (HR, Sales, Tech).
3. **Google Gemini LLM Integration:** Tích hợp mô hình `gemini-1.5-flash` để sinh câu trả lời nhanh chóng và chính xác.
4. **Qdrant Vector DB (Local Mode):** Lưu trữ vector cơ sở dữ liệu ngay tại thư mục cục bộ của máy tính, không cần cài đặt Docker.

---

## 🛠️ Hướng dẫn cài đặt và chạy ứng dụng

### Bước 1: Sao chép tệp cấu hình môi trường
Sao chép file `.env.example` thành `.env` ở thư mục gốc dự án:
```bash
cp .env.example .env
```
Sau đó, mở file `.env` ra và điền khóa API của bạn vào dòng:
```env
GEMINI_API_KEY=khóa_api_gemini_của_bạn_ở_đây
```

*(Nếu không có API Key, hệ thống vẫn sẽ hoạt động ở chế độ ngoại tuyến (Offline Fallback) bằng cách trả về ngữ cảnh thô tìm được từ Vector DB).*

### Bước 2: Cài đặt các thư viện Python
Mở Terminal và chạy lệnh sau để cài đặt toàn bộ các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

### Bước 3: Nạp dữ liệu vào Vector Database (Cách 1)
Bạn có thể chạy trực tiếp tập lệnh Python để đọc tài liệu trong thư mục `data/` và nạp vào DB:
```bash
python -m src.ingestion
```

*(Hoặc bạn có thể bấm nút **"Nạp/Cập nhật dữ liệu vào DB"** trực tiếp trên giao diện Streamlit ở Bước 4).*

### Bước 4: Chạy giao diện Web (Streamlit)
Chạy lệnh sau để khởi chạy ứng dụng web:
```bash
streamlit run src/app.py
```

Sau khi chạy lệnh, Streamlit sẽ hiển thị một đường dẫn cục bộ (ví dụ: `http://localhost:8501`). Hãy click vào đường dẫn đó hoặc mở trình duyệt web để bắt đầu trải nghiệm!

---

## 📂 Cấu trúc thư mục dự án
* `data/`: Chứa các tài liệu thô mẫu (HR, Sales, Tech). Bạn có thể thêm bất kỳ tệp tin `.txt` nào vào đây để mở rộng kho tri thức.
* `src/config.py`: Trình nạp cấu hình và biến môi trường.
* `src/database.py`: Thiết lập kết nối cơ sở dữ liệu Vector Qdrant.
* `src/ingestion.py`: Pipeline tiền xử lý văn bản, phân chia Parent-Child chunking, tạo vector embedding.
* `src/retriever.py`: Thực hiện tìm kiếm vector kèm bộ lọc phân quyền phòng ban.
* `src/llm_service.py`: Tích hợp Google Gemini để sinh câu trả lời và trích dẫn nguồn.
* `src/app.py`: Giao diện ứng dụng chat trực quan bằng Streamlit.
