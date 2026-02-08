# WorldField - Phase 0 Nucleus
# Chunked 2D float field with 4 core ops
# Python authority with Godot bridge

class Chunk:
    __slots__ = ('chunk_key', 'size', 'data', 'dirty')

    def __init__(self, chunk_key, size=32):
        self.chunk_key = chunk_key
        self.size = size
        self.data = [0.0] * (size * size)
        self.dirty = False

    def get_index(self, local_x, local_y):
        return local_y * self.size + local_x

    def get(self, x, y):
        return self.data[self.get_index(x, y)]

    def set(self, x, y, value):
        self.data[self.get_index(x, y)] = value
        self.dirty = True


class WorldField:
    def __init__(self, chunk_size=32):
        self.chunk_size = chunk_size
        self.chunks = {}

    def get_chunk_key(self, world_x, world_y):
        return (world_x // self.chunk_size, world_y // self.chunk_size)

    def get_local_coords(self, world_x, world_y):
        cx, cy = self.get_chunk_key(world_x, world_y)
        return (world_x - (cx * self.chunk_size), world_y - (cy * self.chunk_size))

    def get_or_create_chunk(self, world_x, world_y):
        key = self.get_chunk_key(world_x, world_y)
        if key not in self.chunks:
            self.chunks[key] = Chunk(key, self.chunk_size)
        return self.chunks[key]

    def get_chunk_at(self, world_x, world_y):
        key = self.get_chunk_key(world_x, world_y)
        return self.chunks.get(key)

    def apply_operator(self, operator, center_x, center_y, **kwargs):
        if operator == 'add':
            self._apply_add(center_x, center_y, kwargs.get('radius', 3), kwargs.get('strength', 1.0))
        elif operator == 'subtract':
            self._apply_subtract(center_x, center_y, kwargs.get('radius', 3), kwargs.get('strength', 1.0))
        elif operator == 'smooth':
            self._apply_smooth(center_x, center_y, kwargs.get('radius', 2))
        elif operator == 'clamp':
            self._apply_clamp(center_x, center_y, kwargs.get('min_val', 0.0), kwargs.get('max_val', 1.0))

    def _apply_add(self, center_x, center_y, radius, strength):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                chunk = self.get_or_create_chunk(center_x + dx, center_y + dy)
                if chunk:
                    lx, ly = self.get_local_coords(center_x + dx, center_y + dy)
                    if 0 <= lx < chunk.size and 0 <= ly < chunk.size:
                        current = chunk.get(lx, ly)
                        chunk.set(lx, ly, min(1.0, current + strength))

    def _apply_subtract(self, center_x, center_y, radius, strength):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                chunk = self.get_chunk_at(center_x + dx, center_y + dy)
                if chunk:
                    lx, ly = self.get_local_coords(center_x + dx, center_y + dy)
                    if 0 <= lx < chunk.size and 0 <= ly < chunk.size:
                        current = chunk.get(lx, ly)
                        chunk.set(lx, ly, max(0.0, current - strength))

    def _apply_smooth(self, center_x, center_y, radius):
        affected_chunks = set()
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                chunk = self.get_chunk_at(center_x + dx, center_y + dy)
                if chunk:
                    affected_chunks.add(chunk)

        for chunk in affected_chunks:
            data_copy = list(chunk.data)
            for y in range(chunk.size):
                for x in range(chunk.size):
                    total = 0.0
                    count = 0
                    for ny in range(max(0, y - radius), min(chunk.size, y + radius + 1)):
                        for nx in range(max(0, x - radius), min(chunk.size, x + radius + 1)):
                            total += data_copy[ny * chunk.size + nx]
                            count += 1
                    if count > 0:
                        chunk.set(x, y, total / count)

    def _apply_clamp(self, center_x, center_y, min_val, max_val):
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                chunk = self.get_chunk_at(center_x + dx, center_y + dy)
                if chunk:
                    lx, ly = self.get_local_coords(center_x + dx, center_y + dy)
                    if 0 <= lx < chunk.size and 0 <= ly < chunk.size:
                        current = chunk.get(lx, ly)
                        chunk.set(lx, ly, max(min_val, min(max_val, current)))

    def get_dirty_chunks(self):
        return [c for c in self.chunks.values() if c.dirty]

    def clear_dirty_flags(self):
        for chunk in self.chunks.values():
            chunk.dirty = False


class GodotWorldFieldBridge:
    def __init__(self, world_field):
        self.world_field = world_field
        self.chunk_meshes = {}

    def handle_edit(self, world_x, world_y, operator='add', **kwargs):
        grid_x, grid_y = int(world_x), int(world_y)
        self.world_field.apply_operator(operator, grid_x, grid_y, **kwargs)
        return self.get_dirty_data()

    def get_dirty_data(self):
        dirty_chunks = self.world_field.get_dirty_chunks()
        dirty_data = []
        for chunk in dirty_chunks:
            cx, cy = chunk.chunk_key
            dirty_data.append({
                'chunk_key': (cx, cy),
                'data': list(chunk.data),
                'size': chunk.size
            })
        self.world_field.clear_dirty_flags()
        return dirty_data


if __name__ == "__main__":
    field = WorldField(chunk_size=32)
    bridge = GodotWorldFieldBridge(field)

    bridge.handle_edit(64.0, 64.0, 'add', radius=4, strength=0.3)
    bridge.handle_edit(70.0, 70.0, 'subtract', radius=3, strength=0.2)
    bridge.handle_edit(64.0, 64.0, 'smooth', radius=2)
    bridge.handle_edit(64.0, 64.0, 'clamp', min_val=0.1, max_val=0.8)

    print(f"Chunks: {len(field.chunks)}, Center value: {field.get_chunk_at(64, 64).get(0, 0)}")
