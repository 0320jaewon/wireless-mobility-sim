def compute_signaling_overhead(lu_log, paging_log):
    lu_count = len(lu_log)
    paging_messages = sum(event["cell_count"] for event in paging_log)
    return lu_count + paging_messages


def compute_ping_pong_ratio(ho_log, window=5):
    total_ho = len(ho_log)
    if total_ho == 0:
        return 0.0

    events_by_node = {}
    for event in ho_log:
        events_by_node.setdefault(event["node_id"], []).append(event)

    pingpong_count = 0
    for node_id, events in events_by_node.items():
        events = sorted(events, key=lambda e: e["timestep"])
        for i in range(1, len(events)):
            prev_event = events[i - 1]
            curr_event = events[i]
            within_window = curr_event["timestep"] - prev_event["timestep"] <= window
            reversed_hop = (
                curr_event["from_cell"] == prev_event["to_cell"]
                and curr_event["to_cell"] == prev_event["from_cell"]
            )
            if within_window and reversed_hop:
                pingpong_count += 1

    return pingpong_count / total_ho


def compute_call_drop_approx(signal_log, drop_threshold):
    if not signal_log:
        return 0.0
    dropped = sum(1 for record in signal_log if record["signal"] < drop_threshold)
    return dropped / len(signal_log)


def compute_session_reset_count(reset_log):
    return len(reset_log)


def compute_session_continuity_rate(reset_log, num_nodes, num_timesteps):
    total_node_steps = num_nodes * num_timesteps
    if total_node_steps == 0:
        return 1.0
    return 1.0 - (len(reset_log) / total_node_steps)


def compute_session_metrics(reset_log, num_nodes, num_timesteps):
    return {
        "session_reset_count": compute_session_reset_count(reset_log),
        "session_continuity_rate": compute_session_continuity_rate(reset_log, num_nodes, num_timesteps),
    }


def compute_prediction_accuracy(prediction_log):
    evaluated = [e for e in prediction_log if e["predicted_cell"] is not None]
    if not evaluated:
        return 0.0
    correct = sum(1 for e in evaluated if e["predicted_cell"] == e["actual_cell"])
    return correct / len(evaluated)


def compute_basic_metrics(lu_log, paging_log, ho_log, signal_log, drop_threshold, pingpong_window=5):
    return {
        "signaling_overhead": compute_signaling_overhead(lu_log, paging_log),
        "ping_pong_ratio": compute_ping_pong_ratio(ho_log, window=pingpong_window),
        "call_drop_approx": compute_call_drop_approx(signal_log, drop_threshold),
        "ho_count": len(ho_log),
        "lu_count": len(lu_log),
        "paging_count": len(paging_log),
    }
