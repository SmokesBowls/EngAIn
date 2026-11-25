"""8765 chapter-extraction trigger: runs the existing run_chapter_extraction for one catalog_id.

    POST /chapters/extract          body exactly {"catalog_id": "<book>/<file>"}
    GET  /chapters/extract?catalog_id=<id>   job state for that chapter

- The chapter is resolved only by run_chapter_extraction.find_entry (active vault +
  live catalog); unknown ids are refused before anything starts. No paths are accepted.
- The work is run_chapter_extraction.run_extraction, unchanged, in a worker thread
  (8765's HTTPServer is single-threaded, so the request returns at once and the
  client polls GET). One extraction at a time: a second request while one runs is 409.
- Output is a Stageroom candidate. Nothing here talks to 8080, Trixel, or the vault.
- Access: loopback clients only, JSON bodies only (no browser form posts). No runtime
  credential is involved.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from tier1.engainos.tools import run_chapter_extraction as rce

MAX_BODY_BYTES = 4096


class ChapterExtractionJobs:
    def __init__(self, runner: Callable[..., dict] = rce.run_extraction) -> None:
        self._runner = runner
        self._lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._running: Optional[str] = None

    def start(self, catalog_id: Any, manifest_path: Optional[Path], stageroom: Path) -> tuple[int, dict]:
        if not isinstance(catalog_id, str) or not catalog_id:
            return 400, {"status": "error", "message": "catalog_id must be a non-empty string"}
        try:
            rce.find_entry(catalog_id, manifest_path)  # existing resolver; refuses unknown ids
        except rce.ExtractionError as e:
            return 404, {"status": "error", "state": "refused", "catalog_id": catalog_id, "message": str(e)}
        with self._lock:
            if self._running is not None:
                return 409, {"status": "error", "state": "busy", "running_catalog_id": self._running,
                             "message": "an extraction is already running"}
            self._running = catalog_id
            job = {"state": "running", "catalog_id": catalog_id, "started_at": time.time()}
            self._jobs[catalog_id] = job
        threading.Thread(target=self._run, args=(catalog_id, manifest_path, stageroom), daemon=True).start()
        return 202, {"status": "accepted", **job}

    def _run(self, catalog_id: str, manifest_path: Optional[Path], stageroom: Path) -> None:
        try:
            receipt = self._runner(catalog_id, manifest_path, stageroom)
            result = {"state": "finished", "receipt": receipt}
        except rce.ExtractionError as e:
            result = {"state": "error", "message": str(e)}
        except Exception as e:  # report, never leave the job "running"
            result = {"state": "error", "message": f"{type(e).__name__}: {e}"}
        with self._lock:
            self._jobs[catalog_id].update(result, finished_at=time.time())
            self._running = None

    def status(self, catalog_id: Optional[str]) -> tuple[int, dict]:
        with self._lock:
            job = dict(self._jobs.get(catalog_id or "", {"state": "idle", "catalog_id": catalog_id}))
            running = self._running
        return 200, {"status": "success", **job, "running_catalog_id": running}


JOBS = ChapterExtractionJobs()
