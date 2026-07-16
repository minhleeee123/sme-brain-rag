from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import QDRANT_PATH, QDRANT_COLLECTION_NAME

def get_qdrant_client() -> QdrantClient:
    """Khởi tạo và trả về đối tượng kết nối với Qdrant Client (chế độ local storage)"""
    client = QdrantClient(path=QDRANT_PATH)
    return client

def init_collection(vector_size: int):
    """Khởi tạo collection trong Qdrant nếu chưa tồn tại"""
    client = get_qdrant_client()
    
    # Kiểm tra xem collection đã tồn tại chưa
    collections_list = client.get_collections().collections
    exists = any(c.name == QDRANT_COLLECTION_NAME for c in collections_list)
    
    if not exists:
        print(f"Đang tạo Collection mới: '{QDRANT_COLLECTION_NAME}' với kích thước vector {vector_size}...")
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE  # Dùng Cosine Similarity để so sánh
            )
        )
        print("Tạo Collection thành công!")
    else:
        print(f"Collection '{QDRANT_COLLECTION_NAME}' đã tồn tại.")
