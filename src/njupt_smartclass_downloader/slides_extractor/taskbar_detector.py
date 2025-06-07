from typing import List, Tuple
import cv2
import numpy as np


def detect_windows_logo(left_region: np.ndarray) -> bool:
    """Detect Windows logo pattern in the left region of taskbar."""
    if left_region.shape[0] < 20 or left_region.shape[1] < 40:
        return False

    gray = cv2.cvtColor(left_region, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 30, 100)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if 100 < area < 2000:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            if 0.8 < aspect_ratio < 1.5:
                center_x = x + w // 2
                center_y = y + h // 2
                if (
                    center_x < left_region.shape[1] // 2
                    and center_y > left_region.shape[0] // 4
                ):
                    return True

    return False


def detect_taskbar(frame: np.ndarray) -> bool:
    """Check if frame has Windows taskbar."""
    height, width = frame.shape[:2]
    taskbar_height = int(height * 0.08)

    taskbar_region = frame[height - taskbar_height : height, :width]
    gray_taskbar = cv2.cvtColor(taskbar_region, cv2.COLOR_BGR2GRAY)

    left_portion_width = min(200, width // 4)
    left_region = taskbar_region[:, :left_portion_width]

    # Quick histogram check
    hist = cv2.calcHist([gray_taskbar], [0], None, [256], [0, 256])
    dark_pixels = np.sum(hist[0:100])
    total_pixels = taskbar_height * width
    dark_ratio = dark_pixels / total_pixels

    if not (0.3 < dark_ratio < 0.8):
        return False

    # Detailed checks
    left_gray = cv2.cvtColor(left_region, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(left_gray, 50, 150)
    edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
    horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
    horizontal_line_density = np.sum(horizontal_lines > 0) / (
        horizontal_lines.shape[0] * horizontal_lines.shape[1]
    )

    unique_colors = len(
        np.unique(taskbar_region.reshape(-1, taskbar_region.shape[-1]), axis=0)
    )
    color_diversity = unique_colors / (taskbar_height * width)

    taskbar_indicators = 1

    if 0.01 < edge_density < 0.1:
        taskbar_indicators += 1
    if horizontal_line_density > 0.001:
        taskbar_indicators += 1
    if color_diversity < 0.5:
        taskbar_indicators += 1

    logo_detected = detect_windows_logo(left_region)
    if logo_detected:
        taskbar_indicators += 2

    return taskbar_indicators >= 3


def filter_fullscreen_segments(
    cap: cv2.VideoCapture, all_segments: List[Tuple[int, int]]
) -> List[Tuple[int, int]]:
    fullscreen_segments = []

    for i, (start_frame, end_frame) in enumerate(all_segments):
        accept_segment = True
        frame_to_check = (
            start_frame,
            start_frame + (end_frame - start_frame) // 2,
            end_frame - 1,
        )

        for frame_idx in frame_to_check:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                accept_segment = False
                break

            if detect_taskbar(frame):
                accept_segment = False
                break

        if accept_segment:
            fullscreen_segments.append((start_frame, end_frame))
    return fullscreen_segments
