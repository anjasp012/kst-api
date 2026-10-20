import os
import sys
import logging
from PIL import Image, ImageOps

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.core.config import UPLOADS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def optimize_all_images(uploads_dir: str = UPLOADS_DIR):
    """
    1. Membuat folder uploads/thumbnails jika belum ada.
    2. Membuat versi thumbnail (max 400x400, quality 75) di uploads/thumbnails/{filename}.
    3. Mengompres dan me-resize foto utama di uploads/{filename} (max 1600x1600, quality 82).
    Nama file tetap sama persis sehingga database tidak perlu diubah.
    """
    thumbnails_dir = os.path.join(uploads_dir, "thumbnails")
    os.makedirs(thumbnails_dir, exist_ok=True)

    image_exts = {".jpg", ".jpeg", ".png", ".webp"}
    files = [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
    image_files = [f for f in files if os.path.splitext(f)[1].lower() in image_exts]

    print(f"=== MEMULAI OPTIMASI GAMBAR DI: {uploads_dir} ===")
    print(f"Ditemukan {len(image_files)} file gambar untuk diproses.\n")

    total_orig_bytes = 0
    total_new_bytes = 0
    total_thumb_bytes = 0
    processed_count = 0
    error_count = 0

    for idx, fname in enumerate(image_files, 1):
        src_path = os.path.join(uploads_dir, fname)
        thumb_path = os.path.join(thumbnails_dir, fname)
        ext = os.path.splitext(fname)[1].lower()

        try:
            orig_size = os.path.getsize(src_path)
            total_orig_bytes += orig_size

            # Buka dan load sepenuhnya ke RAM, lalu tutup file handle agar os.replace di Windows tidak Access Denied
            with Image.open(src_path) as img_raw:
                img_raw.load()
                img = ImageOps.exif_transpose(img_raw).copy()

            # Format color mode
            is_jpeg = ext in (".jpg", ".jpeg")
            if is_jpeg and img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")

            # 1. Generate Thumbnail (max 400x400) ke folder thumbnails/
            img_thumb = img.copy()
            img_thumb.thumbnail((400, 400), Image.Resampling.LANCZOS)
            if is_jpeg and img_thumb.mode != "RGB":
                img_thumb = img_thumb.convert("RGB")
            
            img_thumb.save(
                thumb_path,
                format="JPEG" if is_jpeg else (img.format or "PNG"),
                quality=75,
                optimize=True
            )
            thumb_size = os.path.getsize(thumb_path)
            total_thumb_bytes += thumb_size

            # 2. Optimasi Gambar Utama (max 1600x1600) jika lebih besar
            needs_resize = img.width > 1600 or img.height > 1600
            needs_compression = orig_size > (400 * 1024)  # jika > 400 KB

            if needs_resize or needs_compression:
                img_main = img.copy()
                if needs_resize:
                    img_main.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                if is_jpeg and img_main.mode != "RGB":
                    img_main = img_main.convert("RGB")

                temp_path = src_path + ".tmp"
                img_main.save(
                    temp_path,
                    format="JPEG" if is_jpeg else (img.format or "PNG"),
                    quality=82,
                    optimize=True
                )
                # Gantikan file asli (karena handle sudah ditutup, os.replace aman)
                os.replace(temp_path, src_path)

            new_size = os.path.getsize(src_path)
            total_new_bytes += new_size
            processed_count += 1

            if idx % 10 == 0 or idx == len(image_files):
                print(f"[{idx}/{len(image_files)}] Diproses: {fname} (Asli: {orig_size/1024:.0f}KB -> Utama: {new_size/1024:.0f}KB | Thumb: {thumb_size/1024:.0f}KB)")

        except Exception as e:
            error_count += 1
            print(f"[ERROR] Gagal memproses {fname}: {e}")

    orig_mb = total_orig_bytes / (1024 * 1024)
    new_mb = total_new_bytes / (1024 * 1024)
    thumb_mb = total_thumb_bytes / (1024 * 1024)
    saved_mb = orig_mb - (new_mb + thumb_mb)
    pct = (saved_mb / orig_mb * 100) if orig_mb > 0 else 0

    print("\n" + "="*50)
    print("HASIL OPTIMASI SELESAI:")
    print(f"- Total Gambar Diproses: {processed_count}")
    print(f"- Gagal: {error_count}")
    print(f"- Ukuran Asli Sebelumnya: {orig_mb:.2f} MB")
    print(f"- Ukuran Foto Utama (1600px): {new_mb:.2f} MB")
    print(f"- Ukuran Folder Thumbnails (400px): {thumb_mb:.2f} MB")
    print(f"- Total Ukuran Baru: {new_mb + thumb_mb:.2f} MB")
    print(f"- Penghematan Bersih: {saved_mb:.2f} MB ({pct:.1f}% LEBIH RINGAN!)")
    print("="*50)


if __name__ == "__main__":
    optimize_all_images()
