"""Default stageroom resolution and explicit legacy-mode preservation.

All artifacts are isolated fixtures. No pipeline, server or world mutation.
"""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tier1.engainos.bridgeroom import scene_loader


class TestStageroomSceneLoader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'stageroom'
        self.index_root = self.root / 'output/chapterroom/scene_packets'
        self.pass_root = self.root / 'output/passroom'
        self.index_root.mkdir(parents=True)
        self.pass_root.mkdir(parents=True)

    def index(self, chapter, scenes):
        path = self.index_root / chapter / 'scene_packets_index.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            'contract': 'engain.scene_provider_packet.v1',
            'chapter_id': chapter,
            'packets': [{'scene_id': sid, 'chapter_id': chapter} for sid in scenes],
        }), encoding='utf-8')
        return path

    def artifact(self, sid, payload=None):
        path = self.pass_root / sid / 'game_scenes' / (sid + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'scene_id': sid, 'entities': [], 'events': []}
                                   if payload is None else payload), encoding='utf-8')
        return path

    def resolver(self):
        cls = getattr(scene_loader, 'StageroomSceneResolver', None)
        if cls is None:
            raise AssertionError('SceneLoader needs the current stageroom resolver')
        return cls(self.root)

    def test_default_loader_uses_resolver_not_flat_directory(self):
        sid = 'scene.book001.001.scene001'
        self.index('chapter.book001.001', [sid])
        self.artifact(sid)
        resolver = self.resolver()
        with patch.object(scene_loader, 'StageroomSceneResolver',
                          return_value=resolver) as constructor:
            loader = scene_loader.SceneLoader()
            constructor.assert_called_once_with()
            self.assertEqual(loader.list_available_scenes(), [sid])
            self.assertEqual(loader.load_scene(sid)['scene_id'], sid)

    def test_default_loader_does_not_fall_back_when_catalog_missing(self):
        resolver = self.resolver()
        self.index_root.rmdir()
        with patch.object(scene_loader, 'StageroomSceneResolver', return_value=resolver):
            loader = scene_loader.SceneLoader()
            with self.assertRaises(FileNotFoundError):
                loader.list_available_scenes()
            with self.assertRaises(FileNotFoundError):
                loader.load_scene('scene.a')

    def test_default_loader_rejects_wrong_payload_identity(self):
        self.index('chapter.a', ['scene.a'])
        self.artifact('scene.a', {'scene_id': 'scene.b'})
        resolver = self.resolver()
        with patch.object(scene_loader, 'StageroomSceneResolver', return_value=resolver):
            loader = scene_loader.SceneLoader()
            with self.assertRaises(ValueError):
                loader.list_available_scenes()
            with self.assertRaises(ValueError):
                loader.load_scene('scene.a')

    def test_multiple_chapters_and_scenes_are_sorted_and_loadable(self):
        scenes = ['scene.book002.002.scene001', 'scene.book001.001.scene002',
                  'scene.book001.001.scene001']
        self.index('chapter.book002.002', scenes[:1])
        self.index('chapter.book001.001', scenes[1:])
        for sid in scenes:
            self.artifact(sid)
        resolver = self.resolver()
        self.assertEqual(resolver.list_available_scenes(), sorted(scenes))
        for sid in resolver.list_available_scenes():
            self.assertEqual(resolver.load_scene(sid)['scene_id'], sid)

    def test_unindexed_json_and_metadata_are_not_discovered(self):
        sid = 'scene.book001.001.scene001'
        self.index('chapter.book001.001', [sid])
        path = self.artifact(sid)
        (path.parent / 'scene_index.json').write_text('{}', encoding='utf-8')
        self.artifact('scene.unindexed', {'scene_id': 'scene.unindexed'})
        self.assertEqual(self.resolver().list_available_scenes(), [sid])

    def test_duplicate_scene_ids_across_indexes_are_ambiguous(self):
        sid = 'scene.duplicate'
        self.index('chapter.a', [sid])
        self.index('chapter.b', [sid])
        self.artifact(sid)
        with self.assertRaisesRegex(ValueError, 'ambiguous|duplicate'):
            self.resolver().list_available_scenes()

    def test_duplicate_scene_ids_within_index_are_rejected(self):
        self.index('chapter.a', ['scene.a', 'scene.a'])
        self.artifact('scene.a')
        with self.assertRaisesRegex(ValueError, 'ambiguous|duplicate'):
            self.resolver().load_scene('scene.a')

    def test_wrong_payload_identity_rejected_by_listing_and_loading(self):
        self.index('chapter.a', ['scene.a'])
        self.artifact('scene.a', {'scene_id': 'scene.b'})
        for operation in (lambda: self.resolver().list_available_scenes(),
                          lambda: self.resolver().load_scene('scene.a')):
            with self.assertRaisesRegex(ValueError, 'scene_id|identity'):
                operation()

    def test_non_dict_payload_rejected(self):
        self.index('chapter.a', ['scene.a'])
        self.artifact('scene.a', [])
        with self.assertRaises(ValueError):
            self.resolver().load_scene('scene.a')

    def test_malformed_payload_rejected(self):
        self.index('chapter.a', ['scene.a'])
        self.artifact('scene.a').write_text('{broken', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.resolver().list_available_scenes()

    def test_missing_artifact_is_loud(self):
        self.index('chapter.a', ['scene.missing'])
        with self.assertRaises(FileNotFoundError):
            self.resolver().list_available_scenes()

    def test_wrong_filename_is_not_a_fallback(self):
        self.index('chapter.a', ['scene.a'])
        path = self.pass_root / 'scene.a/game_scenes/a.json'
        path.parent.mkdir(parents=True)
        path.write_text('{"scene_id":"scene.a"}', encoding='utf-8')
        with self.assertRaises(FileNotFoundError):
            self.resolver().load_scene('scene.a')

    def test_missing_discovery_root_is_loud(self):
        self.index_root.rmdir()
        with self.assertRaises(FileNotFoundError):
            self.resolver().list_available_scenes()

    def test_existing_empty_catalog_returns_empty(self):
        self.assertEqual(self.resolver().list_available_scenes(), [])

    def test_unindexed_scene_is_not_loadable(self):
        self.artifact('scene.unindexed')
        with self.assertRaises(FileNotFoundError):
            self.resolver().load_scene('scene.unindexed')

    def test_invalid_index_shapes_are_rejected(self):
        path = self.index('chapter.a', [])
        for payload in ([], {}, {'packets': {}}, {'packets': [None]},
                        {'packets': [{'scene_id': None}]},
                        {'packets': [{'scene_id': 'scene_index'}]}):
            with self.subTest(payload=payload):
                path.write_text(json.dumps(payload), encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.resolver().list_available_scenes()

    def test_scene_id_path_traversal_rejected(self):
        for sid in ('../outside', 'scene../outside', '/absolute', 'scene.a\\b', 'scene...'):
            with self.subTest(sid=sid):
                self.index('chapter.a', [sid])
                with self.assertRaises(ValueError):
                    self.resolver().list_available_scenes()

    def test_artifact_symlink_escape_rejected(self):
        self.index('chapter.a', ['scene.a'])
        path = self.pass_root / 'scene.a/game_scenes/scene.a.json'
        path.parent.mkdir(parents=True)
        outside = Path(self.tmp.name) / 'outside.json'
        outside.write_text('{"scene_id":"scene.a"}', encoding='utf-8')
        path.symlink_to(outside)
        with self.assertRaises(ValueError):
            self.resolver().list_available_scenes()

    def test_scene_directory_symlink_to_other_scene_rejected(self):
        self.index('chapter.a', ['scene.a'])
        other = self.pass_root / 'scene.b/game_scenes'
        other.mkdir(parents=True)
        (other / 'scene.a.json').write_text('{"scene_id":"scene.a"}', encoding='utf-8')
        (self.pass_root / 'scene.a').symlink_to(other.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.resolver().load_scene('scene.a')

    def test_index_symlink_escape_rejected(self):
        path = self.index('chapter.a', [])
        outside = Path(self.tmp.name) / 'index.json'
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaises(ValueError):
            self.resolver().list_available_scenes()

    def test_chapter_directory_symlink_rejected(self):
        path = self.index('chapter.a', ['scene.a']).parent
        self.artifact('scene.a')
        outside = Path(self.tmp.name) / 'outside_chapter'
        path.rename(outside)
        path.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.resolver().list_available_scenes()

    def test_game_scenes_directory_symlink_rejected(self):
        self.index('chapter.a', ['scene.a'])
        path = self.artifact('scene.a').parent
        outside = Path(self.tmp.name) / 'outside_game_scenes'
        path.rename(outside)
        path.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.resolver().load_scene('scene.a')

    def test_root_ancestor_symlink_rejected(self):
        alias = Path(self.tmp.name) / 'alias'
        alias.symlink_to(self.root.parent, target_is_directory=True)
        cls = type(self.resolver())
        with self.assertRaises(ValueError):
            cls(alias / 'stageroom').list_available_scenes()

    def test_root_ancestor_swap_cannot_redirect_catalog(self):
        workspace = Path(self.tmp.name) / 'workspace'
        workspace.mkdir()
        self.root.rename(workspace / 'stageroom')
        self.root = workspace / 'stageroom'
        self.index_root = self.root / 'output/chapterroom/scene_packets'
        self.pass_root = self.root / 'output/passroom'
        self.index('chapter.a', ['scene.a'])
        self.artifact('scene.a')
        resolver = self.resolver()
        outside = Path(self.tmp.name) / 'outside'
        outside_index = outside / 'stageroom/output/chapterroom/scene_packets/chapter.a'
        outside_index.mkdir(parents=True)
        (outside_index / 'scene_packets_index.json').write_text(
            '{"packets":[{"scene_id":"scene.a"}]}', encoding='utf-8')
        outside_packet = outside / 'stageroom/output/passroom/scene.a/game_scenes'
        outside_packet.mkdir(parents=True)
        (outside_packet / 'scene.a.json').write_text(
            '{"scene_id":"scene.a","redirected":true}', encoding='utf-8')
        real_open = os.open
        swapped = False

        def swap_before_root_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if not swapped and Path(path) in (self.root, Path('stageroom')):
                workspace.rename(Path(self.tmp.name) / 'original_workspace')
                workspace.symlink_to(outside, target_is_directory=True)
                swapped = True
            return real_open(path, flags, *args, **kwargs)

        with patch('os.open', side_effect=swap_before_root_open):
            try:
                packet = resolver.load_scene('scene.a')
            except ValueError:
                packet = None
        self.assertTrue(swapped, 'the ancestor-swap hook must execute')
        if packet is not None:
            self.assertNotIn('redirected', packet)

    def test_catalog_refreshes_and_load_revalidates(self):
        self.index('chapter.a', ['scene.a'])
        path = self.artifact('scene.a')
        resolver = self.resolver()
        self.assertEqual(resolver.list_available_scenes(), ['scene.a'])
        path.write_text('{"scene_id":"scene.wrong"}', encoding='utf-8')
        with self.assertRaises(ValueError):
            resolver.load_scene('scene.a')

    def test_stage_id_does_not_override_validated_scene_identity(self):
        self.index('chapter.a', ['scene.a'])
        self.artifact('scene.a', {'scene_id': 'scene.a', 'stage_id': 'scene.other'})
        self.assertEqual(self.resolver().load_scene('scene.a')['scene_id'], 'scene.a')

    def test_strict_json_rejects_duplicate_identity_keys_and_nan(self):
        self.index('chapter.a', ['scene.a'])
        path = self.artifact('scene.a')
        for text in ('{"scene_id":"scene.other","scene_id":"scene.a"}',
                     '{"scene_id":"scene.a","value":NaN}',
                     '{"scene_id":"scene.a","value":1e999}'):
            with self.subTest(text=text):
                path.write_text(text, encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.resolver().load_scene('scene.a')


class TestExplicitFlatSceneLoader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.loader = scene_loader.SceneLoader(scenes_dir=self.root)

    def test_flat_override_preserves_aliases_and_packet_normalization(self):
        (self.root / 'a.json').write_text(json.dumps({'chapter_id': 'chapter.a',
                                                     'stage_id': 'stage.a'}), encoding='utf-8')
        for sid in ('a', 'scene.a'):
            packet = self.loader.load_scene(sid)
            self.assertEqual(packet['chapter_id'], 'chapter.a')
            self.assertEqual(packet['scene_id'], 'stage.a')
            self.assertEqual(packet['source_packet_id'], 'scene.a')

    def test_flat_override_lists_stems_except_metadata(self):
        for name in ('a.json', 'scene.b.json', 'scene_index.json'):
            (self.root / name).write_text('{}', encoding='utf-8')
        self.assertEqual(set(self.loader.list_available_scenes()), {'a', 'scene.b'})

    def test_flat_override_keeps_requested_stem_precedence(self):
        for stem in ('a', 'scene.a'):
            (self.root / f'{stem}.json').write_text(
                json.dumps({'scene_id': stem, 'description': stem}), encoding='utf-8')
        self.assertEqual(self.loader.load_scene('a')['description'], 'a')
        self.assertEqual(self.loader.load_scene('scene.a')['description'], 'scene.a')

    def test_flat_override_missing_file_error_is_preserved(self):
        with self.assertRaisesRegex(FileNotFoundError, 'Attempted'):
            self.loader.load_scene('missing')


if __name__ == '__main__':
    unittest.main()
