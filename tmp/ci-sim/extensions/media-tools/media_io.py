"""Animated IO — GIF input/output via Pillow, MP4/WebM via OpenCV.
GIF export parity: site exports ~2s @ 10fps (we default 10fps, all frames).
Each frame runs the full pipeline with seed=frame_index so animated
params (matrixRain speed, noiseField, vhs grain) actually move."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageSequence

ANIM_INPUT = {".gif", ".mp4", ".webm", ".mov", ".mkv", ".avi"}
ANIM_OUTPUT = {".gif", ".mp4"}


def is_animated(path):
    return Path(path).suffix.lower() in ANIM_INPUT


def load_frames(path, max_frames=None):
    """Yield (PIL.Image, duration_ms) per frame."""
    ext = Path(path).suffix.lower()
    if ext == ".gif":
        with Image.open(path) as im:
            for i, fr in enumerate(ImageSequence.Iterator(im)):
                if max_frames and i >= max_frames:
                    break
                yield fr.convert("RGB"), fr.info.get("duration", 100)
        return
    import cv2
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"cannot open video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    dur = 1000 / fps
    i = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok or (max_frames and i >= max_frames):
                break
            yield Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), dur
            i += 1
    finally:
        cap.release()


def save_gif(frames, path, durations=None):
    """frames: list of PIL images. durations: ms per frame or scalar."""
    frames = [f.convert("P", palette=Image.ADAPTIVE, colors=256) for f in frames]
    if not frames:
        raise ValueError("no frames")
    dur = durations if isinstance(durations, (int, float)) else 100
    if isinstance(durations, (list, tuple)):
        dur = list(durations) + [100] * (len(frames) - len(durations))
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=dur, loop=0, optimize=True)


def save_mp4(frames, path, fps=10):
    import cv2
    if not frames:
        raise ValueError("no frames")
    w, h = frames[0].size
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    if not vw.isOpened():
        raise RuntimeError("cv2.VideoWriter failed — codec unavailable")
    try:
        for f in frames:
            vw.write(cv2.cvtColor(np.asarray(f), cv2.COLOR_RGB2BGR))
    finally:
        vw.release()
