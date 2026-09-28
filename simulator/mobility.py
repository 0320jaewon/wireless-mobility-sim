import math


class MobileNode:
    def __init__(self, node_id, x, y, speed, cell_id, domain_id):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.speed = speed
        self.cell_id = cell_id
        self.domain_id = domain_id
        self.ip_address = None
        self.waypoint = None
        self.pause_remaining = 0
        self.direction = None
        self.segment_remaining = 0.0


def signal_strength(distance, max_signal=100.0, atten=10.0):
    return max_signal - atten * distance


def _clamp_reflect(pos, lo, hi):
    if pos < lo:
        pos = lo + (lo - pos)
    elif pos > hi:
        pos = hi - (pos - hi)
    return min(max(pos, lo), hi)


def _movement_bounds(topology, margin_ratio):
    min_x, max_x, min_y, max_y = topology.bounds()
    margin_x = (max_x - min_x) * margin_ratio
    margin_y = (max_y - min_y) * margin_ratio
    return min_x - margin_x, max_x + margin_x, min_y - margin_y, max_y + margin_y


def create_nodes(topology, num_nodes, speed, rng, margin_ratio=0.5):
    lo_x, hi_x, lo_y, hi_y = _movement_bounds(topology, margin_ratio)

    nodes = []
    for node_id in range(num_nodes):
        x = rng.uniform(lo_x, hi_x)
        y = rng.uniform(lo_y, hi_y)
        cell_id = topology.nearest_cell(x, y)
        domain_id = topology.get_cell(cell_id).domain_id
        node = MobileNode(node_id, x, y, speed, cell_id, domain_id)
        nodes.append(node)
    return nodes


def random_walk_step(node, topology, rng, margin_ratio=0.5):
    lo_x, hi_x, lo_y, hi_y = _movement_bounds(topology, margin_ratio)

    angle = rng.uniform(0, 2 * math.pi)
    new_x = node.x + node.speed * math.cos(angle)
    new_y = node.y + node.speed * math.sin(angle)

    node.x = _clamp_reflect(new_x, lo_x, hi_x)
    node.y = _clamp_reflect(new_y, lo_y, hi_y)


def random_waypoint_step(node, topology, rng, margin_ratio=0.5, pause_steps=0):
    lo_x, hi_x, lo_y, hi_y = _movement_bounds(topology, margin_ratio)

    if node.pause_remaining > 0:
        node.pause_remaining -= 1
        return

    if node.waypoint is None:
        node.waypoint = (rng.uniform(lo_x, hi_x), rng.uniform(lo_y, hi_y))

    wx, wy = node.waypoint
    dx, dy = wx - node.x, wy - node.y
    dist = math.hypot(dx, dy)

    if dist <= node.speed:
        node.x, node.y = wx, wy
        node.waypoint = None
        node.pause_remaining = pause_steps
    else:
        node.x += node.speed * dx / dist
        node.y += node.speed * dy / dist


_MANHATTAN_DIRECTIONS = {
    "N": (0, 1),
    "S": (0, -1),
    "E": (1, 0),
    "W": (-1, 0),
}
_MANHATTAN_OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


def manhattan_grid_step(node, topology, rng, margin_ratio=0.5, grid_spacing=1.5):
    lo_x, hi_x, lo_y, hi_y = _movement_bounds(topology, margin_ratio)

    if node.direction is None:
        node.direction = rng.choice(list(_MANHATTAN_DIRECTIONS.keys()))
        node.segment_remaining = rng.uniform(0, grid_spacing)

    remaining_speed = node.speed
    while remaining_speed > 0:
        dx, dy = _MANHATTAN_DIRECTIONS[node.direction]
        step = min(remaining_speed, node.segment_remaining)

        new_x = _clamp_reflect(node.x + dx * step, lo_x, hi_x)
        new_y = _clamp_reflect(node.y + dy * step, lo_y, hi_y)
        hit_boundary = new_x != node.x + dx * step or new_y != node.y + dy * step

        node.x, node.y = new_x, new_y
        node.segment_remaining -= step
        remaining_speed -= step

        if hit_boundary:
            node.direction = _MANHATTAN_OPPOSITE[node.direction]
            node.segment_remaining = grid_spacing
        elif node.segment_remaining <= 1e-9:
            choices = [d for d in _MANHATTAN_DIRECTIONS if d != _MANHATTAN_OPPOSITE[node.direction]]
            node.direction = rng.choice(choices)
            node.segment_remaining = grid_spacing


MOBILITY_MODELS = {
    "random_walk": random_walk_step,
    "random_waypoint": random_waypoint_step,
    "manhattan_grid": manhattan_grid_step,
}


def step_node(node, topology, rng, model="random_walk", margin_ratio=0.5, **kwargs):
    step_fn = MOBILITY_MODELS[model]
    step_fn(node, topology, rng, margin_ratio=margin_ratio, **kwargs)
