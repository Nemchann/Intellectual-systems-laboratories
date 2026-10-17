from collections import deque


def neighbors(node_id, relation_id, triples, nodes):
    """
    Возвращает узлы, связанные с заданным узлом
    исходящими связями указанного типа.

    node_id — ID исходного узла, например PLT-001.
    relation_id — ID отношения, например REL-004.
    triples — список троек из triples.json.
    nodes — список узлов из nodes.json.
    """

    # Находим тройки с нужным субъектом и отношением
    object_ids = [
        triple["object"]
        for triple in triples
        if triple.get("subject") == node_id
        and triple.get("relation") == relation_id
        and "object" in triple
    ]

    # Создаём словарь для быстрого поиска узлов по ID
    nodes_by_id = {
        node["id"]: node
        for node in nodes
    }

    # Возвращаем найденные узлы
    return [
        nodes_by_id[object_id]
        for object_id in object_ids
        if object_id in nodes_by_id
    ]



def find_path(source_id, target_id, triples, nodes):
    """
    Находит кратчайший направленный путь между двумя узлами.

    Возвращает список троек, составляющих путь.
    Если путь не найден, возвращает None.
    """
    nodes_by_id = {
        node["id"]: node
        for node in nodes
    }

    if source_id not in nodes_by_id or target_id not in nodes_by_id:
        return None

    if source_id == target_id:
        return []

    # Строим список исходящих связей для каждого узла.
    adjacency = {}

    for triple in triples:
        subject_id = triple.get("subject")
        object_id = triple.get("object")

        adjacency.setdefault(subject_id, []).append(triple)

    # Очередь для поиска в ширину.
    queue = deque([source_id])
    visited = {source_id}
    previous = {}

    while queue:
        current_id = queue.popleft()

        for triple in adjacency.get(current_id, []):
            next_id = triple.get("object")

            if next_id in visited:
                continue

            visited.add(next_id)
            previous[next_id] = triple

            if next_id == target_id:
                # Восстанавливаем путь от цели к началу.
                path = []
                current = target_id

                while current != source_id:
                    path_triple = previous[current]
                    path.append(path_triple)
                    current = path_triple["subject"]

                path.reverse()
                return path

            queue.append(next_id)

    return None
