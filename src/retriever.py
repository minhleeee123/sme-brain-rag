from sentence_transformers import SentenceTransformer
from qdrant_client.http import models
from src.config import EMBEDDING_MODEL_NAME, QDRANT_COLLECTION_NAME
from src.database import get_qdrant_client

# Tải mô hình embedding dùng chung để mã hóa câu hỏi người dùng
print("Đang tải mô hình Embedding cho bộ truy xuất...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def retrieve_context(query: str, department_filter: str = None, top_k: int = 3) -> list[dict]:
    """
    Truy xuất các đoạn tài liệu liên quan nhất dựa trên câu hỏi và bộ lọc phòng ban.
    
    Args:
        query (str): Câu hỏi của người dùng.
        department_filter (str): Phòng ban được phép truy cập (ví dụ: 'HR', 'Sales', 'Tech').
                                 Nếu None, sẽ tìm kiếm toàn bộ tài liệu công cộng hoặc không giới hạn.
        top_k (int): Số lượng kết quả liên quan nhất muốn lấy.
        
    Returns:
        list[dict]: Danh sách các đoạn văn bản kèm nguồn trích dẫn.
    """
    client = get_qdrant_client()
    
    # 1. Chuyển câu hỏi thành vector
    query_vector = embedding_model.encode(query).tolist()
    
    # 2. Xây dựng bộ lọc (Metadata Filter) nếu có phòng ban cụ thể
    query_filter = None
    if department_filter:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="department",
                    match=models.MatchValue(value=department_filter)
                )
            ]
        )
        
    # 3. Tìm kiếm trong Qdrant sử dụng query_points (API mới của Qdrant v1.11.0+)
    search_results = client.query_points(
        collection_name=QDRANT_COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k
    ).points
    
    # 4. Trích xuất thông tin và trả về
    retrieved_documents = []
    for hit in search_results:
        payload = hit.payload
        retrieved_documents.append({
            "score": hit.score,
            "child_text": payload.get("text"),
            "parent_text": payload.get("parent_text"), # Trích xuất đoạn Cha chứa đầy đủ ngữ cảnh
            "department": payload.get("department"),
            "source_file": payload.get("source_file")
        })
        
    return retrieved_documents

if __name__ == "__main__":
    # Test thử chức năng tìm kiếm
    print("\n--- TEST TRUY XUẤT THỬ NGHIỆM ---")
    
    # Test 1: Tìm kiếm trong phòng ban HR
    print("\nHỏi: 'Chính sách đi muộn thế nào?' với quyền truy cập HR:")
    results = retrieve_context("Chính sách đi muộn thế nào?", department_filter="HR", top_k=2)
    for idx, res in enumerate(results):
        print(f"\n[{idx+1}] Độ tương đồng: {res['score']:.4f} | Nguồn: {res['source_file']}")
        print(f"Ngữ cảnh Cha: {res['parent_text'][:200]}...")
        
    # Test 2: Tìm kiếm trong phòng ban Tech
    print("\nHỏi: 'Cách xử lý khi server sập?' với quyền truy cập Tech:")
    results = retrieve_context("Cách xử lý khi server sập?", department_filter="Tech", top_k=2)
    for idx, res in enumerate(results):
        print(f"\n[{idx+1}] Độ tương đồng: {res['score']:.4f} | Nguồn: {res['source_file']}")
        print(f"Ngữ cảnh Cha: {res['parent_text'][:200]}...")
