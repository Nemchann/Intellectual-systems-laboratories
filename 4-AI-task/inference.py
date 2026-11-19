
import json
from pathlib import Path


# --------------------------------------------------
# Загрузка базы знаний
# --------------------------------------------------

def load_json(filename):
    """Загружает JSON-файл из папки data или из текущей папки."""
    base_dir = Path(__file__).resolve().parent

    path = base_dir / "data" / filename
    if not path.exists():
        path = base_dir / filename

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_knowledge_base():
    """Загрузка всех данных экспертной системы."""
    plants_data = load_json("plants.json")
    compatibility_data = load_json("compatibility.json")
    graph = load_json("graph_updated.json")

    return {
        "plants": plants_data["plants"],
        "compatibility": compatibility_data["compatibility"],
        "graph": graph
    }


# --------------------------------------------------
# Проверка ответов пользователя
# --------------------------------------------------

def validate_answers(answers):
    """Проверяет наличие обязательных ответов и их значения."""

    required_fields = [
        "lighting",
        "watering",
        "humidity",
        "draft_exposure",
        "size",
        "care_capacity",
        "appearance",
        "any_pet",
        "mistake_tolerance"
    ]

    missing = [
        field for field in required_fields
        if field not in answers or answers[field] is None
    ]

    if missing:
        raise ValueError(
            f"Не заполнены обязательные вопросы: {', '.join(missing)}"
        )

    # Q7: необходимо выбрать хотя бы один вариант.
    if not isinstance(answers["appearance"], (list, tuple, set)):
        raise ValueError("Ответ на Q7 должен содержать список вариантов.")

    if not answers["appearance"]:
        raise ValueError("В Q7 необходимо выбрать хотя бы один вариант.")

    if not set(answers["appearance"]).issubset(
        {"foliage", "flowering"}
    ):
        raise ValueError("Недопустимое значение Q7.")

    # Q8: обязательный вопрос.
    if answers["any_pet"] not in {
        "no", "cats", "dogs", "cats_and_dogs"
    }:
        raise ValueError("Недопустимое значение Q8.")

    # Q9 задаётся только при наличии животных.
    if answers["any_pet"] != "no":
        if answers.get("pet_risks") not in {"true", "false"}:
            raise ValueError(
                "При наличии животных необходимо ответить на Q9."
            )


# --------------------------------------------------
# Получение коэффициентов из графа
# --------------------------------------------------

def get_connection(graph, source, target):
    """Находит связь между двумя узлами."""
    for edge in graph["connections"]:
        if (
            edge["source"] == source
            and edge["target"] == target
        ):
            return edge

    raise KeyError(
        f"В графе отсутствует связь {source} -> {target}"
    )


def get_edge_k(graph, source, target, plant_id):
    """Получает k для конкретной связи и растения."""

    edge = get_connection(graph, source, target)

    if "k_by_plant" in edge:
        if plant_id not in edge["k_by_plant"]:
            raise KeyError(
                f"Для растения {plant_id} не задан коэффициент k."
            )

        return float(edge["k_by_plant"][plant_id])

    return float(edge.get("k", 1.0))


# --------------------------------------------------
# Расчёт групп AND / OR
# --------------------------------------------------

def calculate_group(group, node_values):
    """Вычисляет значение AND- или OR-группы."""

    input_values = [
        node_values[node_id]
        for node_id in group["inputs"]
    ]

    if group["type"] == "AND":
        k_and = float(group.get("k", 1.0))

        return k_and * min(input_values)

    if group["type"] == "OR":
        input_ks = group.get(
            "input_k",
            [1.0] * len(input_values)
        )

        if len(input_ks) != len(input_values):
            raise ValueError(
                f"Количество коэффициентов input_k "
                f"не совпадает с количеством входов группы {group['id']}."
            )

        product = 1.0

        for k, q in zip(input_ks, input_values):
            product *= 1.0 - float(k) * q

        return 1.0 - product

    raise ValueError(
        f"Неизвестный тип группы: {group['type']}"
    )


# --------------------------------------------------
# Вычисление узла c04
# --------------------------------------------------

