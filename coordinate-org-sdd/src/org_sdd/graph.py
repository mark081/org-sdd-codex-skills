"""Deterministic stage graph, independent of approvals and evidence readiness.

build_graph(dataset) returns StageGraph. Nodes are (record_id, stage) tuples;
edges point prerequisite -> dependent. dependency_details retains authored
obligations/evidence for later checks. order contains all structurally usable,
acyclic nodes, including descendants of cycles only in blocked_nodes (never in
order). Acyclic graph membership is not proof of readiness.
"""
from dataclasses import dataclass, field
import heapq

from .diagnostics import Diagnostic, sorted_diagnostics
from .records import STAGES


@dataclass
class StageGraph:
    nodes: set = field(default_factory=set)
    prerequisites: dict = field(default_factory=dict)
    dependents: dict = field(default_factory=dict)
    dependency_details: dict = field(default_factory=dict)
    order: list = field(default_factory=list)
    cycles: list = field(default_factory=list)
    blocked_nodes: set = field(default_factory=set)
    diagnostics: list = field(default_factory=list)
    structural_valid: bool = True

    def ancestors(self, node):
        """All transitive prerequisites, safely terminating on cycles."""
        return self._closure(node, self.prerequisites)

    def descendants(self, node):
        return self._closure(node, self.dependents)

    @staticmethod
    def _closure(node, edges):
        found, pending = set(), list(edges.get(node, ()))
        while pending:
            current = pending.pop()
            if current in found: continue
            found.add(current); pending.extend(edges.get(current, ()))
        found.discard(node)
        return found


def build_graph(dataset):
    graph = StageGraph()
    if not dataset.valid:
        graph.structural_valid = False
        graph.diagnostics = list(dataset.diagnostics)
        return graph
    supported = {"contract": ("contract_approved",), "handoff": STAGES, "initiative": ("integration", "release")}
    for identity, record in dataset.records.items():
        for stage in supported.get(record["kind"], ()):
            node = (identity, stage)
            graph.nodes.add(node); graph.prerequisites[node] = set(); graph.dependents[node] = set()

    def add(producer, consumer, field_name, detail=None):
        if producer not in graph.nodes or consumer not in graph.nodes:
            identity = consumer[0]
            code = "REFERENCE_UNRESOLVED" if producer[0] not in dataset.records else "FORMAT_INVALID"
            graph.diagnostics.append(Diagnostic(code, dataset.files.get(identity, "<record>"), identity, field_name, "Dependency must identify an existing supported stage"))
            graph.structural_valid = False
            return
        graph.prerequisites[consumer].add(producer); graph.dependents[producer].add(consumer)
        if detail is not None: graph.dependency_details.setdefault((producer, consumer), []).append(detail)

    initiative = dataset.initiative
    for identity in sorted(dataset.records):
        record = dataset.records[identity]
        if record["kind"] != "handoff": continue
        add((identity, "planning"), (identity, "execution"), "intrinsic")
        add((identity, "execution"), (identity, "local_complete"), "intrinsic")
        for index, obligation in enumerate(record["obligations"]):
            add((obligation["record_id"], "contract_approved"), (identity, "planning"), f"obligations[{index}]")
        for index, dependency in enumerate(record["dependencies"]):
            add((dependency["producer_id"], dependency["required_stage"]), (identity, dependency["consumer_stage"]),
                f"dependencies[{index}]", dict(handoff_id=identity, field=f"dependencies[{index}]", dependency=dependency))
    for identity in initiative["required_handoffs"]:
        add((identity, "local_complete"), (initiative["id"], "integration"), "required_handoffs")
    for identity in initiative["required_contracts"]:
        add((identity, "contract_approved"), (initiative["id"], "integration"), "required_contracts")
    add((initiative["id"], "integration"), (initiative["id"], "release"), "intrinsic")
    if not graph.structural_valid:
        graph.blocked_nodes = set(graph.nodes)
        graph.diagnostics = sorted_diagnostics(graph.diagnostics)
        return graph

    # Iterative Kosaraju avoids recursion-limit failures on long valid plans.
    visited, finish = set(), []
    for start in sorted(graph.nodes):
        if start in visited: continue
        stack = [(start, False)]
        while stack:
            node, expanded = stack.pop()
            if expanded: finish.append(node); continue
            if node in visited: continue
            visited.add(node); stack.append((node, True))
            for dependent in reversed(sorted(graph.dependents[node])):
                if dependent not in visited: stack.append((dependent, False))
    assigned = set()
    for start in reversed(finish):
        if start in assigned: continue
        component, pending = set(), [start]
        while pending:
            node = pending.pop()
            if node in assigned: continue
            assigned.add(node); component.add(node)
            pending.extend(sorted(graph.prerequisites[node], reverse=True))
        if len(component) > 1 or start in graph.dependents[start]:
            graph.cycles.append(sorted(component))
    graph.cycles.sort()
    for component in graph.cycles:
        for node in component:
            graph.blocked_nodes.add(node); graph.blocked_nodes.update(graph.descendants(node))
        identities = ", ".join(identity + "/" + stage for identity, stage in component)
        first = component[0][0]
        graph.diagnostics.append(Diagnostic("DEPENDENCY_CYCLE", dataset.files.get(first, "<record>"), first, "dependencies",
                                            "Resolve stage cycle: " + identities))
    usable = graph.nodes - graph.blocked_nodes
    indegree = {node: len(graph.prerequisites[node] & usable) for node in usable}
    ready = [node for node, count in indegree.items() if count == 0]; heapq.heapify(ready)
    while ready:
        node = heapq.heappop(ready); graph.order.append(node)
        for dependent in sorted(graph.dependents[node] & usable):
            indegree[dependent] -= 1
            if indegree[dependent] == 0: heapq.heappush(ready, dependent)
    graph.diagnostics = sorted_diagnostics(graph.diagnostics)
    return graph
