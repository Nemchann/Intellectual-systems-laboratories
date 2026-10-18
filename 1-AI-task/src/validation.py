
def validate(network):
    """
    Проверяет структуру семантической сети.

    network — словарь с ключами:
        nodes, relations, triples

    Возвращает список обнаруженных ошибок.
    Если список пустой, ошибок не найдено.
    """
    errors = []

    nodes = network.get("nodes", [])
    relations = network.get("relations", [])
    triples = network.get("triples", [])

    # 1. Проверяем уникальность ID узлов
    node_ids = [node.get("id") for node in nodes]

    if len(node_ids) != len(set(node_ids)):
        errors.append("Обнаружены повторяющиеся ID узлов.")

    # 2. Проверяем уникальность ID отношений
    relation_ids = [relation.get("id") for relation in relations]

    if len(relation_ids) != len(set(relation_ids)):
        errors.append("Обнаружены повторяющиеся ID отношений.")

    # 3. Проверяем уникальность ID троек
    triple_ids = [triple.get("id") for triple in triples]

    if len(triple_ids) != len(set(triple_ids)):
        errors.append("Обнаружены повторяющиеся ID троек.")

    # Создаём словари для быстрого поиска
    nodes_by_id = {
        node["id"]: node
        for node in nodes
        if node.get("id") is not None
    }

    relations_by_id = {
        relation["id"]: relation
        for relation in relations
        if relation.get("id") is not None
    }

    # 4. Проверяем обязательные поля узлов
    for node in nodes:
        for field in ("id", "name", "type", "description"):
            if not node.get(field):
                errors.append(
                    f"Узел {node.get('id', '<без ID>')}: "
                    f"отсутствует поле '{field}'."
                )

    # 5. Проверяем обязательные поля отношений
    for relation in relations:
        for field in (
            "id", "name", "meaning",
            "subject_types", "object_types"
        ):
            if field not in relation or relation[field] is None:
                errors.append(
                    f"Отношение {relation.get('id', '<без ID>')}: "
                    f"отсутствует поле '{field}'."
                )

    # 6. Проверяем тройки
    for triple in triples:
        triple_id = triple.get("id", "<без ID>")
        subject_id = triple.get("subject")
        relation_id = triple.get("relation")
        object_id = triple.get("object")

        # Проверяем существование субъекта
        if subject_id not in nodes_by_id:
            errors.append(
                f"{triple_id}: неизвестный субъект '{subject_id}'."
            )
            continue

        # Проверяем существование отношения
        if relation_id not in relations_by_id:
            errors.append(
                f"{triple_id}: неизвестное отношение '{relation_id}'."
            )
            continue

        # Проверяем существование объекта
        if object_id not in nodes_by_id:
            errors.append(
                f"{triple_id}: неизвестный объект '{object_id}'."
            )
            continue

        subject = nodes_by_id[subject_id]
        relation = relations_by_id[relation_id]
        obj = nodes_by_id[object_id]

        # Проверяем допустимый тип субъекта
        if subject.get("type") not in relation.get(
            "subject_types", []
        ):
            errors.append(
                f"{triple_id}: тип субъекта "
                f"'{subject.get('type')}' недопустим для "
                f"отношения '{relation.get('name')}'."
            )

        # Проверяем допустимый тип объекта
        if obj.get("type") not in relation.get(
            "object_types", []
        ):
            errors.append(
                f"{triple_id}: тип объекта "
                f"'{obj.get('type')}' недопустим для "
                f"отношения '{relation.get('name')}'."
            )

    return errors
