from __future__ import annotations

from pathlib import Path

import miniaudio


def probe_duration(path: Path) -> float:
    """Return audio duration in seconds, 0.0 if the file cannot be probed."""
    for probe in [
        miniaudio.wav_get_file_info,
        miniaudio.flac_get_file_info,
        miniaudio.mp3_get_file_info,
        miniaudio.vorbis_get_file_info,
    ]:
        try:
            info = probe(str(path))
            return info.num_frames / info.sample_rate
        except Exception:
            continue
    return 0.0
