# Canvas undo/redo: snapshots of scene JSON (expressions, positions, modes).
from __future__ import annotations

import copy
from typing import Any, Callable, Dict, List, Optional


class CanvasHistory:
    def __init__(self, capture: Callable[[], Dict[str, Any]], restore: Callable[[Dict[str, Any]], None], limit: int = 50):
        self._capture = capture
        self._restore = restore
        self._limit = limit
        self._undo: List[Dict[str, Any]] = []
        self._redo: List[Dict[str, Any]] = []
        self._restoring = False

    def push(self) -> None:
        if self._restoring:
            return
        snap = copy.deepcopy(self._capture())
        self._undo.append(snap)
        if len(self._undo) > self._limit:
            self._undo.pop(0)
        self._redo.clear()

    def undo(self) -> bool:
        if len(self._undo) < 2:
            return False
        current = self._undo.pop()
        self._redo.append(current)
        self._restoring = True
        try:
            self._restore(copy.deepcopy(self._undo[-1]))
        finally:
            self._restoring = False
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        snap = self._redo.pop()
        self._undo.append(snap)
        self._restoring = True
        try:
            self._restore(copy.deepcopy(snap))
        finally:
            self._restoring = False
        return True
