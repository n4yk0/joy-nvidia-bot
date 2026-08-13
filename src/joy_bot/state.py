from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class StateTracker:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._seen: dict[str, bool] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            self._seen = json.loads(self._path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("state file unreadable, starting fresh: %s", exc)
            self._seen = {}

    def transitioned_to_in_stock(self, sku: str, is_active: bool) -> bool:
        previous = self._seen.get(sku, False)
        return is_active and not previous

    def update(self, sku: str, is_active: bool) -> None:
        self._seen[sku] = is_active

    def flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._seen))
        tmp.replace(self._path)
