from simulator.mobility import MobileNode
from simulator.session import SessionManager


def make_node(node_id, domain_id):
    return MobileNode(node_id, x=0.0, y=0.0, speed=0.3, cell_id=0, domain_id=domain_id)


def test_init_session_assigns_ip_and_matches_domain():
    manager = SessionManager()
    node = make_node(0, domain_id=1)
    manager.init_session(node)

    assert node.ip_address is not None
    assert node.ip_address.startswith("10.1.")
    assert manager.reset_log == []


def test_update_without_domain_change_does_not_reset():
    manager = SessionManager()
    node = make_node(0, domain_id=0)
    manager.init_session(node)
    ip_before = node.ip_address

    result = manager.update(node, timestep=5)

    assert result is False
    assert node.ip_address == ip_before
    assert manager.reset_log == []


def test_update_with_domain_change_triggers_reset():
    manager = SessionManager()
    node = make_node(0, domain_id=0)
    manager.init_session(node)
    ip_before = node.ip_address

    node.domain_id = 1
    result = manager.update(node, timestep=7)

    assert result is True
    assert node.ip_address != ip_before
    assert node.ip_address.startswith("10.1.")
    assert len(manager.reset_log) == 1
    assert manager.reset_log[0]["node_id"] == 0
    assert manager.reset_log[0]["timestep"] == 7
    assert manager.reset_log[0]["old_domain"] == 0
    assert manager.reset_log[0]["new_domain"] == 1


def test_ip_addresses_are_unique_within_a_domain():
    manager = SessionManager()
    node_a = make_node(0, domain_id=0)
    node_b = make_node(1, domain_id=0)
    manager.init_session(node_a)
    manager.init_session(node_b)

    assert node_a.ip_address != node_b.ip_address


def test_repeated_domain_flip_flop_counts_each_reset():
    manager = SessionManager()
    node = make_node(0, domain_id=0)
    manager.init_session(node)

    node.domain_id = 1
    manager.update(node, timestep=1)
    node.domain_id = 0
    manager.update(node, timestep=2)

    assert len(manager.reset_log) == 2
