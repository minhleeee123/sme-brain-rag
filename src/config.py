import os
from pathlib import Path
from dotenv import load_dotenv

# Tìm đường dẫn gốc của dự án (thư mục chứa src)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load file .env từ thư mục gốc
load_dotenv(BASE_DIR / ".env")

# Cấu hình API Key cho Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Cấu hình Qdrant
QDRANT_PATH = os.getenv("QDRANT_PATH", str(BASE_DIR / "qdrant_db"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "sme_knowledge_base")

# Cấu hình mô hình Embedding
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Đường dẫn thư mục dữ liệu
DATA_DIR = BASE_DIR / "data"
