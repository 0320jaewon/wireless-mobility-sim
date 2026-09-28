import math


class Cell:
    def __init__(self, cell_id, row, col, x, y):
        self.cell_id = cell_id
        self.row = row
        self.col = col
        self.x = x
        self.y = y
        self.domain_id = None
        self.neighbor_ids = []


class Topology:
    def __init__(self, cells, domain_map):
        self.cells = cells
        self.domain_map = domain_map

    def get_cell(self, cell_id):
        return self.cells[cell_id]

    def get_neighbors(self, cell_id):
        return self.cells[cell_id].neighbor_ids

    def get_domain_cells(self, domain_id):
        return self.domain_map[domain_id]

    def all_cell_ids(self):
        return list(self.cells.keys())

    def nearest_cell(self, x, y):
        best_id = None
        best_dist = None
        for cell_id, cell in self.cells.items():
            d = math.hypot(cell.x - x, cell.y - y)
            if best_dist is None or d < best_dist:
                best_dist = d
                best_id = cell_id
        return best_id

    def distance_to_cell(self, cell_id, x, y):
        cell = self.cells[cell_id]
        return math.hypot(cell.x - x, cell.y - y)

    def bounds(self):
        xs = [c.x for c in self.cells.values()]
        ys = [c.y for c in self.cells.values()]
        return min(xs), max(xs), min(ys), max(ys)


def _axial_to_pixel(row, col, size):
    x = size * 1.5 * col
    y = size * math.sqrt(3) * (row + 0.5 * (col % 2))
    return x, y


def _offset_neighbors(row, col, cols_count, rows_count):
    even = col % 2 == 0
    if even:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]
    else:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1), (1, -1), (1, 1)]
    result = []
    for dr, dc in deltas:
        nr, nc = row + dr, col + dc
        if 0 <= nr < rows_count and 0 <= nc < cols_count:
            result.append((nr, nc))
    return result


def create_hex_grid(rows=5, cols=5, cell_size=1.0):
    cells = {}
    id_by_pos = {}
    cell_id = 0
    for row in range(rows):
        for col in range(cols):
            x, y = _axial_to_pixel(row, col, cell_size)
            cell = Cell(cell_id, row, col, x, y)
            cells[cell_id] = cell
            id_by_pos[(row, col)] = cell_id
            cell_id += 1

    for row in range(rows):
        for col in range(cols):
            cid = id_by_pos[(row, col)]
            neighbor_positions = _offset_neighbors(row, col, cols, rows)
            cells[cid].neighbor_ids = [id_by_pos[p] for p in neighbor_positions]

    domain_map = {}
    topology = Topology(cells, domain_map)
    return topology


def assign_domains(topology, num_domains=2):
    min_x, max_x, _, _ = topology.bounds()
    span = max_x - min_x
    if span == 0:
        span = 1.0

    domain_map = {d: [] for d in range(num_domains)}
    for cell in topology.cells.values():
        ratio = (cell.x - min_x) / span
        domain_id = min(int(ratio * num_domains), num_domains - 1)
        cell.domain_id = domain_id
        domain_map[domain_id].append(cell.cell_id)

    topology.domain_map = domain_map
    return topology
