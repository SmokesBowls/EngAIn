from trixel_brush_adapter import AssetRegistry
from pathlib import Path
registry = AssetRegistry()
registry.load_from_directory(Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/data"))
print(registry.flares)
print(registry.errors)
