"""Tests for utility functions in src/services/utils.py"""

import pytest
from igraph import Graph

from src.services.utils import (
    get_incoming_connections,
    get_outgoing_connections,
    get_priority_level,
    has_cyclic_dependencies,
)


class TestOutgoingConnections:
    """Tests for get_outgoing_connections function"""

    def test_node_with_no_outgoing_connections(self):
        # Excel input: Leaf node (A with no dependencies)
        g = Graph(directed=True)
        g.add_vertices(["A", "B"])
        g.add_edge("B", "A")  # B → A, so A has no outgoing edges
        
        assert get_outgoing_connections(g, "A") == 0

    def test_node_with_single_outgoing_connection(self):
        # Excel input: A depends on B
        g = Graph(directed=True)
        g.add_vertices(["A", "B"])
        g.add_edge("A", "B")
        
        assert get_outgoing_connections(g, "A") == 1

    def test_node_with_multiple_outgoing_connections(self):
        # Excel input: C depends on both A and B
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C"])
        g.add_edge("C", "A")
        g.add_edge("C", "B")
        
        assert get_outgoing_connections(g, "C") == 2

    def test_nonexistent_node_returns_zero(self):
        # Excel input: Node doesn't exist
        g = Graph(directed=True)
        g.add_vertices(["A", "B"])
        
        assert get_outgoing_connections(g, "X") == 0


class TestIncomingConnections:
    """Tests for get_incoming_connections function"""

    def test_node_with_no_incoming_connections(self):
        # Excel input: Root node (A with no dependencies, no incoming)
        g = Graph(directed=True)
        g.add_vertices(["A", "B"])
        g.add_edge("A", "B")  # A → B, so A has no incoming edges
        
        assert get_incoming_connections(g, "A") == 0

    def test_node_with_single_incoming_connection(self):
        # Excel input: A depends on B, so B has incoming from A
        g = Graph(directed=True)
        g.add_vertices(["A", "B"])
        g.add_edge("A", "B")
        
        assert get_incoming_connections(g, "B") == 1

    def test_node_with_multiple_incoming_connections(self):
        # Excel input: Both B and C depend on A
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C"])
        g.add_edge("B", "A")
        g.add_edge("C", "A")
        
        assert get_incoming_connections(g, "A") == 2

    def test_nonexistent_node_returns_zero(self):
        # Excel input: Node doesn't exist
        g = Graph(directed=True)
        g.add_vertices(["A", "B"])
        
        assert get_incoming_connections(g, "X") == 0


class TestHasCyclicDependencies:
    """Tests for has_cyclic_dependencies function"""

    def test_acyclic_single_node(self):
        # Excel input: Single independent node
        g = Graph(directed=True)
        g.add_vertices(["A"])
        
        assert has_cyclic_dependencies(g) is False

    def test_acyclic_linear_chain(self):
        # Excel input: A → B → C (linear dependencies)
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C"])
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        
        assert has_cyclic_dependencies(g) is False

    def test_acyclic_diamond_pattern(self):
        # Excel input: A, B=A, C=A, D=B+C
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C", "D"])
        g.add_edge("B", "A")
        g.add_edge("C", "A")
        g.add_edge("D", "B")
        g.add_edge("D", "C")
        
        assert has_cyclic_dependencies(g) is False

    def test_cyclic_self_loop(self):
        # Excel input: A = A (self-referential)
        g = Graph(directed=True)
        g.add_vertices(["A"])
        g.add_edge("A", "A")
        
        assert has_cyclic_dependencies(g) is True

    def test_cyclic_two_node_loop(self):
        # Excel input: A = B, B = A
        g = Graph(directed=True)
        g.add_vertices(["A", "B"])
        g.add_edge("A", "B")
        g.add_edge("B", "A")
        
        assert has_cyclic_dependencies(g) is True

    def test_cyclic_three_node_loop(self):
        # Excel input: A = B, B = C, C = A
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C"])
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("C", "A")
        
        assert has_cyclic_dependencies(g) is True

    def test_acyclic_empty_graph(self):
        # Excel input: Empty graph
        g = Graph(directed=True)
        
        assert has_cyclic_dependencies(g) is False

    def test_acyclic_no_edges(self):
        # Excel input: All independent nodes
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C", "D"])
        
        assert has_cyclic_dependencies(g) is False


