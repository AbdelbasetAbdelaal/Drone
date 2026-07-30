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
            
        # Using 'mp4v' codec as a standard cross-platform option
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self._writer = cv2.VideoWriter(
            output_path, 
            fourcc, 
            self.fps, 
            (self.width, self.height)
        )
        
        if not self._writer.isOpened():
            logger.error(f"Failed to create video writer at: {output_path}")
            return False
            
        logger.info(f"Writer setup complete for: {output_path}")
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

    def __enter__(self):
        """Context manager support."""
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        self.close()
