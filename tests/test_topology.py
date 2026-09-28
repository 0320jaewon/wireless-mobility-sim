from simulator.topology import create_hex_grid, assign_domains


def test_create_hex_grid_cell_count():
    topology = create_hex_grid(rows=5, cols=5, cell_size=1.0)
    assert len(topology.cells) == 25


def test_neighbors_are_symmetric():
    topology = create_hex_grid(rows=5, cols=5, cell_size=1.0)
    for cell in topology.cells.values():
        for neighbor_id in cell.neighbor_ids:
            neighbor = topology.get_cell(neighbor_id)
            assert cell.cell_id in neighbor.neighbor_ids


def test_neighbor_count_within_hex_bounds():
    topology = create_hex_grid(rows=5, cols=5, cell_size=1.0)
    for cell in topology.cells.values():
        assert 2 <= len(cell.neighbor_ids) <= 6


def test_assign_domains_covers_every_cell_exactly_once():
    topology = create_hex_grid(rows=5, cols=5, cell_size=1.0)
    assign_domains(topology, num_domains=2)

    all_assigned = [cell_id for cells in topology.domain_map.values() for cell_id in cells]
    assert sorted(all_assigned) == sorted(topology.all_cell_ids())

    for cell in topology.cells.values():
        assert cell.domain_id in topology.domain_map
        assert cell.cell_id in topology.domain_map[cell.domain_id]


def test_nearest_cell_returns_closest():
    topology = create_hex_grid(rows=5, cols=5, cell_size=1.0)
    target = topology.get_cell(12)
    result = topology.nearest_cell(target.x + 0.05, target.y - 0.02)
    assert result == 12


def test_distance_to_cell_matches_euclidean():
    topology = create_hex_grid(rows=5, cols=5, cell_size=1.0)
    cell = topology.get_cell(0)
    distance = topology.distance_to_cell(0, cell.x + 3.0, cell.y + 4.0)
    assert distance == 5.0
