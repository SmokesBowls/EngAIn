import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from mesh_intake import intake_mesh, count_vertices_faces, compute_mesh_hash


def test_mesh_intake():
    print("=== MESH INTAKE TEST ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        obj_path = Path(tmpdir) / "test.obj"
        # Simple fake OBJ: 3 verts, 1 face
        obj_path.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")

        print("TEST 1: Count vertices/faces")
        verts, faces = count_vertices_faces(obj_path)
        assert verts == 3
        assert faces == 1
        print(f"  ✓ verts={verts}, faces={faces}")

        print("\nTEST 2: Hash is stable")
        h1 = compute_mesh_hash(obj_path)
        h2 = compute_mesh_hash(obj_path)
        assert h1 == h2
        assert len(h1) == 64
        print(f"  ✓ hash={h1[:16]}...")

        print("\nTEST 3: Intake produces manifest")
        manifest = intake_mesh(
            obj_path,
            zw_concept="test_guard",
            ap_profile="damageable_npc",
            collision_role="solid",
            lod_class="prop",
            placeholder_mesh="cube",
            source_tool="test",
        )
        assert manifest.zw_concept == "test_guard"
        assert manifest.geometry.vertex_count == verts
        assert manifest.geometry.face_count == faces
        assert manifest.is_valid
        print("  ✓ manifest valid")

    print("\n============================================================")
    print("✅ MESH INTAKE: ALL TESTS PASS")
    print("============================================================")


if __name__ == "__main__":
    test_mesh_intake()
