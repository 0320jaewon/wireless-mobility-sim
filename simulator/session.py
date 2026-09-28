class Session:
    def __init__(self, node_id, application_id, port, ip_address):
        self.node_id = node_id
        self.application_id = application_id
        self.port = port
        self.ip_address = ip_address


class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.reset_log = []
        self._session_domain = {}
        self._ip_counters = {}

    def _allocate_ip(self, domain_id):
        counter = self._ip_counters.get(domain_id, 1)
        self._ip_counters[domain_id] = counter + 1 if counter < 254 else 1
        return f"10.{domain_id}.0.{counter}"

    def init_session(self, node, application_id=0, port=5000):
        ip = self._allocate_ip(node.domain_id)
        node.ip_address = ip
        self.sessions[node.node_id] = Session(node.node_id, application_id, port, ip)
        self._session_domain[node.node_id] = node.domain_id

    def update(self, node, timestep):
        session = self.sessions[node.node_id]
        prev_domain = self._session_domain[node.node_id]

        if node.domain_id == prev_domain:
            return False

        old_ip = session.ip_address
        new_ip = self._allocate_ip(node.domain_id)
        session.ip_address = new_ip
        node.ip_address = new_ip
        self._session_domain[node.node_id] = node.domain_id

        self.reset_log.append({
            "node_id": node.node_id,
            "timestep": timestep,
            "old_ip": old_ip,
            "new_ip": new_ip,
            "old_domain": prev_domain,
            "new_domain": node.domain_id,
        })
        return True
