import json
from pathlib import Path


# Путь к папке проекта, где лежит этот Python-файл
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"


def load_json(filename):
    """Загружает JSON-файл из папки data."""
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Не найден файл базы знаний: {file_path}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Ошибка в JSON-файле {filename}: {error}"
        ) from error


def load_knowledge_base():
    """Загружает все данные экспертной системы."""
    plants_data = load_json("plants.json")
    questions_data = load_json("questions.json")
    rules_data = load_json("rules.json")

    # Проверяем наличие основных разделов
    if "plants" not in plants_data:
        raise ValueError(
            "В plants.json отсутствует раздел 'plants'"
        )

    if "questions" not in questions_data:
        raise ValueError(
            "В questions.json отсутствует раздел 'questions'"
        )

    if "rules" not in rules_data:
        raise ValueError(
            "В rules.json отсутствует раздел 'rules'"
        )

    return {
        "plants": plants_data["plants"],
        "questions": questions_data["questions"],
        "rules": rules_data["rules"],
    }


if __name__ == "__main__":
    try:
        knowledge_base = load_knowledge_base()

        print("База знаний успешно загружена.")
        print(
            f"Количество растений: "
            f"{len(knowledge_base['plants'])}"
        )
        print(
            f"Количество вопросов: "
            f"{len(knowledge_base['questions'])}"
        )
        print(
            f"Количество правил: "
            f"{len(knowledge_base['rules'])}"
        )

    except (FileNotFoundError, ValueError) as error:
        print(f"Ошибка загрузки базы знаний: {error}")
