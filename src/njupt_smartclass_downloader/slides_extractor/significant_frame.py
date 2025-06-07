import cv2
import numpy as np
from typing import Callable, List, Optional, Tuple


def detect_significant_changes(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """
    Detect significant changes while filtering out noise.

    Returns:
        Change rate
    """
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    diff = cv2.absdiff(gray1, gray2)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    significant_changes = 0
    total_pixels = thresh.shape[0] * thresh.shape[1]

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:
            significant_changes += area

    change_rate = significant_changes / total_pixels
    return change_rate


def find_all_significant_frame(
    cap: cv2.VideoCapture,
    threshold: float,
    min_frame_gap: int,
    report_progress: Optional[Callable[[int, int], None]] = None,
) -> List[Tuple[int, int]]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    prev_frame = None
    segment_start = 0
    segments = []  # Collect all segments in a list
    frame_idx = -1

    # Process frames sequentially
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        if prev_frame is None:
            # First frame - start first segment
            segment_start = frame_idx
            prev_frame = frame.copy()
            continue

        # Detect significant changes for EVERY frame
        change_rate = detect_significant_changes(prev_frame, frame)

        if change_rate > threshold:
            if frame_idx - segment_start >= min_frame_gap:
                segments.append((segment_start, frame_idx))
            # Start new segment
            segment_start = frame_idx
            prev_frame = frame.copy()

        # Report progress
        if frame_idx % 50 == 0 or frame_idx == frame_count - 1:
            if report_progress:
                report_progress(frame_idx + 1, frame_count)

    if segment_start is not None:
        segments.append((segment_start, frame_idx + 1))

    return segments
