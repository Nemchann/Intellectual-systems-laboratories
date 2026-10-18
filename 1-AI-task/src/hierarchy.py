
def ancestors(node_id, triples, nodes):
    """
    Возвращает всех предков класса,
    последовательно двигаясь от подкласса к общему классу.
    """
    hierarchy_relation = "REL-001"

    nodes_by_id = {
        node["id"]: node
        for node in nodes
    }

    result = []
    visited = {node_id}
    current_ids = [node_id]

    while current_ids:
        next_ids = []

        for current_id in current_ids:
            for triple in triples:
                if (
                    triple.get("subject") == current_id
                    and triple.get("relation") == hierarchy_relation
                ):
                    parent_id = triple.get("object")

                    if parent_id not in visited:
                        visited.add(parent_id)
                        next_ids.append(parent_id)

                        if parent_id in nodes_by_id:
                            result.append(nodes_by_id[parent_id])

        current_ids = next_ids

    return result


def descendants(node_id, triples, nodes):
    """
    Возвращает всех потомков класса,
    последовательно двигаясь от общего класса к подклассам.
    """
    hierarchy_relation = "REL-001"

    nodes_by_id = {
        node["id"]: node
        for node in nodes
    }

    result = []
    visited = {node_id}
    current_ids = [node_id]

    while current_ids:
        next_ids = []

        for current_id in current_ids:
            for triple in triples:
                if (
                    triple.get("object") == current_id
                    and triple.get("relation") == hierarchy_relation
                ):
                    child_id = triple.get("subject")

                    if child_id not in visited:
                        visited.add(child_id)
                        next_ids.append(child_id)

                        if child_id in nodes_by_id:
                            result.append(nodes_by_id[child_id])

        current_ids = next_ids

    return result
