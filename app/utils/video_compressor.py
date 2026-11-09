import os
import sys
import re
import glob
import shutil
import logging
import subprocess
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger("video_compressor")

# Cache ffmpeg command path once resolved
_CACHED_FFMPEG_CMD: Optional[str] = None


def get_resolution_label(w: int, h: int) -> str:
    """Mengubah dimensi pixel ke label resolusi (4K, 2K, 1080p, 720p, 480p, 360p)."""
    if not w or not h:
        return "1080p"
    min_dim = min(w, h)
    if min_dim >= 2000:
        return "4K"
    elif min_dim >= 1400:
        return "2K"
    elif min_dim >= 950:
        return "1080p"
    elif min_dim >= 650:
        return "720p"
    elif min_dim >= 440:
        return "480p"
    elif min_dim >= 320:
        return "360p"
    return f"{min_dim}p"


def get_video_dimensions(video_path: str, ffmpeg_exe: Optional[str] = None) -> Tuple[int, int]:
    """
    Mendeteksi dimensi (width, height) video menggunakan FFmpeg atau OpenCV.
    Mengembalikan (0, 0) jika gagal dideteksi.
    """
    if not os.path.isfile(video_path):
        return 0, 0

    if not ffmpeg_exe:
        ffmpeg_exe = get_ffmpeg_cmd()

    # 1. Coba probe metadata dengan FFmpeg
    if ffmpeg_exe:
        try:
            cmd = [ffmpeg_exe, "-i", video_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            stderr_text = (res.stderr or b"").decode("utf-8", errors="ignore")
            matches = re.findall(r'Video:.*?\b(\d{3,5})x(\d{3,5})\b', stderr_text)
            if matches:
                w, h = int(matches[0][0]), int(matches[0][1])
                if w > 0 and h > 0:
                    return w, h
        except Exception as e:
            logger.debug(f"[VideoCompressor] Probe dimensi FFmpeg gagal: {e}")

    # 2. Fallback menggunakan OpenCV jika terpasang
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            if w > 0 and h > 0:
                return w, h
    except Exception:
        pass

    return 0, 0


def format_file_size(size_bytes: int) -> str:
    """Format bytes to human readable string (KB, MB, GB)."""
    if not size_bytes or size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.1f} {units[i]}"


def get_ffmpeg_cmd() -> Optional[str]:
    """
    Mencari executable FFmpeg di berbagai sumber:
    1. Cache yang sudah valid
    2. Environment variable FFMPEG_PATH
    3. System PATH (shutil.which)
    4. Lokasi standar Linux (/usr/bin/ffmpeg, /usr/local/bin/ffmpeg, dll.)
    5. Package imageio-ffmpeg jika terpasang
    6. Lokasi standar Windows / Laragon
    """
    global _CACHED_FFMPEG_CMD
    if _CACHED_FFMPEG_CMD and os.path.isfile(_CACHED_FFMPEG_CMD):
        return _CACHED_FFMPEG_CMD

    # 1. Cek environment variable
    custom_path = os.getenv("FFMPEG_PATH", "").strip()
    if custom_path and os.path.isfile(custom_path):
        _CACHED_FFMPEG_CMD = custom_path
        logger.info(f"[VideoCompressor] FFmpeg ditemukan dari env FFMPEG_PATH: {_CACHED_FFMPEG_CMD}")
        return _CACHED_FFMPEG_CMD

    # 2. Cek system PATH
    system_ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if system_ffmpeg:
        _CACHED_FFMPEG_CMD = system_ffmpeg
        logger.info(f"[VideoCompressor] FFmpeg ditemukan di PATH: {_CACHED_FFMPEG_CMD}")
        return _CACHED_FFMPEG_CMD

    # 3. Cek lokasi standar Linux (/usr/bin/ffmpeg dari apt install)
    linux_paths = [
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/bin/ffmpeg",
        "/snap/bin/ffmpeg",
    ]
    for lp in linux_paths:
        if os.path.isfile(lp) and os.access(lp, os.X_OK):
            _CACHED_FFMPEG_CMD = lp
            logger.info(f"[VideoCompressor] FFmpeg ditemukan di lokasi Linux: {_CACHED_FFMPEG_CMD}")
            return _CACHED_FFMPEG_CMD

    # 4. Cek library imageio_ffmpeg jika tersedia
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and os.path.isfile(ffmpeg_exe):
            _CACHED_FFMPEG_CMD = ffmpeg_exe
            logger.info(f"[VideoCompressor] FFmpeg ditemukan via imageio_ffmpeg: {_CACHED_FFMPEG_CMD}")
            return _CACHED_FFMPEG_CMD
    except Exception:
        pass

    # 5. Cek lokasi standar di Windows / Laragon
    possible_paths = [
        r"C:\laragon\bin\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
    ]
    # Tambahkan pencarian di AppData WinGet jika ada
    user_profile = os.getenv("USERPROFILE") or os.path.expanduser("~")
    winget_glob = os.path.join(user_profile, "AppData", "Local", "Microsoft", "WinGet", "Packages", "*ffmpeg*", "*", "ffmpeg.exe")
    possible_paths.extend(glob.glob(winget_glob))

    for p in possible_paths:
        if os.path.isfile(p):
            _CACHED_FFMPEG_CMD = p
            logger.info(f"[VideoCompressor] FFmpeg ditemukan di direktori Windows: {_CACHED_FFMPEG_CMD}")
            return _CACHED_FFMPEG_CMD

    logger.warning("[VideoCompressor] FFmpeg tidak ditemukan di sistem. Video disimpan tanpa kompresi.")
    return None


