import pytest

from inference import (
    calculate_group,
    evaluate_pet_safety,
    load_knowledge_base,
    run_expert_system,
    validate_answers,
)


@pytest.fixture
def knowledge_base():
    """Загружает реальные JSON-файлы проекта."""
    return load_knowledge_base()


@pytest.fixture
def base_answers():
    """Корректный набор ответов для интеграционного теста."""
    return {
        "lighting": "moderate",
        "watering": "rare",
        "humidity": "moderate",
        "draft_exposure": "no",
        "size": "medium",
        "care_capacity": "moderate",
        "appearance": ["foliage"],
        "any_pet": "no",
        # При any_pet == "no" ответ pet_risks не требуется.
        "mistake_tolerance": "low",
    }


def test_and_or_group_calculations():
    """Проверяет формулы AND и OR на простых известных значениях."""
    and_group = {
        "id": "test_and",
        "type": "AND",
        "inputs": ["a", "b", "c"],
        "output": "result",
        "k": 0.7,
    }
    or_group = {
        "id": "test_or",
        "type": "OR",
        "inputs": ["a", "b"],
        "output": "result",
        "input_k": [1.0, 1.0],
    }

    values = {"a": 0.8, "b": 0.6, "c": 0.9}

    assert calculate_group(and_group, values) == pytest.approx(0.42)
    assert calculate_group(or_group, values) == pytest.approx(0.92)


def test_q8_q9_and_pet_safety_rules(knowledge_base, base_answers):
    """Проверяет условность Q9, токсичность и физические риски."""
    plants = {
        plant["id"]: plant
        for plant in knowledge_base["plants"]
    }

    # Если животных нет, Q9 не нужен.
    validate_answers(base_answers)
    assert evaluate_pet_safety(plants["espostoa"], base_answers) == 1.0

    # При наличии кошки Q9 обязателен.
    answers_with_cat = {**base_answers, "any_pet": "cats"}
    with pytest.raises(ValueError, match="Q9"):
        validate_answers(answers_with_cat)

    # Если риски не допускаются, токсичное для кошек растение исключается.
    answers_with_cat["pet_risks"] = "false"
    validate_answers(answers_with_cat)

    assert evaluate_pet_safety(
        plants["zamioculcas"], answers_with_cat
    ) == 0.0

    # Эспостоа нетоксична, но имеет физический риск (колючки).
    assert plants["espostoa"]["toxic_to"] == []
    assert plants["espostoa"]["physical_risks"]
    assert evaluate_pet_safety(
        plants["espostoa"], answers_with_cat
    ) == 0.0

    # Если пользователь допускает риски, проверка безопасности пройдена.
    answers_with_cat["pet_risks"] = "true"
    assert evaluate_pet_safety(
        plants["espostoa"], answers_with_cat
    ) == 1.0


def test_full_expert_system_returns_sorted_results(
    knowledge_base, base_answers
):
    """Проверяет полный расчёт для всех растений и сортировку результата."""
    results = run_expert_system(
        base_answers,
        knowledge_base["plants"],
        knowledge_base["compatibility"],
        knowledge_base["graph"],
    )

    assert len(results) == len(knowledge_base["plants"])

    scores = [result["q_final"] for result in results]

    # Все оценки должны находиться в допустимом диапазоне.
    assert all(0.0 <= score <= 1.0 for score in scores)

    # Результаты должны идти от большей оценки к меньшей.
    assert scores == sorted(scores, reverse=True)

    # Каждому растению соответствует ровно один выходной узел.
    assert all(len(result["outputs"]) == 1 for result in results)

    # При отсутствии животных c04 не должен снижать оценку.
    assert all(
        result["nodes"]["c04"] == 1.0
        for result in results
    )
