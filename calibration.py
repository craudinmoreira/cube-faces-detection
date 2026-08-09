import time

import numpy as np


class CalibrationTracker:
    """Collect robust LAB samples from one solved face over a minimum duration."""

    def __init__(self, min_frames=30, min_duration_seconds=1.0):
        if min_frames < 1:
            raise ValueError("min_frames must be at least 1")
        if min_duration_seconds < 0:
            raise ValueError("min_duration_seconds cannot be negative")

        self.min_frames = min_frames
        self.min_duration_seconds = min_duration_seconds
        self._samples = []
        self._started_at = None
        self._last_observed_at = None

    @property
    def frame_count(self):
        return len(self._samples)

    def reset(self):
        self._samples.clear()
        self._started_at = None
        self._last_observed_at = None

    def progress(self, timestamp=None):
        if self._started_at is None:
            return 0.0

        current_time = self._last_observed_at if timestamp is None else timestamp
        elapsed = max(0.0, current_time - self._started_at)
        frame_progress = min(1.0, self.frame_count / self.min_frames)
        if self.min_duration_seconds == 0:
            duration_progress = 1.0
        else:
            duration_progress = min(1.0, elapsed / self.min_duration_seconds)
        return min(frame_progress, duration_progress)

    def observe(self, lab_samples, timestamp=None):
        """Record nine LAB medians and return the calibrated center when ready."""
        samples = np.asarray(lab_samples, dtype=float)
        if samples.shape != (9, 3):
            self.reset()
            return None

        observed_at = time.monotonic() if timestamp is None else timestamp
        if self._started_at is None:
            self._started_at = observed_at
        self._last_observed_at = observed_at
        self._samples.append(samples)

        if self.frame_count < self.min_frames:
            return None
        if self.progress(observed_at) < 1.0:
            return None

        return np.median(np.vstack(self._samples), axis=0)

    def profile(self):
        """Summarize the accepted observations for persistence and later analysis."""
        if not self._samples or self._started_at is None or self._last_observed_at is None:
            return None
        observations = np.vstack(self._samples)
        center = np.median(observations, axis=0)
        distances = np.linalg.norm(observations - center, axis=1)
        return {
            "center_lab": [float(value) for value in center],
            "channel_std_lab": [float(value) for value in np.std(observations, axis=0)],
            "distance_percentiles": {
                "p50": float(np.percentile(distances, 50)),
                "p90": float(np.percentile(distances, 90)),
                "p95": float(np.percentile(distances, 95)),
            },
            "sample_count": int(len(observations)),
            "duration_seconds": float(self._last_observed_at - self._started_at),
        }
