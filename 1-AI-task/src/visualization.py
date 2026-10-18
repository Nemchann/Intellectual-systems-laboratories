
import matplotlib.pyplot as plt
import networkx as nx


def render_graph(network, output_file="semantic_network.png"):
    """
    Строит и сохраняет изображение семантической сети.
    """
    nodes = network.get("nodes", [])
    relations = network.get("relations", [])
    triples = network.get("triples", [])

    graph = nx.DiGraph()

    # Сопоставляем ID узлов и названия отношений
    relations_by_id = {
        relation["id"]: relation["name"]
        for relation in relations
    }

    # Добавляем узлы
    for node in nodes:
        graph.add_node(
            node["id"],
            label=node["name"],
            node_type=node["type"],
        )

    # Добавляем направленные связи
    for triple in triples:
        subject_id = triple.get("subject")
        object_id = triple.get("object")
        relation_id = triple.get("relation")

        if (
            subject_id in graph
            and object_id in graph
            and relation_id in relations_by_id
        ):
            graph.add_edge(
                subject_id,
                object_id,
                label=relations_by_id[relation_id],
            )

    # Располагаем узлы на рисунке
    positions = nx.spring_layout(graph, seed=42, k=1.5)

    labels = nx.get_node_attributes(graph, "label")
    edge_labels = nx.get_edge_attributes(graph, "label")

    plt.figure(figsize=(18, 12))

    nx.draw_networkx(
        graph,
        positions,
        labels=labels,
        node_size=2200,
        node_color="lightblue",
        font_size=8,
        arrows=True,
        arrowsize=15,
    )

    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=edge_labels,
        font_size=7,
    )

    plt.title("Семантическая сеть комнатных растений")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.show()

    return graph
