"""Автоматические тесты экспертной системы подбора комнатных растений.

Запуск из корневой папки проекта:
    python -m unittest -v tests.py

Ожидаемая структура:
    data/plants.json, data/questions.json, data/rules.json
Если папки data нет, файлы ищутся рядом с tests.py.
"""

import json
import unittest
from pathlib import Path

from inference import run_inference, normalize_safety


ROOT = Path(__file__).resolve().parent


def _data_path(filename: str) -> Path:
    """Поддерживает проектную папку data/ и локальный запуск рядом с JSON."""
    in_data = ROOT / "data" / filename
    if in_data.exists():
        return in_data
    return ROOT / filename


def load_test_knowledge_base() -> dict:
    """Загружает необходимые JSON-файлы без дополнительных библиотек."""
    with _data_path("plants.json").open("r", encoding="utf-8") as file:
        plants_data = json.load(file)
    with _data_path("rules.json").open("r", encoding="utf-8") as file:
        rules_data = json.load(file)

    return {
        "plants": plants_data["plants"],
        "rules": rules_data["rules"],
    }


def standard_facts(**overrides) -> dict:
    """Типичный набор ответов пользователя; отдельные ответы можно переопределить."""
    facts = {
        "user.lighting": "умеренное",
        "user.watering_preference": "редкий",
        "user.humidity": "умеренная",
        "user.drafts": "нет",
        "user.time_for_care": "минимальное",
        "user.size": "среднее",
        "user.appearance": "декоративно-лиственное",
        "user.pets": "нет",
    }
    facts.update(overrides)
    return facts


class ExpertSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        kb = load_test_knowledge_base()
        cls.plants = kb["plants"]
        cls.rules = kb["rules"]
        cls.plant_ids = {plant["id"] for plant in cls.plants}
        cls.plants_by_id = {plant["id"]: plant for plant in cls.plants}

    def test_normal_scenario_returns_one_known_plant(self):
        """Обычный подбор должен вернуть одно растение из базы знаний."""
        result = run_inference(standard_facts(), self.plants, self.rules)

        self.assertIsNotNone(result["recommendation"])
        self.assertIn(result["recommendation"]["id"], self.plant_ids)
        self.assertIsInstance(result["message"], str)
        self.assertTrue(result["message"])

    def test_cat_scenario_does_not_recommend_confirmed_toxic_plant(self):
        """При наличии кошки растение с подтверждённой токсичностью не должно выбираться."""
        facts = standard_facts(
            **{
                "user.pets": "кошка",
                "user.pets_interest": "да",
            }
        )
        result = run_inference(facts, self.plants, self.rules)

        if result["recommendation"] is not None:
            plant = result["recommendation"]
            safety = normalize_safety(
                plant.get("pet_safety", {}).get("cats", "")
            )
            self.assertNotEqual(safety, "toxic")

    def test_unknown_environment_answers_do_not_crash(self):
        """Ответ «не знаю» обрабатывается как неизвестный факт, а не как ошибка."""
        facts = standard_facts(
            **{
                "user.lighting": "не знаю",
                "user.humidity": "не знаю",
            }
        )
        result = run_inference(facts, self.plants, self.rules)

        self.assertIn("recommendation", result)
        self.assertIn("message", result)
        self.assertTrue(
            result["recommendation"] is None
            or result["recommendation"]["id"] in self.plant_ids
        )

    def test_no_solution_returns_no_recommendation(self):
        """Несовместимые условия должны приводить к отсутствию рекомендации."""
        facts = standard_facts(
            **{
                "user.lighting": "слабое",
                "user.watering_preference": "частый",
                "user.humidity": "низкая",
                "user.pets": "кошка",
                "user.pets_interest": "да",
            }
        )
        result = run_inference(facts, self.plants, self.rules)

        self.assertIsNone(result["recommendation"])
        self.assertTrue(result["message"])

    def test_multiple_candidates_still_return_only_one_recommendation(self):
        """Даже если допущено несколько кандидатов, результат — один объект растения."""
        result = run_inference(standard_facts(), self.plants, self.rules)

        self.assertIsNotNone(result["recommendation"])
        self.assertIsInstance(result["recommendation"], dict)
        self.assertIn(result["recommendation"]["id"], self.plant_ids)
        eligible_count = sum(
            candidate.get("facts", {}).get("eligible") is True
            for candidate in result.get("candidates", [])
        )
        self.assertGreaterEqual(eligible_count, 1)

    def test_every_plant_has_unique_id(self):
        """Проверяет целостность списка растений в базе знаний."""
        ids = [plant.get("id") for plant in self.plants]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(ids))

    def test_rules_have_unique_ids(self):
        """Проверяет, что правила можно однозначно упоминать в объяснениях."""
        ids = [rule.get("id") for rule in self.rules]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(ids))


if __name__ == "__main__":
    unittest.main(verbosity=2)