def evaluate_pet_safety(plant, answers):
    """Проверяет токсичность и физические риски растения."""

    # Q8: животных нет.
    if answers["any_pet"] == "no":
        return 1.0

    # Q9: пользователь допускает риски.
    if answers["pet_risks"] == "true":
        return 1.0

    # Определяем виды домашних животных.
    pets_mapping = {
        "cats": {"cats"},
        "dogs": {"dogs"},
        "cats_and_dogs": {"cats", "dogs"}
    }

    selected_pets = pets_mapping[answers["any_pet"]]

    toxic_to = set(plant.get("toxic_to", []))
    physical_risks = plant.get("physical_risks", [])

    # Растение токсично для одного из выбранных видов животных.
    if selected_pets.intersection(toxic_to):
        return 0.0

    # У растения имеются физические опасности.
    if physical_risks:
        return 0.0

    return 1.0


# --------------------------------------------------
# Вычисление оценки одного растения
# --------------------------------------------------

def calculate_plant(plant, answers, compatibility, graph):

    plant_id = plant["id"]

    if plant_id not in compatibility:
        raise KeyError(
            f"Для растения {plant_id} нет данных совместимости."
        )

    plant_compat = compatibility[plant_id]

    # Здесь будут храниться значения всех узлов.
    node_values = {}

    # Поле ответа -> узел и исходный узел графа.
    field_to_node = {
        "lighting": ("t01", "e01"),
        "watering": ("t02", "e02"),
        "humidity": ("t03", "e03"),
        "draft_exposure": ("t04", "e04"),
        "care_capacity": ("t05", "e05"),
        "size": ("t06", "e06"),
        "mistake_tolerance": ("t07", "e10")
    }

    # ----------------------------------------------
    # Узлы t01–t07
    # ----------------------------------------------

    for field, (node_id, source_id) in field_to_node.items():

        answer = answers[field]

        try:
            q = float(plant_compat[field][answer])
        except KeyError:
            raise ValueError(
                f"Не найдено значение совместимости: "
                f"{plant_id} -> {field} -> {answer}"
            )

        k = get_edge_k(
            graph,
            source_id,
            node_id,
            plant_id
        )

        node_values[node_id] = k * q

    # ----------------------------------------------
    # Узлы a07-1 и a07-2
    # ----------------------------------------------

    selected_appearance = set(answers["appearance"])

    # a07-1: цветущее растение.
    if "flowering" in selected_appearance:
        node_values["a07-1"] = float(
            plant_compat["appearance"]["flowering"]
        )
    else:
        node_values["a07-1"] = 0.0

    # a07-2: декоративно-лиственное растение.
    if "foliage" in selected_appearance:
        node_values["a07-2"] = float(
            plant_compat["appearance"]["foliage"]
        )
    else:
        node_values["a07-2"] = 0.0

    # ----------------------------------------------
    # Узел c04: безопасность животных
    # ----------------------------------------------

    node_values["c04"] = evaluate_pet_safety(
        plant,
        answers
    )

    # ----------------------------------------------
    # Вычисление всех AND/OR-групп
    # ----------------------------------------------

    group_values = {}

    for group in graph["groups"]:

        q_group = calculate_group(
            group,
            node_values
        )

        group_values[group["id"]] = q_group

        # Результат группы записывается
        # в соответствующий выходной узел.
        node_values[group["output"]] = q_group

    # ----------------------------------------------
    # Итоговая оценка растения
    # ----------------------------------------------

    # g05 -> c05.
    # Так как коэффициент связи c05 -> rXX равен 1,
    # итоговая оценка выходного узла не меняется.

    final_q = node_values["c05"]

    # Формируем значения выходных узлов r01–r10.
    output_values = {}

    for node in graph["nodes"]:

        if (
            node["type"] == "output"
            and node["plant_id"] == plant_id
        ):
            k = get_edge_k(
                graph,
                "c05",
                node["id"],
                plant_id
            )

            output_values[node["id"]] = k * final_q

    return {
        "plant_id": plant_id,
        "name": plant["name"],
        "nodes": node_values,
        "groups": group_values,
        "outputs": output_values,
        "q_g05": group_values["g05"],
        "q_final": final_q
    }


# --------------------------------------------------
# Запуск экспертной системы
# --------------------------------------------------

def run_expert_system(answers, plants, compatibility, graph):

    validate_answers(answers)

    results = []


    for plant in plants:

        result = calculate_plant(
            plant,
            answers,
            compatibility,
            graph
        )

        results.append(result)

    # Сортировка от наиболее подходящего растения
    # к наименее подходящему.
    results.sort(
        key=lambda item: item["q_final"],
        reverse=True
    )

    return results
