"""Webcam input — capture a single frame via OpenCV (site parity: webcam source)."""
import numpy as np
from PIL import Image


def capture(device=0, warmup=5, width=None, height=None):
    import cv2
    cap = cv2.VideoCapture(int(device))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open webcam {device}")
    if width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
    if height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
    try:
        for _ in range(int(warmup)):  # let auto-exposure settle
            cap.read()
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("webcam read failed")
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        cap.release()
