from typing import Optional, List
from app.core.config import settings


def build_full_url(url: Optional[str]) -> Optional[str]:
    """
    Mengubah path gambar lokal/relatif menjadi Full Absolute URL.
    Contoh:
      - '/uploads/abc.jpg' -> 'http://127.0.0.1:8000/uploads/abc.jpg'
      - 'uploads/abc.jpg'  -> 'http://127.0.0.1:8000/uploads/abc.jpg'
      - 'abc.jpg'          -> 'http://127.0.0.1:8000/uploads/abc.jpg'
      - 'http://...'       -> 'http://...' (sudah absolute)
      - 'sprout'           -> 'sprout' (icon identifier dipertahankan)
    """
    if not url:
        return None
    url = str(url).strip()
    if not url:
        return None
        
    # Bersihkan sisa URL localhost lama dari database jika ada
    for prefix in (
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "https://127.0.0.1:8000",
        "https://localhost:8000",
        "https://127.0.0.1:8000",
        "https://localhost:8000",
    ):
        if url.startswith(prefix):
            url = url[len(prefix):]
            break

    if url.startswith("http://") or url.startswith("https://") or url.startswith("data:"):
        return url
        
    backend_url = getattr(settings, "BACKEND_URL", "").rstrip("/")
    
    if url.startswith("/uploads/"):
        return f"{backend_url}{url}" if backend_url else url
        
    if url.startswith("uploads/"):
        return f"{backend_url}/{url}" if backend_url else f"/{url}"
        
    common_extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp", ".ico", ".mp4", ".pdf")
    if any(url.lower().endswith(ext) for ext in common_extensions):
        clean_name = url.lstrip("/")
        return f"{backend_url}/uploads/{clean_name}" if backend_url else f"/uploads/{clean_name}"
        
    if url.startswith("/"):
        return f"{backend_url}{url}" if backend_url else url
        
    return url


def build_full_url_list(urls: Optional[List[str]]) -> List[str]:
    """
    Mengubah list URL/path menjadi list Full Absolute URL.
    """
    if not urls:
        return []
    return [build_full_url(u) for u in urls if u]

