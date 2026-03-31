from dataclasses import dataclass
from typing import Iterator, Tuple
import numpy as np


@dataclass
class PurgedKFold:
    n_splits: int = 5
    embargo_pct: float = 0.01
    label_horizon: int = 10

    def split(self, n_samples: int) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        idx = np.arange(n_samples)
        fold_sizes = np.full(self.n_splits, n_samples // self.n_splits)
        fold_sizes[: n_samples % self.n_splits] += 1

        cur = 0
        for fs in fold_sizes:
            start, stop = cur, cur + fs
            test = idx[start:stop]
            embargo = int(np.ceil(n_samples * self.embargo_pct))
            mask = np.ones(n_samples, dtype=bool)
            mask[start:min(n_samples, stop + self.label_horizon)] = False
            mask[stop:min(n_samples, stop + embargo)] = False
            yield idx[mask], test
            cur = stop