def is_ffmpeg_available() -> bool:
    """Cek apakah fitur kompresi FFmpeg siap digunakan."""
    return get_ffmpeg_cmd() is not None


def get_safe_ffmpeg_threads() -> int:
    """
    Menghitung batas thread FFmpeg yang ramah server untuk VPS multi-website:
    - Tidak memonopoli CPU 100% (menyisakan core untuk Nginx/Apache, MySQL, dan website lain).
    - Mencegah throttling CPU oleh provider VPS dan mencegah web lain kena timeout/504.
    """
    total_cores = os.cpu_count() or 1
    if total_cores <= 1:
        return 1
    elif total_cores == 2:
        return 1  # 1 thread kompresi, 1 thread tersisa untuk web server & DB
    elif total_cores <= 4:
        return 2  # 2 thread kompresi, 2 thread untuk sistem & web lain
    else:
        return min(3, max(1, total_cores - 2))


def get_nice_prefix() -> list:
    """
    Di Linux, gunakan utilitas 'nice -n 15' agar proses kompresi berjalan dengan
    prioritas CPU rendah (background priority). Kernel Linux akan selalu mendahulukan
    Nginx, MySQL, dan request website lain daripada FFmpeg.
    """
    if sys.platform != "win32":
        nice_bin = shutil.which("nice")
        if nice_bin:
            return [nice_bin, "-n", "15"]
    return []


