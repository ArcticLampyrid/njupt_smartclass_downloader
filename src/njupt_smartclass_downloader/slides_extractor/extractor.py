from typing import Callable, Optional
import cv2
from pathlib import Path

from njupt_smartclass_downloader.slides_extractor.mode_frame import calculate_mode_frame
from njupt_smartclass_downloader.slides_extractor.pdf_compositor import make_pdf
from njupt_smartclass_downloader.slides_extractor.significant_frame import (
    find_all_significant_frame,
)
from njupt_smartclass_downloader.slides_extractor.taskbar_detector import (
    filter_fullscreen_segments,
)


def extract_slides(
    video_input: str,
    pdf_output: str,
    threshold: float = 0.02,
    min_time_gap: float = 3,
    report_progress: Optional[Callable[[str, int, int], None]] = None,
):
    cap = None
    try:
        cap = cv2.VideoCapture(video_input)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_input}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        all_segments = find_all_significant_frame(
            cap,
            threshold,
            int(min_time_gap * fps),
            lambda current, total: (
                report_progress(f"Analyzing", current, total)
                if report_progress
                else None
            ),
        )

        if report_progress:
            report_progress("Filtering", 0, len(all_segments))
        fullscreen_segments = filter_fullscreen_segments(cap, all_segments)
        if report_progress:
            report_progress("Filtering", len(all_segments), len(all_segments))

        n_mode_frame_to_calculate = sum(
            end_frame - start_frame for start_frame, end_frame in fullscreen_segments
        )
        n_mode_frame_calculated = 0

        slides = []
        for i, (start_frame, end_frame) in enumerate(fullscreen_segments):
            mode_frame = calculate_mode_frame(
                cap,
                start_frame,
                end_frame,
                lambda current, _: (
                    report_progress(
                        "Compositing",
                        n_mode_frame_calculated + current,
                        n_mode_frame_to_calculate,
                    )
                    if report_progress
                    else None
                ),
            )
            n_mode_frame_calculated += end_frame - start_frame
            slides.append(
                (f"Slide {i+1} (frames {start_frame}-{end_frame - 1})", mode_frame)
            )

        if report_progress:
            report_progress("Saving", 0, len(slides))
        make_pdf(slides, pdf_output, video_width, video_height)
        if report_progress:
            report_progress("Saving", len(slides), len(slides))

        return 0

    except Exception as e:
        return 1

    finally:
        if cap and cap.isOpened():
            cap.release()
