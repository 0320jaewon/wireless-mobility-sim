from simulator.ai_predictor import AIAlgorithm, FirstOrderMarkovPredictor, MarkovPredictor
from simulator.mobility import MobileNode
from simulator.topology import assign_domains, create_hex_grid


def test_markov_predictor_returns_none_without_history():
    predictor = MarkovPredictor()
    assert predictor.predict_next(node_id=0, context=5) is None


def test_markov_predictor_predicts_most_frequent_next_cell():
    predictor = MarkovPredictor()
    predictor.update(node_id=0, context=5, next_cell=6)
    predictor.update(node_id=0, context=5, next_cell=6)
    predictor.update(node_id=0, context=5, next_cell=9)

    assert predictor.predict_next(node_id=0, context=5) == 6


def test_markov_predictor_is_per_node():
    predictor = MarkovPredictor()
    predictor.update(node_id=0, context=5, next_cell=6)
    assert predictor.predict_next(node_id=1, context=5) is None


def test_first_order_predictor_uses_exact_prev_current_pair():
    predictor = FirstOrderMarkovPredictor()
    predictor.update(node_id=0, context=(1, 5), next_cell=6)
    predictor.update(node_id=0, context=(1, 5), next_cell=6)
    predictor.update(node_id=0, context=(2, 5), next_cell=9)

    assert predictor.predict_next(node_id=0, context=(1, 5)) == 6
    assert predictor.predict_next(node_id=0, context=(2, 5)) == 9


def test_first_order_predictor_falls_back_to_zero_order():
    predictor = FirstOrderMarkovPredictor()
    predictor.update(node_id=0, context=(1, 5), next_cell=6)
    predictor.update(node_id=0, context=(1, 5), next_cell=6)

    unseen_context = (99, 5)
    assert predictor.predict_next(node_id=0, context=unseen_context) == 6


def test_first_order_predictor_returns_none_without_any_history():
    predictor = FirstOrderMarkovPredictor()
    assert predictor.predict_next(node_id=0, context=(1, 5)) is None


def test_ai_algorithm_paging_falls_back_to_all_cells_when_no_prediction():
    topology = create_hex_grid(rows=5, cols=5, cell_size=1.0)
    assign_domains(topology, num_domains=2)
    algorithm = AIAlgorithm()

    node = MobileNode(0, x=0.0, y=0.0, speed=0.3, cell_id=12, domain_id=0)
    algorithm.init_node(node)

    cells = algorithm.get_paging_cells(node, topology)
    assert set(cells) == set(topology.all_cell_ids())


def test_ai_algorithm_paging_narrows_to_predicted_cell_and_neighbors():
    topology = create_hex_grid(rows=5, cols=5, cell_size=1.0)
    assign_domains(topology, num_domains=2)
    algorithm = AIAlgorithm()

    node = MobileNode(0, x=0.0, y=0.0, speed=0.3, cell_id=12, domain_id=0)
    algorithm.init_node(node)
    algorithm.predictor.update(node_id=0, context=12, next_cell=13)

    cells = algorithm.get_paging_cells(node, topology)
    expected = {13} | set(topology.get_neighbors(13))
    assert set(cells) == expected
    assert len(cells) < len(topology.all_cell_ids())
