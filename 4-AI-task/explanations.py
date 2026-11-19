
import json
from pathlib import Path


def load_explanations(filename="explanations.json"):
    """Загрузка текстов объяснений."""

    project_dir = Path(__file__).resolve().parent
    file_path = project_dir / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_level(value, levels):
    """Определение уровня соответствия по значению q."""

    if value >= levels["high"]["min"]:
        return "high"

    if value >= levels["medium"]["min"]:
        return "medium"

    return "low"


def explain_nodes(result, explanations):
    """Формирование объяснений отдельных узлов."""

    node_explanations = []

    for node_id, node_info in explanations["nodes"].items():

        # Берём только те узлы, для которых есть описание
        # и которые присутствуют в результате расчёта.
        if node_id not in result["nodes"]:
            continue

        value = result["nodes"][node_id]

        # Особая обработка узла безопасности животных.
        if node_id == "c04":

            if value >= 1.0:
                description = node_info["safe"]
            else:
                description = node_info["unsafe"]

            node_explanations.append({
                "id": node_id,
                "name": node_info["name"],
                "value": value,
                "description": description
            })

            continue

        level = get_level(
            value,
            explanations["levels"]
        )

        node_explanations.append({
            "id": node_id,
            "name": node_info["name"],
            "value": value,
            "level": level,
            "level_label": explanations["levels"][level]["label"],
            "description": node_info["description"]
        })

    return node_explanations


def explain_groups(result, explanations):
    """Формирование объяснений AND/OR-групп."""

    group_explanations = []

    for group_id, value in result["groups"].items():

        if group_id not in explanations["groups"]:
            continue

        group_info = explanations["groups"][group_id]

        level = get_level(
            value,
            explanations["levels"]
        )

        group_explanations.append({
            "id": group_id,
            "name": group_info["name"],
            "value": value,
            "level": level,
            "level_label": explanations["levels"][level]["label"],
            "description": group_info["description"]
        })

    return group_explanations


def explain_result(result, explanations):
    """Формирование полного объяснения результата."""

    node_explanations = explain_nodes(
        result,
        explanations
    )

    group_explanations = explain_groups(
        result,
        explanations
    )

    final_q = result["q_final"]

    final_level = get_level(
        final_q,
        explanations["levels"]
    )

    return {
        "plant_id": result["plant_id"],
        "name": result["name"],

        "criteria": node_explanations,

        "groups": group_explanations,

        "final_score": final_q,

        "final_percentage": round(final_q * 100, 2),

        "final_level": final_level,

        "final_level_label":
            explanations["levels"][final_level]["label"]
    }
