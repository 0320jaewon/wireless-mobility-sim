from simulator.mobility import signal_strength


class MarkovPredictor:
    def __init__(self):
        self.transitions = {}

    def update(self, node_id, context, next_cell):
        current_cell = context
        node_transitions = self.transitions.setdefault(node_id, {})
        counts = node_transitions.setdefault(current_cell, {})
        counts[next_cell] = counts.get(next_cell, 0) + 1

    def predict_next(self, node_id, context):
        current_cell = context
        node_transitions = self.transitions.get(node_id)
        if not node_transitions:
            return None
        counts = node_transitions.get(current_cell)
        if not counts:
            return None
        return max(counts.items(), key=lambda item: (item[1], -item[0]))[0]


class FirstOrderMarkovPredictor:
    def __init__(self):
        self.transitions = {}
        self.fallback = {}

    def update(self, node_id, context, next_cell):
        prev_cell, current_cell = context

        node_transitions = self.transitions.setdefault(node_id, {})
        counts = node_transitions.setdefault((prev_cell, current_cell), {})
        counts[next_cell] = counts.get(next_cell, 0) + 1

        node_fallback = self.fallback.setdefault(node_id, {})
        fallback_counts = node_fallback.setdefault(current_cell, {})
        fallback_counts[next_cell] = fallback_counts.get(next_cell, 0) + 1

    def predict_next(self, node_id, context):
        prev_cell, current_cell = context

        node_transitions = self.transitions.get(node_id)
        if node_transitions:
            counts = node_transitions.get((prev_cell, current_cell))
            if counts:
                return max(counts.items(), key=lambda item: (item[1], -item[0]))[0]

        node_fallback = self.fallback.get(node_id)
        if node_fallback:
            fallback_counts = node_fallback.get(current_cell)
            if fallback_counts:
                return max(fallback_counts.items(), key=lambda item: (item[1], -item[0]))[0]

        return None


def _build_predictor(predictor_order):
    if predictor_order == "first":
        return FirstOrderMarkovPredictor()
    return MarkovPredictor()


class AIAlgorithm:
    def __init__(
        self,
        ho_threshold=5.0,
        ho_timer=3,
        ho_threshold_predicted=2.5,
        ho_timer_predicted=1,
        lu_period=15,
        predictor_order="zero",
    ):
        self.ho_threshold = ho_threshold
        self.ho_timer = ho_timer
        self.ho_threshold_predicted = ho_threshold_predicted
        self.ho_timer_predicted = ho_timer_predicted
        self.lu_period = lu_period
        self.predictor_order = predictor_order

        self.predictor = _build_predictor(predictor_order)
        self.last_lu_step = {}
        self.candidate_cell = {}
        self.candidate_duration = {}
        self.prev_cell = {}

        self.ho_log = []
        self.lu_log = []
        self.paging_log = []
        self.prediction_log = []

    def init_node(self, node):
        self.last_lu_step[node.node_id] = 0
        self.candidate_cell[node.node_id] = None
        self.candidate_duration[node.node_id] = 0
        self.prev_cell[node.node_id] = None

    def _context(self, node_id, current_cell):
        if self.predictor_order == "first":
            return (self.prev_cell.get(node_id), current_cell)
        return current_cell

    def step_handover(self, node, topology, timestep):
        node_id = node.node_id
        current_cell = node.cell_id
        current_signal = signal_strength(topology.distance_to_cell(current_cell, node.x, node.y))
        context = self._context(node_id, current_cell)
        predicted_cell = self.predictor.predict_next(node_id, context)

        best_cell = None
        best_signal = None
        best_is_predicted = False
        for neighbor_id in topology.get_neighbors(current_cell):
            neighbor_signal = signal_strength(topology.distance_to_cell(neighbor_id, node.x, node.y))
            is_predicted = neighbor_id == predicted_cell
            threshold = self.ho_threshold_predicted if is_predicted else self.ho_threshold
            if neighbor_signal > current_signal + threshold:
                if best_signal is None or neighbor_signal > best_signal:
                    best_signal = neighbor_signal
                    best_cell = neighbor_id
                    best_is_predicted = is_predicted

        if best_cell is None:
            self.candidate_cell[node_id] = None
            self.candidate_duration[node_id] = 0
            return False

        if self.candidate_cell.get(node_id) == best_cell:
            self.candidate_duration[node_id] += 1
        else:
            self.candidate_cell[node_id] = best_cell
            self.candidate_duration[node_id] = 1

        required_timer = self.ho_timer_predicted if best_is_predicted else self.ho_timer
        if self.candidate_duration[node_id] < required_timer:
            return False

        from_domain = node.domain_id
        node.cell_id = best_cell
        node.domain_id = topology.get_cell(best_cell).domain_id

        self.ho_log.append({
            "node_id": node_id,
            "timestep": timestep,
            "from_cell": current_cell,
            "to_cell": best_cell,
            "from_domain": from_domain,
            "to_domain": node.domain_id,
        })
        self.prediction_log.append({
            "node_id": node_id,
            "timestep": timestep,
            "predicted_cell": predicted_cell,
            "actual_cell": best_cell,
        })

        self.predictor.update(node_id, context, best_cell)
        self.prev_cell[node_id] = current_cell
        self.candidate_cell[node_id] = None
        self.candidate_duration[node_id] = 0
        return True

    def step_lm(self, node, timestep):
        last = self.last_lu_step.get(node.node_id, 0)
        if timestep - last >= self.lu_period:
            self.last_lu_step[node.node_id] = timestep
            self.lu_log.append({"node_id": node.node_id, "timestep": timestep})
            return True
        return False

    def get_paging_cells(self, node, topology):
        context = self._context(node.node_id, node.cell_id)
        predicted_cell = self.predictor.predict_next(node.node_id, context)
        if predicted_cell is None:
            return topology.all_cell_ids()

        cells = {predicted_cell}
        cells.update(topology.get_neighbors(predicted_cell))
        return list(cells)

    def trigger_paging(self, node, topology, timestep):
        cells = self.get_paging_cells(node, topology)
        self.paging_log.append({
            "node_id": node.node_id,
            "timestep": timestep,
            "cell_count": len(cells),
        })
        return cells