def extract_video_thumbnail_ffmpeg(
    video_path: str,
    thumb_dest_path: str,
    time_sec: float = 1.0,
    max_dimension: int = 400
) -> bool:
    """
    Mengekstrak 1 frame gambar dari video pada detik tertentu menggunakan FFmpeg.
    """
    ffmpeg_exe = get_ffmpeg_cmd()
    if not ffmpeg_exe or not os.path.isfile(video_path):
        return False

    try:
        # Scale to max_dimension on largest side, maintaining aspect ratio, even pixels
        scale_filter = f"scale='min({max_dimension},iw)':-2"
        cmd = [
            ffmpeg_exe,
            "-ss", f"{time_sec:.2f}",
            "-i", video_path,
            "-vframes", "1",
            "-vf", scale_filter,
            "-q:v", "2",
            "-y",
            thumb_dest_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return res.returncode == 0 and os.path.isfile(thumb_dest_path) and os.path.getsize(thumb_dest_path) > 0
    except Exception as e:
        logger.warning(f"[VideoCompressor] Gagal ekstrak thumbnail via ffmpeg: {e}")
        return False


def compress_video(
    input_path: str,
    output_path: Optional[str] = None,
    max_dimension: int = 1920,
    crf: int = 24,
    preset: str = "ultrafast"
) -> Dict[str, Any]:
    """
    Mengompresi file video untuk kebutuhan web:
    - Target resolusi minimal 1080p Full HD (max 1920px).
    - Aturan resolusi: Jika video <= 1080p (contoh: 1080p, 720p, 480p), video TIDAK dikompres (pertahankan file asli).
    - Jika video > 1080p (contoh: 4K 2160p, 2K/1440p), video dikompresi ke 1080p.
    - Codec video: H.264 (libx264) dengan pixel format yuv420p (kompatibel 100% browser & HP).
    - Codec audio: AAC 128kbps stereo.
    - Preset: ultrafast (super kencang di VPS).
    - Flag '+faststart': Memindahkan moov atom ke awal file untuk INSTANT STREAMING di browser.
    - Fallback aman: Jika gagal atau ukuran hasil kompresi lebih besar, file asli tetap dipertahankan.
    """
    if not os.path.isfile(input_path):
        return {
            "success": False,
            "error": "File input tidak ditemukan",
            "is_compressed": False,
            "final_path": input_path
        }

    original_size = os.path.getsize(input_path)
    ffmpeg_exe = get_ffmpeg_cmd()

    if not ffmpeg_exe:
        return {
            "success": False,
            "is_compressed": False,
            "reason": "ffmpeg_not_available",
            "original_size": original_size,
            "compressed_size": original_size,
            "saved_bytes": 0,
            "saved_percent": 0.0,
            "final_path": input_path,
            "info": "FFmpeg tidak terpasang di sistem. Video disimpan tanpa kompresi."
        }

    # 1. Deteksi dimensi asli video
    orig_w, orig_h = get_video_dimensions(input_path, ffmpeg_exe)
    detected_res = get_resolution_label(orig_w, orig_h) if (orig_w and orig_h) else "1080p"

    # 2. Aturan kompresi: Jika resolusi video <= 1080p, JANGAN dikompres (pertahankan file asli)
    if orig_w > 0 and orig_h > 0:
        is_le_1080 = max(orig_w, orig_h) <= 1920 and min(orig_w, orig_h) <= 1080
        if is_le_1080:
            logger.info(
                f"[VideoCompressor] Video {input_path} terdeteksi {orig_w}x{orig_h} ({detected_res}) <= 1080p. "
                "Kompresi dilewati sesuai instruksi minimal 1080p."
            )
            return {
                "success": True,
                "is_compressed": False,
                "reason": "resolution_le_1080p",
                "resolution": detected_res,
                "original_size": original_size,
                "compressed_size": original_size,
                "saved_bytes": 0,
                "saved_percent": 0.0,
                "final_path": input_path,
                "final_filename": os.path.basename(input_path),
                "info": f"Resolusi {detected_res} (<= 1080p), ukuran dipertahankan tanpa kompresi."
            }

    # Tentukan output path (selalu gunakan kontainer MP4 untuk kompatibilitas web optimal)
    input_dir = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    if output_path is None:
        temp_output_path = os.path.join(input_dir, f"temp_{base_name}.mp4")
    else:
        temp_output_path = output_path

    try:
        # Filter scale menjaga rasio aspek dan memastikan dimensi genap (-2)
        # Jika video portrait/vertikal (tinggi > lebar), batasi tinggi max 1920
        if orig_h > orig_w:
            scale_filter = f"scale=-2:'min({max_dimension},ih)':flags=fast_bilinear"
        else:
            scale_filter = f"scale='min({max_dimension},iw)':-2:flags=fast_bilinear"

        safe_threads = str(get_safe_ffmpeg_threads())
        nice_prefix = get_nice_prefix()

        cmd = nice_prefix + [
            ffmpeg_exe,
            "-y",                          # Timpa jika ada
            "-threads", safe_threads,      # Batas thread aman, menyisakan core untuk web & DB lain
            "-i", input_path,              # File input
            "-vf", scale_filter,           # Resize max dimension ke 1080p
            "-r", "30",                    # Batasi max 30 FPS (hemat waktu separuh untuk video 60fps)
            "-c:v", "libx264",             # Universal H.264 video codec
            "-preset", preset,             # ultrafast (super kencang di VPS)
            "-crf", str(crf),              # Constant Rate Factor (kualitas visual)
            "-pix_fmt", "yuv420p",         # Kompatibel di semua browser, iOS & Android
            "-c:a", "aac",                 # Universal AAC audio
            "-b:a", "128k",                # Audio bitrate yang jernih & hemat
            "-ac", "2",                    # Downmix stereo agar kompatibel di semua browser
            "-movflags", "+faststart",     # Instant web playback tanpa nunggu download
            "-max_muxing_queue_size", "1024",
            temp_output_path
        ]

        logger.info(
            f"[VideoCompressor] Memulai kompresi video > 1080p ({detected_res}) ke 1080p [threads={safe_threads}]: "
            f"{input_path} (Ukuran Asli: {format_file_size(original_size)})"
        )
        
        # Eksekusi proses ffmpeg dengan timeout wajar (maks 120 detik)
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )

        # Jika gagal dengan audio (misal video tanpa track suara), coba fallback tanpa audio (-an)
        if process.returncode != 0:
            cmd_no_audio = nice_prefix + [
                ffmpeg_exe,
                "-y",
                "-threads", safe_threads,
                "-i", input_path,
                "-vf", scale_filter,
                "-r", "30",
                "-c:v", "libx264",
                "-preset", preset,
                "-crf", str(crf),
                "-pix_fmt", "yuv420p",
                "-an",
                "-movflags", "+faststart",
                "-max_muxing_queue_size", "1024",
                temp_output_path
            ]
            process_no_audio = subprocess.run(
                cmd_no_audio,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120
            )
            if process_no_audio.returncode == 0:
                process = process_no_audio

        if process.returncode != 0:
            err_output = process.stderr.decode("utf-8", errors="ignore")[-400:]
            logger.warning(f"[VideoCompressor] FFmpeg gagal mengompresi (code {process.returncode}): {err_output}")
            if os.path.isfile(temp_output_path):
                os.remove(temp_output_path)
            return {
                "success": False,
                "is_compressed": False,
                "error": "ffmpeg_process_failed",
                "original_size": original_size,
                "compressed_size": original_size,
                "saved_bytes": 0,
                "saved_percent": 0.0,
                "final_path": input_path,
                "final_filename": os.path.basename(input_path),
                "resolution": detected_res,
                "info": "Gagal memproses video via FFmpeg. File asli dipertahankan."
            }

        # Cek ukuran file hasil kompresi
        compressed_size = os.path.getsize(temp_output_path)

        # Jika hasil kompresi lebih kecil (atau format awal bukan mp4 web-friendly), gunakan hasil kompresi
        if compressed_size < original_size or not input_path.lower().endswith(".mp4"):
            saved_bytes = max(0, original_size - compressed_size)
            saved_percent = round((saved_bytes / original_size) * 100, 1) if original_size > 0 else 0.0

            # Target nama file akhir .mp4
            final_mp4_path = os.path.join(input_dir, f"{base_name}.mp4")
            
            # Jika file awal berbeda ekstensi (misal .mov / .webm), hapus file mentah asli
            if input_path != final_mp4_path and os.path.isfile(input_path):
                try:
                    os.remove(input_path)
                except Exception as e:
                    logger.warning(f"Could not remove original raw file: {e}")

            # Pindahkan temp output ke nama final
            if temp_output_path != final_mp4_path:
                if os.path.isfile(final_mp4_path):
                    os.remove(final_mp4_path)
                os.rename(temp_output_path, final_mp4_path)

            # Deteksi resolusi akhir
            res_label = "1080p"
            try:
                out_w, out_h = get_video_dimensions(final_mp4_path, ffmpeg_exe)
                if out_w and out_h:
                    res_label = get_resolution_label(out_w, out_h)
            except Exception:
                pass

            orig_str = format_file_size(original_size)
            comp_str = format_file_size(compressed_size)
            info_msg = f"Berhasil dikompresi ke {res_label}: {orig_str} ➔ {comp_str} (Hemat {saved_percent}%)"
            logger.info(f"[VideoCompressor] {info_msg}")

            return {
                "success": True,
                "is_compressed": True,
                "resolution": res_label,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "saved_bytes": saved_bytes,
                "saved_percent": saved_percent,
                "final_path": final_mp4_path,
                "final_filename": os.path.basename(final_mp4_path),
                "info": info_msg
            }
        else:
            # Jika hasil kompresi malah lebih besar (sangat jarang, misal video sangat pendek/sudah hyper-compressed),
            # pertahankan file input
            if os.path.isfile(temp_output_path):
                os.remove(temp_output_path)
            logger.info(f"[VideoCompressor] File asli sudah lebih kecil atau sebanding, mempertahankan file asli.")
            return {
                "success": True,
                "is_compressed": False,
                "resolution": detected_res,
                "original_size": original_size,
                "compressed_size": original_size,
                "saved_bytes": 0,
                "saved_percent": 0.0,
                "final_path": input_path,
                "final_filename": os.path.basename(input_path),
                "info": "File asli dipertahankan karena ukuran sudah optimal."
            }

    except subprocess.TimeoutExpired:
        logger.error("[VideoCompressor] Timeout saat memproses kompresi video FFmpeg (melebihi batas 120 detik).")
        if os.path.isfile(temp_output_path):
            try:
                os.remove(temp_output_path)
            except Exception:
                pass
        return {
            "success": False,
            "is_compressed": False,
            "error": "timeout",
            "original_size": original_size,
            "compressed_size": original_size,
            "final_path": input_path,
            "info": "Kompresi video dibatalkan karena melebihi batas waktu (timeout)."
        }
    except Exception as e:
        logger.error(f"[VideoCompressor] Terjadi kendala saat kompresi video: {e}")
        if os.path.isfile(temp_output_path):
            try:
                os.remove(temp_output_path)
            except Exception:
                pass
        return {
            "success": False,
            "is_compressed": False,
            "error": str(e),
            "original_size": original_size,
            "compressed_size": original_size,
            "final_path": input_path,
            "info": f"Gagal kompresi: {str(e)}"
        }

