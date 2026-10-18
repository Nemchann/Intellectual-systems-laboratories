import json
from pathlib import Path

from src.validation import validate
from src.hierarchy import ancestors, descendants
from src.search import neighbors, find_path

from src.visualization import render_graph

# Путь к папке с данными
DATA_DIR = Path(__file__).parent / "data"


def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        return json.load(file)


# Загружаем все данные один раз
nodes = load_json("nodes.json")["nodes"]
relations = load_json("relations.json")["relations"]
triples = load_json("triples.json")["triples"]

# Собираем данные в общую структуру для валидации
network = {
    "nodes": nodes,
    "relations": relations,
    "triples": triples,
}

render_graph(network)

def show_path(source_id, target_id):
    path = find_path(source_id, target_id, triples, nodes)

    if path is None:
        print("Путь не найден.")
        return

    if not path:
        print("Начальный и конечный узлы совпадают.")
        return

    nodes_by_id = {node["id"]: node for node in nodes}
    relations_by_id = {
        relation["id"]: relation
        for relation in relations
    }

    for triple in path:
        subject = nodes_by_id[triple["subject"]]
        relation = relations_by_id[triple["relation"]]
        obj = nodes_by_id[triple["object"]]

        print(
            f'{subject["name"]} '
            f'—[{relation["name"]}]→ '
            f'{obj["name"]}'
        )


# 1. Проверяем корректность сети
errors = validate(network)

if errors:
    print("Найдены ошибки:")
    for error in errors:
        print("-", error)
else:
    print("Ошибок не обнаружено.")

# 2. Ищем соседей
result = neighbors(
    node_id="PLT-001",
    relation_id="REL-004",
    triples=triples,
    nodes=nodes,
)

for node in result:
    print(f'{node["id"]}: {node["name"]}')


print("\nПредки класса «Кактус»:")
for node in ancestors("CLS-003", triples, nodes):
    print(f'{node["id"]}: {node["name"]}')

print("\nПотомки класса «Комнатное растение»:")
for node in descendants("CLS-001", triples, nodes):
    print(f'{node["id"]}: {node["name"]}')


print("\nПуть от Спатифиллума до Комнатного растения:")

path = find_path(
    source_id="PLT-003",
    target_id="CLS-001",
    triples=triples,
    nodes=nodes,
)

if path is None:
    print("Путь не найден.")
elif not path:
    print("Начальный и конечный узлы совпадают.")
else:
    for triple in path:
        subject = next(
            node for node in nodes
            if node["id"] == triple["subject"]
        )
        relation = next(
            rel for rel in relations
            if rel["id"] == triple["relation"]
        )
        obj = next(
            node for node in nodes
            if node["id"] == triple["object"]
        )

        print(
            f'{subject["name"]} '
            f'—[{relation["name"]}]→ '
            f'{obj["name"]}'
        )


print("\nТест 1. Спатифиллум → Комнатное растение")
show_path("PLT-003", "CLS-001")

print("\nТест 2. Экземпляр замиокулькаса → Неприхотливость")
show_path("INS-001", "CHR-005")

print("\nТест 3. Слабое освещение → Комнатное растение")
show_path("VAL-001", "CLS-001")
