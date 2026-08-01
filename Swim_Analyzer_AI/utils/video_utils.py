"""
Video processing utilities wrapping OpenCV functionality.
"""
import cv2
import numpy as np
from typing import Tuple, Generator, Optional
from pathlib import Path
from core.logger import setup_logger

logger = setup_logger(__name__)

class VideoProcessor:
    """
    Utility class for reading from and writing to video files using OpenCV.
    Abstracts away the low-level cv2 VideoCapture and VideoWriter details.
    """
    
    def __init__(self, input_path: str):
        self.input_path = input_path
        self._cap: Optional[cv2.VideoCapture] = None
        self._writer: Optional[cv2.VideoWriter] = None
        
        # Video properties
        self.fps = 0.0
        self.width = 0
        self.height = 0
        self.frame_count = 0
        
    def open(self) -> bool:
        """Opens the video file for reading and populates properties."""
        self._cap = cv2.VideoCapture(self.input_path)
        if not self._cap.isOpened():
            logger.error(f"Failed to open video at: {self.input_path}")
            return False
            
        self.fps = self._cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Opened video: {self.input_path} ({self.width}x{self.height} @ {self.fps}fps)")
        return True
        
    def setup_writer(self, output_path: str) -> bool:
        """
        Sets up the OpenCV VideoWriter.
        
        Args:
            output_path: Path where the output video will be saved.
            
        Returns:
            bool: True if writer was successfully initialized, False otherwise.
        """
        if self.width == 0 or self.height == 0:
            logger.error("Cannot setup writer: video properties not initialized. Call open() first.")
            return False
            
        # Target 480p width for stability and memory efficiency on long videos
        target_width = min(self.width, 854)
        if target_width < self.width:
            scale = target_width / self.width
            self.width = target_width
            self.height = int(self.height * scale)
            logger.info(f"Output video will be downscaled to {self.width}x{self.height} (480p max) for stability.")
            
        # Fallback codec strategy: try 'mp4v' first, then 'avc1'
        codec_str = 'mp4v'
        fourcc = cv2.VideoWriter_fourcc(*codec_str)
        self._writer = cv2.VideoWriter(
            output_path, 
            fourcc, 
            self.fps, 
            (self.width, self.height)
        )
        
        if not self._writer.isOpened():
            logger.error(f"Failed to create video writer at: {output_path}")
            return False
            
        logger.info(f"Writer setup complete for: {output_path} (Codec: {codec_str})")
        return True
        
    def write_frame(self, frame: np.ndarray) -> None:
        """Writes a single frame to the output video."""
        if self._writer is None or not self._writer.isOpened():
            logger.warning("Writer is not open. Skipping frame write.")
            return
            
        self._writer.write(frame)
        
    def generate_frames(self) -> Generator[np.ndarray, None, None]:
        """
        Yields frames from the video sequentially.
        
        Yields:
            np.ndarray: The video frame as a NumPy array (BGR format).
        """
        if self._cap is None or not self._cap.isOpened():
            logger.error("Video capture is not open. Cannot generate frames.")
            return
            
        frame_idx = 0
        while True:
            ret, frame = self._cap.read()
            if not ret:
                break
                
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
                
            yield frame
            frame_idx += 1
            
            if frame_idx % 100 == 0:
                logger.debug(f"Processed {frame_idx}/{self.frame_count} frames")
                
    def close(self) -> None:
        """Releases video capture and writer resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            
        if self._writer is not None:
            self._writer.release()
            self._writer = None
            
        logger.info("Video resources released.")

    @staticmethod
    def ensure_browser_compatible_mp4(output_path: str) -> None:
        """
        Transcodes an OpenCV output video to web-compatible H.264 (avc1) format with +faststart
        so that modern browsers (Chrome, Edge, Firefox) can stream and play it natively.
        """
        import shutil
        import subprocess
        
        path_obj = Path(output_path)
        if not path_obj.exists() or path_obj.stat().st_size < 10 * 1024:
            return

        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            logger.warning("FFmpeg binary not found in PATH. Skipping H.264 web transcoding.")
            return

        temp_h264 = path_obj.with_name(f"{path_obj.stem}_h264.mp4")
        cmd = [
            ffmpeg_bin, "-y", "-i", str(path_obj),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(temp_h264)
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
            if temp_h264.exists() and temp_h264.stat().st_size > 10 * 1024:
                temp_h264.replace(path_obj)
                logger.info(f"[VIDEO] Video transcoded to web-optimized H.264 format: {output_path}")
            else:
                logger.warning(f"[VIDEO] H.264 transcoding produced empty file: {res.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            logger.warning(f"[VIDEO] H.264 transcoding encountered an error: {str(e)}")

    @staticmethod
    def validate_export(output_path: str) -> bool:
        """
        Validates that the exported video file is functional.
        Checks existence, size, and tests reopening with OpenCV.
        
        Args:
            output_path: The file path to validate.
            
        Returns:
            bool: True if valid, False if broken or empty.
        """
        import os
        path_obj = Path(output_path)
        
        # Ensure H.264 browser compatibility
        VideoProcessor.ensure_browser_compatible_mp4(output_path)
        
        # 1. Check file exists
        if not path_obj.exists():
            logger.error(f"Export validation failed: File does not exist at {output_path}")
            return False
            
        # 2. Check file size (> 5 KB)
        size_bytes = os.path.getsize(output_path)
        if size_bytes < 5 * 1024:
            logger.error(f"Export validation failed: File size is only {size_bytes} bytes (too small).")
            return False
            
        # 3. Check reopening with OpenCV and verifying metadata
        cap = cv2.VideoCapture(output_path)
        if not cap.isOpened():
            logger.error(f"Export validation failed: cv2.VideoCapture cannot reopen {output_path}")
            return False
            
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = frame_count / fps if fps > 0 else 0
        
        # Test reading the first frame
        ret, frame = cap.read()
        cap.release()
        
        if frame_count <= 0:
            logger.error("Export validation failed: Frame count is 0.")
            return False
            
        if duration <= 0:
            logger.error("Export validation failed: Duration is 0.")
            return False
            
        if not ret or frame is None:
            logger.error("Export validation failed: Cannot read the first frame.")
            return False
            
        logger.info(f"Export validation passed. Size: {size_bytes / (1024*1024):.2f} MB, Frames: {frame_count}, Duration: {duration:.2f}s")
        return True

    def __enter__(self):
        """Context manager support."""
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        self.close()

def get_video_info(video_path: str) -> dict:
    """
    Extracts basic video information (fps, width, height, frame_count) using OpenCV.
    
    Args:
        video_path: Absolute path to the video file.
        
    Returns:
        dict: containing 'fps', 'width', 'height', 'frame_count'
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"fps": 0.0, "width": 0, "height": 0, "frame_count": 0}
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    return {
        "fps": fps,
        "width": width,
        "height": height,
        "frame_count": frame_count
    }

def prepare_static_video(output_video_path: str, st_base_dir: str) -> str:
    """
    Copies the processed video to the Streamlit static directory for HTML5 playback
    and sanitizes the filename.
    
    Args:
        output_video_path: Absolute path to the generated MP4 file.
        st_base_dir: Absolute path to the streamlit application directory.
        
    Returns:
        str: The URL path suitable for HTML5 `<video src="...">`.
    """
    import os
    import re
    import shutil
    
    if not output_video_path or not os.path.exists(output_video_path):
        return ""
        
    static_dir = os.path.join(st_base_dir, "static")
    os.makedirs(static_dir, exist_ok=True)
    
    basename = os.path.basename(output_video_path)
    # Sanitize basename to remove spaces/special chars
    safe_basename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', basename)
    
    # Optional timestamp to bypass browser cache
    import time
    ts = int(time.time())
    safe_basename = f"{ts}_{safe_basename}"
    
    static_video_path = os.path.join(static_dir, safe_basename)
    
    try:
        shutil.copy2(output_video_path, static_video_path)
        logger.info(f"Copied {output_video_path} to {static_video_path}")
        return f"app/static/{safe_basename}"
    except Exception as e:
        logger.error(f"Failed to copy video to static directory: {e}")
        return ""
