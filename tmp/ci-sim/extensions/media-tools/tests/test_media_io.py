import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import media_io


def _frame(i, w=48, h=32):
    a = np.zeros((h, w, 3), np.uint8)
    a[..., 0] = i * 40
    a[:, i * 3:i * 3 + 5] = 255
    return Image.fromarray(a)


def test_gif_roundtrip(tmp_path):
    p = tmp_path / "t.gif"
    media_io.save_gif([_frame(i) for i in range(3)], p, durations=80)
    frames = list(media_io.load_frames(p))
    assert len(frames) == 3
    assert all(f.mode == "RGB" for f, _ in frames)
    # frames differ — animation preserved
    assert not np.array_equal(np.asarray(frames[0][0]), np.asarray(frames[1][0]))


def test_load_frames_max(tmp_path):
    p = tmp_path / "t.gif"
    media_io.save_gif([_frame(i) for i in range(5)], p)
    assert len(list(media_io.load_frames(p, max_frames=2))) == 2


def test_is_animated():
    assert media_io.is_animated("a.gif") and media_io.is_animated("b.MP4")
    assert not media_io.is_animated("c.png")


def test_mp4_roundtrip(tmp_path):
    pytest.importorskip("cv2")
    p = tmp_path / "t.mp4"
    media_io.save_mp4([_frame(i) for i in range(4)], p, fps=10)
    frames = list(media_io.load_frames(p))
    assert len(frames) == 4
    assert frames[0][0].size == (48, 32)


def test_save_gif_durations_list(tmp_path):
    p = tmp_path / "t.gif"
    media_io.save_gif([_frame(0), _frame(1)], p, durations=[50, 200])
    durs = [d for _, d in media_io.load_frames(p)]
    assert durs[0] in (50, 60, 100) and durs[1] == 200
