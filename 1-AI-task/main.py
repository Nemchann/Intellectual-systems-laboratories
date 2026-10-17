import json
from pathlib import Path

from src.search import neighbors
from src.validation import validate
from src.hierarchy import ancestors, descendants
from src.search import neighbors, find_path


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
