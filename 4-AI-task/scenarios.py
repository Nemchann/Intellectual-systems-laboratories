"""
scenarios.py

Проверка экспертной системы на трёх типичных сценариях.

Запуск:
    python scenarios.py

Файлы inference.py и JSON-база знаний должны находиться
в корне проекта или в соответствии с путями, заданными в inference.py.
"""

import json

from inference import (
    load_knowledge_base,
    run_expert_system,
    validate_answers,
)
from explanations import (
    load_explanations,
    explain_result
)


SCENARIOS = {
    "Неприхотливый уход": {
        "description": (
            "Пользователь редко поливает растения, имеет невысокую "
            "готовность к уходу и предпочитает лиственные растения."
        ),
        "answers": {
            "lighting": "moderate",
            "watering": "rare",
            "humidity": "low",
            "draft_exposure": "no",
            "size": "medium",
            "care_capacity": "low",
            "appearance": ["foliage"],
            "any_pet": "no",
            "mistake_tolerance": "low",
        },
    },
    "Комфортные условия": {
        "description": (
            "Пользователь может регулярно ухаживать за растением; "
            "условия освещения, полива и влажности умеренные."
        ),
        "answers": {
            "lighting": "moderate",
            "watering": "moderate",
            "humidity": "moderate",
            "draft_exposure": "no",
            "size": "large",
            "care_capacity": "high",
            "appearance": ["foliage", "flowering"],
            "any_pet": "no",
            "mistake_tolerance": "high",
        },
    },
    "Дом с кошкой без принятия рисков": {
        "description": (
            "В доме живёт кошка. Пользователь не готов допускать "
            "растения, которые могут представлять для неё опасность."
        ),
        "answers": {
            "lighting": "bright",
            "watering": "moderate",
            "humidity": "low",
            "draft_exposure": "no",
            "size": "medium",
            "care_capacity": "moderate",
            "appearance": ["foliage"],
            "any_pet": "cats",
            "pet_risks": "false",
            "mistake_tolerance": "moderate",
        },
    },
}


def print_scenario(name, description, answers, plants, compatibility, graph, explanations):
    """Запускает сценарий и выводит результаты с объяснениями."""

    print("\n" + "=" * 72)
    print(name)
    print("-" * 72)
    print(description)

    # Проверяем ответы.
    validate_answers(answers)

    # Запускаем экспертную систему.
    results = run_expert_system(
        answers=answers,
        plants=plants,
        compatibility=compatibility,
        graph=graph
    )

    print("\nРезультаты:")

    for position, result in enumerate(results, start=1):

        # Формируем объяснение для текущего растения.
        explanation = explain_result(
            result,
            explanations
        )

        print("\n" + "-" * 72)
        print(f"{position}. {explanation['name']}")

        print(
            f"Итоговая оценка: "
            f"{explanation['final_percentage']}%"
        )

        print(
            f"Уровень совместимости: "
            f"{explanation['final_level_label']}"
        )

        # Объяснения отдельных критериев.
        print("\nКритерии:")

        for item in explanation["criteria"]:

            print(
                f"  {item['name']}: "
                f"{item['value']:.2f}"
            )

            print(
                f"    {item['description']}"
            )

        # Объяснения групп.
        print("\nОбобщённые критерии:")

        for item in explanation["groups"]:

            print(
                f"  {item['name']}: "
                f"{item['value']:.2f} — "
                f"{item['level_label']}"
            )

            print(
                f"    {item['description']}"
            )

    return results


def main():
    knowledge_base = load_knowledge_base()
    explanations = load_explanations()

    plants = knowledge_base["plants"]
    compatibility = knowledge_base["compatibility"]
    graph = knowledge_base["graph"]

    all_results = {}

    for name, scenario in SCENARIOS.items():
        results = print_scenario(
            name=name,
            description=scenario["description"],
            answers=scenario["answers"],
            plants=plants,
            compatibility=compatibility,
            graph=graph,
            explanations=explanations
        )
        all_results[name] = results

    print("\n" + "=" * 72)
    print("Проверка сценариев завершена.")
    print(
        "Сравните рейтинги: подходящие растения и их позиции "
        "должны меняться в зависимости от ответов пользователя."
    )

    for result in results:
        explanation = explain_result(
            result,
            explanations
        )

    results = print_scenario(
        name=name,
        description=scenario["description"],
        answers=scenario["answers"],
        plants=plants,
        compatibility=compatibility,
        graph=graph,
        explanations=explanations
    )


if __name__ == "__main__":
    main()
