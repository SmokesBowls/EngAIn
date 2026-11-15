"""The packet's authored @scene_meta_location/time anchor Pass 4's @where/@when, with provenance.

pipeline_runner used to pass a hardcoded "Unknown" location, so every scene read
Realm/Physical/Unknown even when the manuscript named the place and time.
"""

from pathlib import Path

from tier3.mettaext.passroom.pass4_zon_bridge import ZONMetadata
from tier3.mettaext.passroom.pass5_game_bridge import GameBridge
from tier3.mettaext.pipeline_runner import read_packet_scene_meta

PACKET = """@scene_id: scene.book001.003_first_contact.scene001
@scene_meta_location: Earth coastline landing beach
@scene_meta_time: day 1, first night
@scene_meta_focus:
---
@scene_meta_location: body text after the header is not metadata
"""


def test_packet_header_meta_is_read_up_to_the_separator(tmp_path: Path) -> None:
    packet = tmp_path / "p.txt"
    packet.write_text(PACKET, encoding="utf-8")
    assert read_packet_scene_meta(packet) == {
        "location": "Earth coastline landing beach", "time": "day 1, first night"}


def test_authored_anchors_win_and_say_so() -> None:
    anchors = ZONMetadata(authored_location="Earth coastline landing beach",
                          authored_time="day 1, first night").anchors("x")
    assert anchors["@where"] == "Realm/Physical/Earth coastline landing beach"
    assert anchors["@when"] == "day 1, first night"
    assert anchors["@anchor_provenance"] == {"when": "authored:@scene_meta_time",
                                             "where": "authored:@scene_meta_location"}


def test_without_authored_meta_the_default_is_labelled_default() -> None:
    anchors = ZONMetadata().anchors("x")
    assert anchors["@where"] == "Realm/Physical/Unknown" and anchors["@when"] == "Unknown.scene_x"
    assert anchors["@anchor_provenance"] == {"when": "default", "where": "default"}


def test_fixing_the_descriptive_location_assigns_no_persistent_identity() -> None:
    """Authoring @where changed locations[0].id ('unknown' -> 'earth coastline landing beach').

    That id is read off descriptive text, so it must say so, and the identities that are not
    derived from the location (scene id, entity ids) must not move when only the location does.
    """
    def convert(where: str) -> dict:
        zon = {"@id": "scene.book001.003_first_contact.scene001", "@where": where,
               "@entities": ["Senareth", "Vairis"], "=segments": []}
        return GameBridge().convert_zon_to_game(zon)

    default = convert(ZONMetadata().anchors("x")["@where"])
    authored = convert(ZONMetadata(authored_location="Earth coastline landing beach").anchors("x")["@where"])
    for scene in (default, authored):
        (location,) = scene["locations"]
        assert location["id_source"] == "derived:where_last_segment"
        assert location["identity"] == "unresolved"
    assert authored["scene_id"] == default["scene_id"] == "scene.book001.003_first_contact.scene001"
    assert [e["id"] for e in authored["entities"]] == [e["id"] for e in default["entities"]] == ["senareth", "vairis"]
