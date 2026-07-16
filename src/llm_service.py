import google.generativeai as genai
from src.config import GEMINI_API_KEY
from src.retriever import retrieve_context

# Cấu hình API Key cho Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("CẢNH BÁO: Chưa cấu hình GEMINI_API_KEY trong file .env")

def generate_answer(query: str, department_filter: str = None) -> dict:
    """
    Tìm kiếm tài liệu liên quan và sử dụng Gemini LLM để trả lời câu hỏi.
    
    Args:
        query (str): Câu hỏi của người dùng.
        department_filter (str): Phòng ban được phép truy cập để lọc tài liệu.
        
    Returns:
        dict: Gồm câu trả lời 'answer', nguồn 'sources' và các bước 'steps' trong workflow.
    """
    steps = []
    
    # 1. Bước 1: Mã hóa câu hỏi
    steps.append({
        "title": "1. Mã hóa Câu hỏi (Embedding)",
        "status": "success",
        "details": f"Chuyển câu hỏi '*{query}*' thành vector 384 chiều bằng mô hình `sentence-transformers`."
    })
    
    # 2. Bước 2: Thiết lập bộ lọc phòng ban (RBAC)
    filter_desc = f"`department == '{department_filter}'`" if department_filter else "Admin (Không lọc - Toàn quyền)"
    steps.append({
        "title": "2. Áp dụng Bộ lọc Bảo mật (RBAC)",
        "status": "success",
        "details": f"Kiểm tra quyền hạn người dùng. Điều kiện lọc: {filter_desc}"
    })
    
    # 3. Bước 3: Truy xuất các ngữ cảnh liên quan nhất từ Vector DB
    contexts = retrieve_context(query, department_filter=department_filter, top_k=3)
    
    if not contexts:
        steps.append({
            "title": "3. Kết quả quét Vector DB",
            "status": "warning",
            "details": "Không tìm thấy đoạn văn nào liên quan trong kho dữ liệu được cấp phép."
        })
        return {
            "answer": "Tôi không tìm thấy tài liệu nào liên quan đến câu hỏi của bạn trong cơ sở dữ liệu được cấp quyền.",
            "sources": [],
            "steps": steps
        }
        
    # Xây dựng mô tả chi tiết cho bước truy xuất
    db_details = "Quét Qdrant Vector DB bằng Cosine Similarity và trích xuất Top 3 đoạn khớp nhất:\n\n"
    for idx, ctx in enumerate(contexts):
        db_details += (
            f"**Kết quả {idx+1} [Điểm: {ctx['score']:.4f}]** - File: `{ctx['source_file']}` (Phòng {ctx['department']})\n"
            f"- Đoạn Con (Child - Search): *\"{ctx['child_text'][:120]}...\"*\n"
            f"- Đoạn Cha (Parent - Context): *\"{ctx['parent_text'][:160]}...\"*\n\n"
        )
    steps.append({
        "title": "3. Truy xuất & Ánh xạ Cha-Con (Parent-Child Matching)",
        "status": "success",
        "details": db_details
    })
        
    # 4. Định dạng ngữ cảnh gửi cho LLM
    context_str = ""
    sources = set()
    for idx, ctx in enumerate(contexts):
        source_info = f"{ctx['source_file']} (Phòng {ctx['department']})"
        sources.add(source_info)
        context_str += f"--- ĐOẠN NGỮ CẢNH {idx+1} (Nguồn: {source_info}) ---\n{ctx['parent_text']}\n\n"
        
    # 5. Xây dựng prompt kèm quy tắc ứng xử cho AI (System Instructions)
    system_instruction = (
        "Bạn là trợ lý AI thông minh quản trị tri thức doanh nghiệp của công ty SME-Tech.\n"
        "Nhiệm vụ của bạn là trả lời câu hỏi của nhân viên một cách chính xác, lịch sự, dựa vào các NGỮ CẢNH tài liệu được cung cấp dưới đây.\n"
        "Hãy tuân thủ nghiêm ngặt các quy tắc sau:\n"
        "1. Chỉ trả lời dựa trên thông tin có trong phần 'NGỮ CẢNH ĐƯỢC CUNG CẤP'. Không tự bịa ra thông tin nằm ngoài ngữ cảnh.\n"
        "2. Nếu ngữ cảnh không có câu trả lời, hãy lịch sự trả lời: 'Tôi xin lỗi, thông tin này không có trong tài liệu hướng dẫn được cung cấp.' hoặc tương tự.\n"
        "3. Ở cuối câu trả lời, hãy liệt kê rõ ràng các nguồn tài liệu bạn đã sử dụng để trả lời dạng: 'Tham chiếu: [Tên file] (Phòng [Tên phòng])'.\n"
        "4. Trả lời bằng tiếng Việt chuyên nghiệp, rõ ràng."
    )
    
    user_prompt = f"""NGỮ CẢNH ĐƯỢC CUNG CẤP:
{context_str}

CÂU HỎI CỦA NHÂN VIÊN:
{query}

CÂU TRẢ LỜI CỦA BẠN:"""

    # Ghi lại thông tin Prompt
    prompt_details = (
        f"**Chỉ thị hệ thống (System Instruction):**\n```\n{system_instruction}\n```\n\n"
        f"**Prompt văn bản hoàn chỉnh:**\n```\n{user_prompt[:500]}...\n[còn lại {len(user_prompt)-500} ký tự]\n```"
    )
    steps.append({
        "title": "4. Xây dựng Prompt & Chỉ thị hệ thống",
        "status": "success",
        "details": prompt_details
    })

    try:
        # 6. Gọi mô hình Gemini
        steps.append({
            "title": "5. Gọi LLM (models/gemini-3.1-flash-lite)",
            "status": "success",
            "details": "Gửi Prompt hoàn chỉnh tới Gemini API để tạo câu trả lời tự nhiên dạng hội thoại."
        })
        
        model = genai.GenerativeModel(
            model_name="models/gemini-3.1-flash-lite",
            system_instruction=system_instruction
        )
        
        response = model.generate_content(user_prompt)
        
        return {
            "answer": response.text,
            "sources": list(sources),
            "steps": steps
        }
        
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        steps.append({
            "title": "5. Lỗi API Gemini - Offline Fallback",
            "status": "warning",
            "details": f"Kết nối API thất bại ({e}). Chuyển sang chế độ dự phòng trả về tài liệu thô từ Vector DB."
        })
        
        # Trường hợp không có API key hoặc lỗi mạng, trả về ngữ cảnh thô để người dùng xem
        fallback_answer = (
            "⚠️ Không thể kết nối với Gemini API (Vui lòng kiểm tra lại GEMINI_API_KEY trong file .env).\n\n"
            "Dưới đây là các đoạn thông tin liên quan nhất được tìm thấy từ kho dữ liệu:\n\n"
        )
        for idx, ctx in enumerate(contexts):
            fallback_answer += f"**Nguồn {idx+1}: {ctx['source_file']} ({ctx['department']})**\n{ctx['parent_text']}\n\n"
            
        return {
            "answer": fallback_answer,
            "sources": list(sources),
            "steps": steps
        }

if __name__ == "__main__":
    # Test thử dịch vụ LLM
    print("\n--- TEST GEMINI LLM ANSWER ---")
    query_text = "Thử việc bao lâu và lương thế nào?"
    print(f"Hỏi: '{query_text}' với quyền HR")
    res = generate_answer(query_text, department_filter="HR")
    print("\nĐáp án từ AI:")
    print(res["answer"])
