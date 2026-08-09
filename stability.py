from collections import Counter, deque
import time

import numpy as np


class FaceStabilityTracker:
    """Accept a face only after its 3x3 colors remain stable over time."""

    def __init__(
        self,
        min_frames=15,
        min_duration_seconds=0.5,
        min_agreement=0.8,
        history_window_seconds=1.0,
        max_history_frames=None,
    ):
        if min_frames < 1:
            raise ValueError("min_frames must be at least 1")
        if min_duration_seconds < 0:
            raise ValueError("min_duration_seconds cannot be negative")
        if not 0 < min_agreement <= 1:
            raise ValueError("min_agreement must be between 0 and 1")
        if history_window_seconds < min_duration_seconds:
            raise ValueError("history_window_seconds must cover min_duration_seconds")
        if max_history_frames is not None and max_history_frames < min_frames:
            raise ValueError("max_history_frames must be >= min_frames")

        self.min_frames = min_frames
        self.min_duration_seconds = min_duration_seconds
        self.min_agreement = min_agreement
        self.history_window_seconds = history_window_seconds
        self.max_history_frames = max_history_frames
        self._history = deque()

    @property
    def frame_count(self):
        return len(self._history)

    def reset(self):
        self._history.clear()

    def progress(self, timestamp=None):
        """Return progress from 0.0 to 1.0 for the current observation."""
        if not self._history:
            return 0.0

        current_time = self._history[-1][0] if timestamp is None else timestamp
        elapsed = max(0.0, current_time - self._history[0][0])
        frames_progress = min(1.0, len(self._history) / self.min_frames)
        if self.min_duration_seconds == 0:
            duration_progress = 1.0
        else:
            duration_progress = min(1.0, elapsed / self.min_duration_seconds)
        return min(frames_progress, duration_progress)

    def observe(self, colors, timestamp=None, color_costs=None):
        """
        Record one 3x3 observation and return stable colors when ready.

        A changed or unknown center starts a new observation. Unknown stickers are
        counted as disagreement, so they cannot be hidden by the consensus vote.
        """
        if colors is None or len(colors) != 9 or colors[4] == 'U':
            self.reset()
            return None

        observed_colors = tuple(colors)
        if self._history and self._history[0][1][4] != observed_colors[4]:
            self.reset()

        observed_at = time.monotonic() if timestamp is None else timestamp
        if color_costs is not None and len(color_costs) != 9:
            raise ValueError("color_costs must contain one entry per sticker")
        self._history.append((observed_at, observed_colors, color_costs))
        self._discard_expired_observations(observed_at)

        if len(self._history) < self.min_frames:
            return None
        if self.progress(observed_at) < 1.0:
            return None

        consensus = []
        total_observations = len(self._history)
        for sticker_index in range(9):
            votes = Counter(frame[sticker_index] for _, frame, _ in self._history)
            color, count = votes.most_common(1)[0]
            if color == 'U' or count / total_observations < self.min_agreement:
                return None
            consensus.append(color)

        return consensus

    def consensus_color_costs(self):
        """Return median per-color costs from the stable observation window."""
        if not self._history or any(costs is None for _, _, costs in self._history):
            return None
        colors = self._history[0][2][0].keys()
        return [
            {
                color: float(np.median([costs[index][color] for _, _, costs in self._history]))
                for color in colors
            }
            for index in range(9)
        ]

    def _discard_expired_observations(self, observed_at):
        while (
            self._history
            and observed_at - self._history[0][0] > self.history_window_seconds
        ):
            self._history.popleft()

        if self.max_history_frames is not None:
            while len(self._history) > self.max_history_frames:
                self._history.popleft()
