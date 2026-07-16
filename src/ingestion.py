import os
import uuid
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client.http import models

from src.config import DATA_DIR, EMBEDDING_MODEL_NAME, QDRANT_COLLECTION_NAME
from src.database import get_qdrant_client, init_collection

# 1. Tải mô hình embedding dùng chung
print(f"Đang tải mô hình Embedding: {EMBEDDING_MODEL_NAME}...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
# Lấy kích thước vector đầu ra của mô hình
VECTOR_SIZE = embedding_model.get_sentence_embedding_dimension()
print(f"Mô hình tải xong! Kích thước vector đầu ra: {VECTOR_SIZE}")

def split_into_parent_chunks(text: str, max_chars: int = 1000) -> list[str]:
    """Chia văn bản thành các đoạn lớn (Parent Chunks) dựa trên các đoạn văn (paragraphs)"""
    paragraphs = text.split("\n\n")
    parent_chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Nếu paragraph quá dài, tự động đưa vào làm một chunk độc lập
        if len(para) > max_chars:
            if current_chunk:
                parent_chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0
            parent_chunks.append(para)
            continue
            
        if current_length + len(para) > max_chars:
            parent_chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_length = len(para)
        else:
            current_chunk.append(para)
            current_length += len(para) + 2  # +2 cho \n\n
            
    if current_chunk:
        parent_chunks.append("\n\n".join(current_chunk))
        
    return parent_chunks

def split_parent_into_child_chunks(parent_text: str, chunk_size: int = 250, overlap: int = 50) -> list[str]:
    """Chia một Parent Chunk lớn thành các Child Chunks nhỏ hơn bằng phương pháp sliding window"""
    words = parent_text.split()
    child_chunks = []
    
    if len(words) <= chunk_size:
        return [parent_text]
        
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        child_chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
        
    return child_chunks

def run_ingestion():
    """Chạy toàn bộ pipeline nạp dữ liệu: quét file, chia chunk, tạo vector & lưu vào Qdrant"""
    # Khởi tạo collection trong Qdrant
    init_collection(VECTOR_SIZE)
    client = get_qdrant_client()
    
    points = []
    
    # Duyệt qua các thư mục phòng ban
    for path in DATA_DIR.rglob("*.txt"):
        department = path.parent.name  # HR, Sales, hoặc Tech
        file_name = path.name
        print(f"\nĐang xử lý file: {file_name} (Thuộc phòng ban: {department})")
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Bước 1: Chia tài liệu thành các Parent Chunks (ngữ cảnh rộng)
        parent_chunks = split_into_parent_chunks(content, max_chars=800)
        print(f"- Chia được {len(parent_chunks)} Parent Chunks.")
        
        for parent_idx, parent_text in enumerate(parent_chunks):
            # Bước 2: Chia mỗi Parent Chunk thành các Child Chunks (tìm kiếm chính xác)
            child_chunks = split_parent_into_child_chunks(parent_text, chunk_size=100, overlap=20)
            
            # Tạo vector embedding cho các Child Chunks
            child_embeddings = embedding_model.encode(child_chunks)
            
            for child_idx, (child_text, vector) in enumerate(zip(child_chunks, child_embeddings)):
                # Tạo một ID ngẫu nhiên duy nhất cho mỗi điểm trong Vector DB
                point_id = str(uuid.uuid4())
                
                # Payload lưu trữ thông tin thực tế cùng với Vector
                payload = {
                    "text": child_text,                 # Text con dùng để hybrid search / hiển thị nháp
                    "parent_text": parent_text,         # Text cha dùng làm ngữ cảnh đầy đủ gửi LLM
                    "department": department,           # Phân quyền phòng ban
                    "source_file": file_name,           # Nguồn gốc tệp tin
                    "parent_index": parent_idx,
                    "child_index": child_idx
                }
                
                # Tạo Point để đưa vào Qdrant
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=vector.tolist(),
                        payload=payload
                    )
                )
                
    # Lưu toàn bộ points vào Qdrant Vector DB
    if points:
        print(f"\nĐang lưu {len(points)} vector vào Qdrant...")
        client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            wait=True,
            points=points
        )
        print("Đã lưu dữ liệu thành công vào cơ sở dữ liệu vector!")
    else:
        print("Không tìm thấy dữ liệu nào để nạp.")

if __name__ == "__main__":
    run_ingestion()
