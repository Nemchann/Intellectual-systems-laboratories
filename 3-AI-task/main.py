
from knowledge_base import load_knowledge_base
from dialogue import collect_facts
from inference import run_inference
from explanation import format_explanation


def main():
    print("=" * 50)
    print("ЭКСПЕРТНАЯ СИСТЕМА ПОДБОРА КОМНАТНЫХ РАСТЕНИЙ")
    print("=" * 50)
    print("Ответьте на вопросы, чтобы подобрать подходящее растение.\n")

    try:
        # 1. Загрузка базы знаний
        kb = load_knowledge_base()

        # 2. Сбор фактов о предпочтениях пользователя
        facts = collect_facts(kb["questions"])

        # 3. Выполнение механизма вывода
        result = run_inference(
            facts,
            kb["plants"],
            kb["rules"]
        )

        # 4. Вывод рекомендации и объяснения
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТ")
        print("=" * 50)

        if result.get("recommendation") is not None:
            plant = result["recommendation"]
            name = plant.get("name", plant.get("id", "Растение"))
            print(f"Рекомендуемое растение: {name}")

        else:
            print(result.get(
                "message",
                "Не удалось подобрать подходящее растение."
            ))

        print("\nПОЧЕМУ?")
        print(format_explanation(facts, result))
        for uncertainty in result.get("uncertainties", []):
            print(f"\nВажно: {uncertainty}")

    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"\nНе удалось запустить экспертную систему: {error}")

    print("\nРабота программы завершена.")


if __name__ == "__main__":
    main()
