# TODO: Search for another way to count the number of connections, because
# the current one, could be very inefficient for large graphs.
from igraph import Graph


def get_outgoing_connections(graph: Graph, source_node: str) -> int:
    """
    Returns the number of outgoing connections from the specified node
    from the adjacency matrix.

    Args:
        graph (Graph): The igraph Graph object.
        source_node (str): The name of the node to check.

    Returns:
        int: The number of outgoing connections from the specified node.
    """
    vertex_names = graph.vs["name"]
    adjacency = graph.get_adjacency()
    i = vertex_names.index(source_node) if source_node in vertex_names else -1
    if i == -1:
        return 0

    return sum(adjacency[i]) if i < len(adjacency) else 0


def get_incoming_connections(graph: Graph, target_node: str) -> int:
    """
    Returns the number of incoming connections to the specified node
    from the adjacency matrix.

    Args:
        graph (Graph): The igraph Graph object.
        target_node (str): The name of the node to check.

    Returns:
        int: The number of incoming connections to the specified node.
    """
    vertex_names = graph.vs["name"]
    adjacency = graph.get_adjacency()
    i = vertex_names.index(target_node) if target_node in vertex_names else -1
    if i == -1:
        return 0
    return sum(list(map(lambda row: row[i], adjacency))) if i < len(adjacency) else 0


def has_cyclic_dependencies(graph: Graph) -> bool:
    """
    Checks if the graph has cyclic dependencies.

    Args:
        graph (Graph): The igraph Graph object.

    Returns:
        bool: True if the graph has cyclic dependencies, False otherwise.
    """
    return not graph.is_dag()  # Directed Acyclic Graph check