class TestGetPriorityLevel:
    """Tests for get_priority_level function"""

    def test_single_independent_node_is_level_zero(self):
        # Excel input: A (no dependencies)
        g = Graph(directed=True)
        g.add_vertices(["A"])
        
        assert get_priority_level(g, "A") == 0

    def test_linear_chain_priorities(self):
        # Excel input: A, B=A, C=B
        # Dependencies: C→B→A
        # Expected: A=0, B=1, C=2
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C"])
        g.add_edge("B", "A")
        g.add_edge("C", "B")
        
        assert get_priority_level(g, "A") == 0
        assert get_priority_level(g, "B") == 1
        assert get_priority_level(g, "C") == 2

    def test_diamond_pattern_priorities(self):
        # Excel input: A, B=A, C=A, D=B+C
        # Dependencies: D→{B,C}, B→A, C→A
        # Priority calculation: sums all paths
        # A=0 (no deps), B=1+0=1, C=1+0=1, D=(1+1)+(1+1)=4
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C", "D"])
        g.add_edge("B", "A")
        g.add_edge("C", "A")
        g.add_edge("D", "B")
        g.add_edge("D", "C")
        
        assert get_priority_level(g, "A") == 0
        assert get_priority_level(g, "B") == 1
        assert get_priority_level(g, "C") == 1
        assert get_priority_level(g, "D") == 4

    def test_complex_tree_priorities(self):
        # Excel input: A, B=A, C=B, D=A, E=D
        #
        #     A (0)
        #    / \
        #   B   D (1 each: 1+0)
        #   |   |
        #   C   E (2 each: 1+1)
        #
        # Actually: C = 1 + get_priority_level(B) = 1 + (1 + 0) = 2
        #          E = 1 + get_priority_level(D) = 1 + (1 + 0) = 2
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C", "D", "E"])
        g.add_edge("B", "A")
        g.add_edge("C", "B")
        g.add_edge("D", "A")
        g.add_edge("E", "D")
        
        assert get_priority_level(g, "A") == 0
        assert get_priority_level(g, "B") == 1
        assert get_priority_level(g, "C") == 2
        assert get_priority_level(g, "D") == 1
        assert get_priority_level(g, "E") == 2

    def test_nonexistent_node_returns_zero(self):
        # Excel input: Node not in graph
        g = Graph(directed=True)
        g.add_vertices(["A", "B"])
        g.add_edge("B", "A")
        
        assert get_priority_level(g, "X") == 0

    def test_cyclic_graph_raises_error(self):
        # Excel input: A = B, B = A (cyclic)
        g = Graph(directed=True)
        g.add_vertices(["A", "B"])
        g.add_edge("A", "B")
        g.add_edge("B", "A")
        
        with pytest.raises(ValueError, match="not a directed acyclic graph"):
            get_priority_level(g, "A")

    def test_complex_dependencies_five_levels(self):
        # Excel input: Deep chain: A→B→C→D→E
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C", "D", "E"])
        g.add_edge("B", "A")
        g.add_edge("C", "B")
        g.add_edge("D", "C")
        g.add_edge("E", "D")
        
        assert get_priority_level(g, "E") == 4
        assert get_priority_level(g, "D") == 3
        assert get_priority_level(g, "C") == 2
        assert get_priority_level(g, "B") == 1
        assert get_priority_level(g, "A") == 0

    def test_multiple_independent_branches(self):
        # Excel input: A, B=A, C=A, D, E=D, F=D
        # Two independent trees rooted at A and D
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C", "D", "E", "F"])
        g.add_edge("B", "A")
        g.add_edge("C", "A")
        g.add_edge("E", "D")
        g.add_edge("F", "D")
        
        assert get_priority_level(g, "A") == 0
        assert get_priority_level(g, "D") == 0
        assert get_priority_level(g, "B") == 1
        assert get_priority_level(g, "C") == 1
        assert get_priority_level(g, "E") == 1
        assert get_priority_level(g, "F") == 1

    @pytest.mark.parametrize("node", ["A", "B", "C"])
    def test_all_independent_nodes_are_level_zero(self, node):
        # Excel input: All independent nodes A, B, C
        g = Graph(directed=True)
        g.add_vertices(["A", "B", "C"])
        
        assert get_priority_level(g, node) == 0
