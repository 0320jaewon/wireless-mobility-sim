from simulator.mobility import signal_strength


class ImprovedAlgorithm:
    def __init__(self, ho_threshold=5.0, ho_timer=3, lu_period=15):
        self.ho_threshold = ho_threshold
        self.ho_timer = ho_timer
        self.lu_period = lu_period
        self.last_lu_step = {}
        self.candidate_cell = {}
        self.candidate_duration = {}
        self.ho_log = []
        self.lu_log = []
        self.paging_log = []

    def init_node(self, node):
        self.last_lu_step[node.node_id] = 0
        self.candidate_cell[node.node_id] = None
        self.candidate_duration[node.node_id] = 0

    def step_handover(self, node, topology, timestep):
        node_id = node.node_id
        current_signal = signal_strength(topology.distance_to_cell(node.cell_id, node.x, node.y))

        best_cell = None
        best_signal = None
        for neighbor_id in topology.get_neighbors(node.cell_id):
            neighbor_signal = signal_strength(topology.distance_to_cell(neighbor_id, node.x, node.y))
            if neighbor_signal > current_signal + self.ho_threshold:
                if best_signal is None or neighbor_signal > best_signal:
                    best_signal = neighbor_signal
                    best_cell = neighbor_id

        if best_cell is None:
            self.candidate_cell[node_id] = None
            self.candidate_duration[node_id] = 0
            return False

        if self.candidate_cell.get(node_id) == best_cell:
            self.candidate_duration[node_id] += 1
        else:
            self.candidate_cell[node_id] = best_cell
            self.candidate_duration[node_id] = 1

        if self.candidate_duration[node_id] < self.ho_timer:
            return False

        from_cell = node.cell_id
        from_domain = node.domain_id
        node.cell_id = best_cell
        node.domain_id = topology.get_cell(best_cell).domain_id

        self.ho_log.append({
            "node_id": node_id,
            "timestep": timestep,
            "from_cell": from_cell,
            "to_cell": best_cell,
            "from_domain": from_domain,
            "to_domain": node.domain_id,
        })

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
        return topology.all_cell_ids()

    def trigger_paging(self, node, topology, timestep):
        cells = self.get_paging_cells(node, topology)
        self.paging_log.append({
            "node_id": node.node_id,
            "timestep": timestep,
            "cell_count": len(cells),
        })
        return cells
