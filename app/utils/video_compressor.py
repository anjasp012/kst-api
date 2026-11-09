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
_CHECKED_FFMPEG: bool = False


def get_resolution_label(w: int, h: int) -> str:
    """Mengubah dimensi pixel ke label resolusi (4K, 2K, 1080p, 720p, 480p, 360p)."""
    if not w or not h:
        return "720p"
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
    1. Environment variable FFMPEG_PATH
    2. System PATH (shutil.which)
    3. Package imageio-ffmpeg jika terpasang
    4. Lokasi standar Laragon / Windows (C:\\laragon\\bin\\ffmpeg, C:\\ffmpeg, dll.)
    """
    global _CACHED_FFMPEG_CMD, _CHECKED_FFMPEG
    if _CHECKED_FFMPEG:
        return _CACHED_FFMPEG_CMD

    _CHECKED_FFMPEG = True

    # 1. Cek environment variable
    custom_path = os.getenv("FFMPEG_PATH", "").strip()
    if custom_path and os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
        _CACHED_FFMPEG_CMD = custom_path
        logger.info(f"[VideoCompressor] FFmpeg ditemukan dari env FFMPEG_PATH: {_CACHED_FFMPEG_CMD}")
        return _CACHED_FFMPEG_CMD

    # 2. Cek system PATH
    system_ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if system_ffmpeg:
        _CACHED_FFMPEG_CMD = system_ffmpeg
        logger.info(f"[VideoCompressor] FFmpeg ditemukan di PATH: {_CACHED_FFMPEG_CMD}")
        return _CACHED_FFMPEG_CMD

    # 3. Cek library imageio_ffmpeg jika tersedia
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and os.path.isfile(ffmpeg_exe):
            _CACHED_FFMPEG_CMD = ffmpeg_exe
            logger.info(f"[VideoCompressor] FFmpeg ditemukan via imageio_ffmpeg: {_CACHED_FFMPEG_CMD}")
            return _CACHED_FFMPEG_CMD
    except Exception:
        pass

    # 4. Cek lokasi standar di Windows / Laragon
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

    logger.warning("[VideoCompressor] FFmpeg tidak ditemukan. Video akan disimpan tanpa kompresi otomatis.")
    return None


def is_ffmpeg_available() -> bool:
    """Cek apakah fitur kompresi FFmpeg siap digunakan."""
    return get_ffmpeg_cmd() is not None


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
    max_dimension: int = 1280,
    crf: int = 26,
    preset: str = "veryfast"
) -> Dict[str, Any]:
    """
    Mengompresi file video untuk kebutuhan web:
    - Codec video: H.264 (libx264) dengan pixel format yuv420p (kompatibel 100% browser & HP)
    - Codec audio: AAC 128kbps stereo
    - Resolusi maks: max_dimension (default 1280px / 720p HD)
    - CRF: 26 (mengurangi ukuran file drastis 60-85% dengan kualitas visual prima)
    - Flag '+faststart': Memindahkan moov atom ke awal file untuk INSTANT STREAMING di browser
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

    # Tentukan output path (selalu gunakan kontainer MP4 untuk kompatibilitas web optimal)
    input_dir = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    if output_path is None:
        temp_output_path = os.path.join(input_dir, f"temp_{base_name}.mp4")
    else:
        temp_output_path = output_path

    try:
        # Filter scale menjaga rasio aspek dan memastikan dimensi genap (-2)
        scale_filter = f"scale='min({max_dimension},iw)':-2"

        cmd = [
            ffmpeg_exe,
            "-y",                          # Timpa jika ada
            "-i", input_path,              # File input
            "-vf", scale_filter,           # Resize max dimension
            "-c:v", "libx264",             # Universal H.264 video codec
            "-preset", preset,             # Kecepatan encoding vs kompresi
            "-crf", str(crf),              # Constant Rate Factor (kualitas visual)
            "-pix_fmt", "yuv420p",         # Kompatibel di semua browser, iOS & Android
            "-c:a", "aac",                 # Universal AAC audio
            "-b:a", "128k",                # Audio bitrate yang jernih & hemat
            "-ac", "2",                    # Downmix stereo agar kompatibel di semua browser
            "-movflags", "+faststart",     # Instant web playback tanpa nunggu download
            "-max_muxing_queue_size", "1024",
            temp_output_path
        ]

        logger.info(f"[VideoCompressor] Memulai kompresi video: {input_path} (Ukuran Asli: {format_file_size(original_size)})")
        
        # Eksekusi proses ffmpeg dengan timeout wajar (maks 120 detik)
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )

        # Jika gagal dengan audio (misal video tanpa track suara), coba fallback tanpa audio (-an)
        if process.returncode != 0:
            cmd_no_audio = [
                ffmpeg_exe,
                "-y",
                "-i", input_path,
                "-vf", scale_filter,
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
                "info": "Gagal memproses video via FFmpeg. File asli dipertahankan."
            }

        # Cek ukuran file hasil kompresi
        compressed_size = os.path.getsize(temp_output_path)

        # Jika hasil kompresi lebih kecil (atau format awal bukan mp4 web-friendly), gunakan hasil kompresi
        # Bandingkan jika ukuran hasil kompresi lebih hemat
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
            res_label = "720p"
            try:
                combined_err = (process.stderr or b"").decode("utf-8", errors="ignore")
                matches = re.findall(r'Video:.*?\s(\d{3,4})x(\d{3,4})', combined_err)
                if matches:
                    last_match = matches[-1]
                    res_label = get_resolution_label(int(last_match[0]), int(last_match[1]))
            except Exception:
                pass

            orig_str = format_file_size(original_size)
            comp_str = format_file_size(compressed_size)
            info_msg = f"Berhasil dikompresi: {orig_str} ➔ {comp_str} (Hemat {saved_percent}%)"
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
                "resolution": "720p",
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

