import re

def condition_is_true(condition, facts):
    """Проверяет условие показа вопроса."""

    if not condition:
        return True

    # Вариант 1: условие задано словарём в JSON
    if isinstance(condition, dict):
        fact_name = condition["fact"]
        operator = condition["operator"]
        expected_value = condition["value"]

    # Вариант 2: условие задано строкой
    elif isinstance(condition, str):
        match = re.fullmatch(
            r"""([\w.]+)\s*(==|!=)\s*["']([^"']+)["']""",
            condition.strip()
        )

        if not match:
            raise ValueError(
                f"Неподдерживаемое условие ask_if: {condition}"
            )

        fact_name, operator, expected_value = match.groups()

    else:
        raise ValueError(
            f"Неверный формат ask_if: {condition}"
        )

    actual_value = facts.get(fact_name)

    if operator == "==":
        return actual_value == expected_value
    elif operator == "!=":
        return actual_value != expected_value

    raise ValueError(f"Неподдерживаемый оператор: {operator}")



def ask_question(question_data, facts):
    """Задаёт вопрос и возвращает ответ пользователя."""
    fact_name = question_data["fact"]
    question_text = question_data["question"]
    options = question_data["options"]
    required = question_data.get("required", True)

    print(f"\n{question_text}")
    print("Варианты ответа:")
    for option in options:
        print(f"  - {option}")

    while True:
        answer = input("Ваш ответ: ").strip().lower()

        # Необязательный вопрос можно пропустить
        if not answer and not required:
            return None

        # Проверяем ответ по допустимым вариантам
        allowed_options = [option.lower() for option in options]

        if answer in allowed_options:
            return answer

        print("Пожалуйста, выберите один из предложенных вариантов.")
        if not required:
            print("Или нажмите Enter, чтобы пропустить вопрос.")


def collect_facts(questions):
    """Проводит опрос и собирает факты пользователя."""
    facts = {}

    for question_data in questions:
        condition = question_data.get("ask_if")

        # Пропускаем вопрос, если его условие не выполнено
        if condition and not condition_is_true(condition, facts):
            continue

        answer = ask_question(question_data, facts)

        if answer is not None:
            facts[question_data["fact"]] = answer

    return facts


if __name__ == "__main__":
    # Небольшая самостоятельная проверка модуля
    from knowledge_base import load_knowledge_base

    try:
        knowledge_base = load_knowledge_base()
        facts = collect_facts(knowledge_base["questions"])

        print("\nСобранные факты:")
        for fact_name, value in facts.items():
            print(f"{fact_name}: {value}")

    except (FileNotFoundError, ValueError, KeyError) as error:
        print(f"Ошибка: {error}")
