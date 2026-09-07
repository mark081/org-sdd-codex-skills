from tests.org_helpers import bundle, record
from org_sdd.graph import build_graph
from org_sdd.records import Dataset, validate_records
from pathlib import Path
from copy import deepcopy
import random
import unittest


def dataset(records):
    return Dataset(Path("."), {r["id"]: r for r in records}, {r["id"]: r["id"] + ".json" for r in records}, validate_records(records))


def dependency(identity, producer, required="local_complete", consumer="execution"):
    return dict(id=identity, producer_id=producer, required_stage=required, consumer_stage=consumer, obligations=[], evidence_ids=[])


class Graph(unittest.TestCase):
    def test_intrinsic_edges_and_no_implementation_before_planning(self):
        records = bundle(); graph = build_graph(dataset(records))
        self.assertTrue(graph.structural_valid)
        self.assertEqual(graph.prerequisites[("work", "planning")], {("api", "contract_approved")})
        self.assertIn(("work", "execution"), graph.prerequisites[("work", "local_complete")])
        self.assertIn(("work", "local_complete"), graph.prerequisites[("demo", "integration")])
        self.assertIn(("demo", "integration"), graph.prerequisites[("demo", "release")])
        self.assertLess(graph.order.index(("api", "contract_approved")), graph.order.index(("work", "planning")))
        self.assertEqual(graph.cycles, [])

    def test_stage_cycle_blocks_descendants_not_independent_work(self):
        records = bundle(); other = record("handoff", "other"); independent = record("handoff", "independent")
        records.extend([other, independent])
        records[2]["dependencies"] = [dependency("wait", "other")]
        other["dependencies"] = [dependency("back", "work", "execution", "planning")]
        graph = build_graph(dataset(records))
        self.assertEqual(len(graph.cycles), 1)
        self.assertIn(("work", "execution"), graph.cycles[0])
        self.assertIn(("other", "local_complete"), graph.cycles[0])
        self.assertIn(("demo", "release"), graph.blocked_nodes)
        self.assertIn(("independent", "execution"), graph.order)
        self.assertIn(("work", "planning"), graph.order)
        self.assertEqual(graph.diagnostics[0].code, "DEPENDENCY_CYCLE")

    def test_self_cycle_and_redundant_edges(self):
        records = bundle(); records[2]["dependencies"] = [dependency("self", "work", "planning", "planning")]
        graph = build_graph(dataset(records)); self.assertEqual(graph.cycles, [[("work", "planning")]])
        records[2]["dependencies"] = [dependency("redundant", "work", "planning", "execution")]
        graph = build_graph(dataset(records)); self.assertFalse(graph.cycles)
        self.assertEqual(len(graph.dependency_details), 1)

    def test_dangling_wrong_kind_and_corruption(self):
        for producer, required in (("missing", "local_complete"), ("api", "execution")):
            records = bundle(); records[2]["dependencies"] = [dependency("bad", producer, required)]
            graph = build_graph(dataset(records))
            self.assertFalse(graph.structural_valid); self.assertFalse(graph.order)
        records = bundle(); records[0]["format_version"] = "unknown"
        self.assertFalse(build_graph(dataset(records)).structural_valid)

    def test_determinism_and_generated_dags_cycles(self):
        for size in range(2, 15):
            records = bundle(); handoffs = [records[2]] + [record("handoff", "work-" + str(i)) for i in range(1, size)]
            records.extend(handoffs[1:])
            for i in range(1, size):
                handoffs[i]["dependencies"] = [dependency("prior", handoffs[i-1]["id"])]
            graph = build_graph(dataset(records))
            self.assertFalse(graph.cycles)
            order = {node: i for i, node in enumerate(graph.order)}
            for consumer, producers in graph.prerequisites.items():
                for producer in producers: self.assertLess(order[producer], order[consumer])
            shuffled = deepcopy(records); random.Random(size).shuffle(shuffled)
            self.assertEqual(graph.order, build_graph(dataset(shuffled)).order)
            handoffs[0]["dependencies"] = [dependency("cycle", handoffs[-1]["id"])]
            cycle_graph = build_graph(dataset(records))
            self.assertTrue(cycle_graph.cycles)
            self.assertIn((handoffs[-1]["id"], "local_complete"), cycle_graph.blocked_nodes)

    def test_closures_and_detail_preservation(self):
        records = bundle(); extra = record("handoff", "extra"); records.append(extra)
        dep = dependency("prior", "work"); extra["dependencies"] = [dep]
        graph = build_graph(dataset(records))
        self.assertIn(("work", "planning"), graph.ancestors(("extra", "execution")))
        self.assertIn(("extra", "local_complete"), graph.descendants(("work", "execution")))
        self.assertEqual(graph.dependency_details[(("work", "local_complete"), ("extra", "execution"))][0]["dependency"], dep)


if __name__ == "__main__": unittest.main()
