from typing import Callable, Optional
import cv2
import numpy as np


def calculate_mode_frame(
    cap: cv2.VideoCapture,
    start_frame: int,
    end_frame: int,
    report_progress: Optional[Callable[[int, int], None]] = None,
) -> np.ndarray:
    frame_count = end_frame - start_frame
    if frame_count <= 0:
        raise ValueError(f"Invalid frame range [{start_frame}, {end_frame})")

    # Set to start frame and read sequentially
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Read first frame to get dimensions
    ret, first_frame = cap.read()
    if not ret:
        raise ValueError(f"Cannot read frame {start_frame}")

    if frame_count == 1:
        if report_progress:
            report_progress(1, 1)
        return first_frame

    height, width = first_frame.shape[:2]

    # Initialize Boyer-Moore state for all pixels
    candidates = first_frame.copy()  # Shape: (height, width, channels)
    counts = np.ones((height, width), dtype=np.int32)
    matches = np.zeros((height, width), dtype=bool)

    # Process remaining frames sequentially
    for frame_idx in range(1, frame_count):
        ret, frame = cap.read()
        if not ret:
            continue

        np.all(frame == candidates, axis=2, out=matches)  # Shape: (height, width)
        counts += np.where(matches, 1, -1)

        # Update candidates where count became zero
        zero_mask = counts == 0
        candidates[zero_mask] = frame[zero_mask]
        counts[zero_mask] = 1

        # Report progress
        if frame_idx % 50 == 0 or frame_idx == frame_count - 1:
            if report_progress:
                report_progress(frame_idx + 1, frame_count)
    return candidates
