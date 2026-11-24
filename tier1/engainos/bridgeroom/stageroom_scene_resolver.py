"""Read-only catalog of Chapterroom-indexed Pass 5 artifacts.

Chapterroom establishes identity; Passroom supplies candidate JSON. This reader
neither dispatches nor grants AP/canon approval. The chapter-scoped done manifest
is run evidence, not the global catalog. No legacy-directory fallback exists.
load_scene restores the scene's own Pass 4 narrative segments; it does not carry
continuity between scenes.
"""

from contextlib import ExitStack
import errno
import hashlib
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
def scene_packet_sha256(packet: Dict[str, Any]) -> str:
    """Identity of a delivered scene packet: SHA-256 of its canonical JSON (sorted keys, no whitespace)."""
    canonical = json.dumps(packet, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


_SCENE_ID = re.compile(r'scene\.[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*\Z')
# narrative_to_game.py's Pass 4 output, as a catalog receipt lists it (one directory level, no traversal).
_PASS4_OUTPUT = re.compile(r'pipeline_work/[^/\\]+\.zonj\.json\Z')


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

    def _read_object(self, path: Path, root_fd: int,
                     expected_sha256: Optional[str] = None) -> Dict[str, Any]:
        """Open every path component without following symlinks; parse once.

        Directory descriptors bind traversal so a swapped directory cannot
        redirect the final read outside the selected stageroom. Non-regular
        files are rejected before parsing (including FIFOs, without blocking).
        With expected_sha256, the exact bytes parsed must have that hash.
        """
        relative = path.relative_to(self.root)
        try:
            with ExitStack() as stack:
                fd = self._directory_fd(root_fd, relative.parts[:-1], stack)
                file_fd = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW
                                  | os.O_NONBLOCK, dir_fd=fd)
                with os.fdopen(file_fd, 'rb') as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise ValueError('artifact is not a regular file')
                    raw = stream.read()
                if expected_sha256 is not None and hashlib.sha256(raw).hexdigest() != expected_sha256:
                    raise ValueError('bytes do not match the recorded SHA-256')
                data = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
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

    def _open_root(self, stack: ExitStack) -> int:
        """Bind the root itself without following any ancestor symlink."""
        try:
            anchor = os.open(self.root.anchor, os.O_RDONLY | os.O_DIRECTORY)
            stack.callback(os.close, anchor)
            return self._directory_fd(anchor, self.root.parts[1:], stack)
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise ValueError(f'Unsafe stageroom directory under {self.root}') from exc
            raise

    def _catalog(self, deliver_scene_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        try:
            with ExitStack() as stack:
                # Both discovery and packet reads stay relative to this same fd.
                root_fd = self._open_root(stack)
                index_fd = self._directory_fd(
                    root_fd, self.index_root.relative_to(self.root).parts, stack)
                self._directory_fd(
                    root_fd, self.pass_root.relative_to(self.root).parts, stack)
                catalog = self._catalog_at(root_fd, index_fd)
                if deliver_scene_id in catalog:
                    catalog[deliver_scene_id] = self._delivery_packet(
                        deliver_scene_id, catalog[deliver_scene_id], root_fd)
                return catalog
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise ValueError(f'Unsafe stageroom directory under {self.root}') from exc
            raise

    def _catalog_at(self, root_fd: int, index_fd: int) -> Dict[str, Dict[str, Any]]:
        indexed, authored = {}, {}
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
                authored[scene_id] = entry

        catalog = {}
        for scene_id in sorted(indexed):
            path = self.pass_root / scene_id / 'game_scenes' / f'{scene_id}.json'
            packet = self._read_object(path, root_fd)
            if packet.get('scene_id') != scene_id:
                raise ValueError(f'Pass 5 scene_id identity mismatch at {path}: '
                                 f'index={scene_id!r}, payload={packet.get("scene_id")!r}')
            # Chapterroom's authored header, kept apart from Passroom's extracted/inferred fields.
            entry = authored[scene_id]
            if isinstance(entry.get('scene_meta'), dict) and 'authored_scene_meta' not in packet:
                packet['authored_scene_meta'] = {
                    'source': 'chapterroom_scene_packets_index',
                    'authority_state': entry.get('authority_state'),
                    'boundary_method': entry.get('boundary_method'),
                    'fields': dict(entry['scene_meta']),
                }
            catalog[scene_id] = packet
        return catalog

    def _delivery_packet(self, scene_id: str, packet: Dict[str, Any],
                         root_fd: int) -> Dict[str, Any]:
        """Fill the runtime scene contract from artifacts Passroom already wrote.

        Pass 5 consumes Pass 4's ``=segments`` without carrying them, and keeps
        ``@where``/``@when`` only as ``metadata.where``/``metadata.when``. Only
        ``=segments`` is taken from Pass 4 (never ``@entities``, which would
        shadow Pass 5's structured entities); where/when are exposed from the
        packet's own metadata. Fields the packet already has are never touched.
        """
        packet = self._expose_where_when(packet)

        if '=segments' in packet or 'segments' in packet:
            return packet  # already complete; no Pass 4 dependency

        scene_dir = self.pass_root / scene_id
        names = (f'{scene_id}.zonj.json',
                 f'{scene_id[len("scene."):]}.zonj.json')  # current, legacy naming
        with ExitStack() as stack:
            dir_fd = self._directory_fd(
                root_fd, scene_dir.relative_to(self.root).parts, stack)
            present = []
            for name in names:
                try:
                    os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
                    present.append(name)
                except FileNotFoundError:
                    pass
        if len(present) > 1:
            raise ValueError(f'ambiguous Pass 4 artifacts for {scene_id!r}: {present}')
        if present != [names[0]]:
            return packet  # no exactly-named Pass 4 pair; serve Pass 5 as written

        path = scene_dir / names[0]
        packet['=segments'] = self._pass4_segments(self._read_object(path, root_fd), scene_id, path)
        return packet

    @staticmethod
    def _expose_where_when(packet: Dict[str, Any]) -> Dict[str, Any]:
        """Copy of the packet with metadata.where/when exposed where the packet lacks them."""
        packet = dict(packet)
        metadata = packet.get('metadata')
        if isinstance(metadata, dict):
            for key, at_key in (('where', '@where'), ('when', '@when')):
                if key in metadata and key not in packet and at_key not in packet:
                    packet[key] = metadata[key]
        return packet

    @staticmethod
    def _pass4_segments(fabric: Dict[str, Any], scene_id: str, path: Path) -> List[Dict[str, Any]]:
        """Pass 4's own =segments for scene_id; anything else is refused, never filled in."""
        if fabric.get('@id') != scene_id:
            raise ValueError(f'Pass 4 identity mismatch at {path}: '
                             f'index={scene_id!r}, payload={fabric.get("@id")!r}')
        segments = fabric.get('=segments')
        if not isinstance(segments, list) or not all(isinstance(s, dict) for s in segments):
            raise ValueError(f'Invalid Pass 4 =segments at {path}')
        return segments

    def load_catalog_scene(self, catalog_id: str,
                           manifest_path: Optional[Path] = None) -> Dict[str, Any]:
        """Deliver a Tier 1 catalog extraction (run_chapter_extraction) like load_scene.

        Identity comes from the live chapter catalog and the extraction receipt:
        extraction_status refuses unknown, unextracted and stale chapters (the
        receipt must be for the chapter's current bytes) and re-hashes the Pass 5
        scene. The receipt must list exactly one Pass 5 scene and exactly one
        Pass 4 ZONJ (narrative_to_game.py feeds that file to Pass 5); the Pass 4
        file is re-hashed against the receipt and must carry the receipt's own
        scene identity. Delivery is not acceptance: the receipt stays a candidate.
        """
        from tier1.engainos.tools import run_chapter_extraction as rce

        status, body = rce.extraction_status(catalog_id, manifest_path, self.root)
        if status == 404:
            raise FileNotFoundError(f'catalog extraction for {catalog_id!r} is '
                                    f'{body.get("extraction")!r}')
        if status != 200:
            raise ValueError(f'catalog extraction for {catalog_id!r} is unavailable '
                             f'(HTTP {status}): {body.get("extraction") or body.get("vault")}')
        receipt = body['receipt']
        if body['extraction'] != 'candidate' or receipt.get('returncode') != 0:
            raise ValueError(f'catalog extraction for {catalog_id!r} did not finish '
                             f'(status {body["extraction"]!r})')
        outputs = {o['path']: o['sha256'] for o in receipt.get('outputs', [])}
        scenes = receipt.get('game_scenes') or []
        pass4 = [p for p in outputs if _PASS4_OUTPUT.fullmatch(p)]
        if len(scenes) != 1 or len(pass4) != 1:
            raise ValueError(f'ambiguous catalog extraction for {catalog_id!r}: '
                             f'{len(scenes)} Pass 5 scenes, {len(pass4)} Pass 4 ZONJ files')

        chapter_id = receipt.get('chapter_id')
        packet = body['game_scenes'][scenes[0]]
        if not isinstance(chapter_id, str) or packet.get('scene_id') != chapter_id:
            raise ValueError(f'Pass 5 scene_id identity mismatch for {catalog_id!r}: '
                             f'receipt={chapter_id!r}, payload={packet.get("scene_id")!r}')
        out = rce.extraction_dir(self.root, {'catalog_id': body['catalog_id'],
                                             'source_sha256': body['source_sha256']})
        path = out / pass4[0]
        with ExitStack() as stack:
            fabric = self._read_object(path, self._open_root(stack), outputs[pass4[0]])

        segments = self._pass4_segments(fabric, f'scene.{chapter_id}', path)
        packet = self._expose_where_when(packet)
        if '=segments' not in packet and 'segments' not in packet:
            packet['=segments'] = segments
        packet.setdefault('catalog_extraction', {
            'source': 'tier1_chapter_extraction_receipt',
            'catalog_id': body['catalog_id'],
            'chapter_id': chapter_id,
            'source_sha256': body['source_sha256'],
            'receipt_status': receipt['status'],
            'acceptance': receipt['acceptance'],
            'pass4_sha256': outputs[pass4[0]],
            'pass5_sha256': outputs[scenes[0]],
        })
        return packet

    def list_available_scenes(self) -> List[str]:
        return list(self._catalog())

    def load_scene(self, scene_id: str) -> Dict[str, Any]:
        self._validate_scene_id(scene_id)
        catalog = self._catalog(deliver_scene_id=scene_id)
        if scene_id not in catalog:
            raise FileNotFoundError(f'Scene {scene_id!r} is not indexed by Chapterroom')
        # Validated Pass 5 payload plus its own Pass 4 narrative (see
        # _delivery_packet); no legacy stage/chapter rewriting of identity.
        return catalog[scene_id]
