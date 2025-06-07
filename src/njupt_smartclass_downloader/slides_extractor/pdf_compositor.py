import cv2
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from typing import List, Tuple


def make_pdf(
    frames_data: List[Tuple[str, np.ndarray]],
    output_path: str,
    paper_width: int,
    paper_height: int,
    title: str = "Slides",
) -> None:
    c = canvas.Canvas(output_path, pagesize=(paper_width, paper_height))

    for i, (title, frame) in enumerate(frames_data):
        try:
            # handle grayscale frames
            if len(frame.shape) == 2:  # Grayscale frame
                img = Image.fromarray(frame, "L")
            elif frame.shape[2] == 1:  # Single channel
                img = Image.fromarray(frame[:, :, 0], "L")
            else:  # Color frame
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), "RGB")

            img_width, img_height = img.size
            scale = min(paper_width / img_width, paper_height / img_height)
            new_width = img_width * scale
            new_height = img_height * scale
            x_offset = (paper_width - new_width) / 2
            y_offset = (paper_height - new_height) / 2
            c.drawImage(
                ImageReader(img),
                x_offset,
                y_offset,
                width=new_width,
                height=new_height,
            )

            bookmark_key = f"slide_{i + 1}"
            c.bookmarkPage(bookmark_key)
            c.addOutlineEntry(title, bookmark_key, level=0)

            c.showPage()

        except Exception as e:
            continue

    c.save()
