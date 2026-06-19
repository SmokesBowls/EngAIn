import unittest

from gui.older_zw_gui_enhanced import ZWEditorCore
from gui.zw.zw_parser import parse_zw
from gui.zon.zon_binary_pack import (
    pack_zonj,
    unpack_zonb,
    DEFAULT_FIELD_IDS,
)


def collect_field_number_leaks(obj, found=None, path="root"):
    if found is None:
        found = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str) and key.startswith("field_"):
                found.append((path, key, value))
            collect_field_number_leaks(value, found, f"{path}.{key}")

    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            collect_field_number_leaks(item, found, f"{path}[{index}]")

    return found


class TestGuiLocalZonbRoundtrip(unittest.TestCase):
    def test_field_id_registry_has_no_collisions(self):
        reverse = {}
        collisions = []

        for name, field_id in DEFAULT_FIELD_IDS.items():
            if field_id in reverse:
                collisions.append((field_id, reverse[field_id], name))
            reverse[field_id] = name

        self.assertEqual(collisions, [])

    def test_all_builtin_templates_roundtrip_without_field_number_leaks(self):
        core = ZWEditorCore()

        for template_name in ["container", "npc", "room", "item", "rule"]:
            with self.subTest(template=template_name):
                zw_text = core.get_template(template_name)

                parsed = parse_zw(zw_text)
                packed = pack_zonj(parsed)
                unpacked = unpack_zonb(packed)

                leaks = collect_field_number_leaks(unpacked)

                self.assertEqual(
                    leaks,
                    [],
                    f"{template_name} leaked unnamed ZONB fields: {leaks}",
                )

                self.assertEqual(
                    unpacked,
                    parsed,
                    f"{template_name} did not survive ZONB roundtrip unchanged",
                )


if __name__ == "__main__":
    unittest.main()
