"""Read-only catalog of Chapterroom-indexed Pass 5 artifacts.

Chapterroom establishes identity; Passroom supplies candidate JSON. This reader
neither dispatches nor grants AP/canon approval. The chapter-scoped done manifest
is run evidence, not the global catalog. No legacy-directory fallback exists.
"""

from contextlib import ExitStack
import errno
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import Any, Dict, List, Optional


DEFAULT_STAGEROOM_ROOT = (
    Path(__file__).resolve().parents[3] / 'tier3/mettaext/stageroom'
)
_SCENE_ID = re.compile(r'scene\.[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*\Z')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f'non-finite JSON constant: {value}')


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'non-finite JSON number: {value}')
    return number


class StageroomSceneResolver:
    """Deterministic, fail-closed catalog rebuilt on each list/load operation.

    A missing root/artifact raises FileNotFoundError. Invalid identity, ambiguous
    indexes, unsafe paths, and malformed packets raise ValueError. One invalid
    indexed artifact blocks the catalog; arbitrary unindexed files are ignored.
    Explicit roots are for isolated fixtures or an operator-selected stageroom.
    """

    def __init__(self, stageroom_root: Optional[Path] = None):
        self.root = Path(stageroom_root if stageroom_root is not None
                         else DEFAULT_STAGEROOM_ROOT).absolute()
        if '..' in self.root.parts:
            raise ValueError(f'Unsafe stageroom root: {self.root}')
        self.index_root = self.root / 'output/chapterroom/scene_packets'
        self.pass_root = self.root / 'output/passroom'

    @staticmethod
    def _validate_scene_id(scene_id: Any) -> str:
        if not isinstance(scene_id, str) or not _SCENE_ID.fullmatch(scene_id):
            raise ValueError(f'Invalid indexed scene_id: {scene_id!r}')
        return scene_id

    @staticmethod
    def _directory_fd(base_fd, parts, stack):
        fd = base_fd
        for part in parts:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                         dir_fd=fd)
            stack.callback(os.close, fd)
        return fd

    def _read_object(self, path: Path, root_fd: int) -> Dict[str, Any]:
        """Open every path component without following symlinks; parse once.

        Directory descriptors bind traversal so a swapped directory cannot
        redirect the final read outside the selected stageroom. Non-regular
        files are rejected before parsing (including FIFOs, without blocking).
        """
        relative = path.relative_to(self.root)
        try:
            with ExitStack() as stack:
                fd = self._directory_fd(root_fd, relative.parts[:-1], stack)
                file_fd = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW
                                  | os.O_NONBLOCK, dir_fd=fd)
                with os.fdopen(file_fd, 'r', encoding='utf-8') as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise ValueError('artifact is not a regular file')
                    data = json.load(stream, object_pairs_hook=_unique_object,
                                     parse_constant=_reject_constant,
                                     parse_float=_finite_float)
            if not isinstance(data, dict):
                raise ValueError('payload must be a dict')
            return data
        except ValueError as exc:
            raise ValueError(f'Invalid stageroom JSON {path}: {exc}') from exc
        except FileNotFoundError as exc:
            raise FileNotFoundError(f'Indexed stageroom artifact not found: {path}') from exc
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise ValueError(f'Unsafe stageroom path: {path}') from exc
            raise

    def _catalog(self) -> Dict[str, Dict[str, Any]]:
        try:
            with ExitStack() as stack:
                anchor = os.open(self.root.anchor, os.O_RDONLY | os.O_DIRECTORY)
                stack.callback(os.close, anchor)
                # Bind the root itself without following any ancestor symlink.
                # Both discovery and packet reads stay relative to this same fd.
                root_fd = self._directory_fd(anchor, self.root.parts[1:], stack)
                index_fd = self._directory_fd(
                    root_fd, self.index_root.relative_to(self.root).parts, stack)
                self._directory_fd(
                    root_fd, self.pass_root.relative_to(self.root).parts, stack)
                return self._catalog_at(root_fd, index_fd)
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise ValueError(f'Unsafe stageroom directory under {self.root}') from exc
            raise

    def _catalog_at(self, root_fd: int, index_fd: int) -> Dict[str, Dict[str, Any]]:
        indexed = {}
        # Exactly one level of retained Chapterroom indexes, not a recursive
        # JSON scan. Packet paths in the index are not used as read targets.
        for chapter in sorted(os.listdir(index_fd)):
            info = os.stat(chapter, dir_fd=index_fd, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                raise ValueError(f'Unsafe Chapterroom directory: {chapter}')
            if not stat.S_ISDIR(info.st_mode):
                continue
            with ExitStack() as stack:
                chapter_fd = self._directory_fd(index_fd, (chapter,), stack)
                try:
                    os.stat('scene_packets_index.json', dir_fd=chapter_fd,
                            follow_symlinks=False)
                except FileNotFoundError:
                    continue
            index_path = self.index_root / chapter / 'scene_packets_index.json'
            index = self._read_object(index_path, root_fd)
            packets = index.get('packets')
            if not isinstance(packets, list):
                raise ValueError(f'Invalid packets list in {index_path}')
            for entry in packets:
                if not isinstance(entry, dict):
                    raise ValueError(f'Invalid packet entry in {index_path}')
                scene_id = self._validate_scene_id(entry.get('scene_id'))
                if scene_id in indexed:
                    raise ValueError(f'ambiguous duplicate scene_id {scene_id!r}: '
                                     f'{indexed[scene_id]} and {index_path}')
                indexed[scene_id] = index_path

        catalog = {}
        for scene_id in sorted(indexed):
            path = self.pass_root / scene_id / 'game_scenes' / f'{scene_id}.json'
            packet = self._read_object(path, root_fd)
            if packet.get('scene_id') != scene_id:
                raise ValueError(f'Pass 5 scene_id identity mismatch at {path}: '
                                 f'index={scene_id!r}, payload={packet.get("scene_id")!r}')
            catalog[scene_id] = packet
        return catalog

    def list_available_scenes(self) -> List[str]:
        return list(self._catalog())

    def load_scene(self, scene_id: str) -> Dict[str, Any]:
        self._validate_scene_id(scene_id)
        catalog = self._catalog()
        if scene_id not in catalog:
            raise FileNotFoundError(f'Scene {scene_id!r} is not indexed by Chapterroom')
        # Return the exact validated payload, with no legacy stage/chapter
        # rewriting that could override the index-established scene identity.
        return catalog[scene_id]
