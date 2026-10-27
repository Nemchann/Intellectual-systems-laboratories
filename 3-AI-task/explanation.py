"""Формирование объяснения рекомендации экспертной системы.

Модуль использует результат run_inference() из inference.py и факты диалога.
Не выполняет подбор растений повторно.
"""

from typing import Any


def _get_user_value(session_facts: dict, key: str) -> Any:
    """Поддерживает плоские факты {'user.lighting': ...} и вложенные {'user': {...}}."""
    flat_key = f"user.{key}"
    if flat_key in session_facts:
        return session_facts[flat_key]
    return session_facts.get("user", {}).get(key)


def _plant_name(plant: dict | None) -> str:
    if not plant:
        return "растение"
    return plant.get("name") or plant.get("id") or "растение"


def _fired_for_plant(candidate_result: dict) -> list[dict]:
    """Возвращает журнал правил конкретного кандидата."""
    entries = candidate_result.get("fired_rules", [])
    seen = set()
    unique = []
    for entry in entries:
        rule_id = entry.get("id")
        if rule_id and rule_id not in seen:
            seen.add(rule_id)
            unique.append(entry)
    return unique


def build_explanation(session_facts: dict, inference_result: dict) -> dict:
    """Строит текстовое объяснение выбранного растения или отсутствия рекомендации.

    Возвращает:
      {
        "title": str,
        "text": str,
        "fired_rule_ids": list[str],
        "reasons": list[str]
      }
    """
    recommendation = inference_result.get("recommendation")
    candidates = inference_result.get("candidates", [])

    if recommendation is None:
        message = inference_result.get(
            "message", "Подходящее растение не найдено по указанным условиям."
        )
        return {
            "title": "Рекомендация не сформирована",
            "text": message,
            "fired_rule_ids": [],
            "reasons": [],
        }

    # Находим результат оценки именно рекомендованного растения.
    candidate_result = next(
        (
            item for item in candidates
            if item.get("plant", {}).get("id") == recommendation.get("id")
        ),
        None,
    )
    local_facts = (candidate_result or {}).get("facts", {})
    fired_rules = _fired_for_plant(candidate_result or {})
    fired_ids = [entry["id"] for entry in fired_rules if entry.get("id")]

    reasons = []
    lighting = _get_user_value(session_facts, "lighting")
    watering = _get_user_value(session_facts, "watering_preference")
    humidity = _get_user_value(session_facts, "humidity")
    drafts = _get_user_value(session_facts, "drafts")
    care_time = _get_user_value(session_facts, "time_for_care")
    size = _get_user_value(session_facts, "size")
    appearance = _get_user_value(session_facts, "appearance")
    pets = _get_user_value(session_facts, "pets")

    plant_lighting = recommendation.get("lighting", {})
    plant_watering = recommendation.get("watering", {})
    plant_humidity = recommendation.get("humidity", {})
    plant_size = recommendation.get("size", {})
    plant_type = recommendation.get("plant_type")

    if local_facts.get("light_compatible"):
        if lighting == plant_lighting.get("preferred"):
            reasons.append(f"освещение совпадает с предпочтительным ({lighting})")
        elif plant_lighting.get("tolerates_low") is True and lighting == "слабое":
            reasons.append("растение переносит слабое освещение")

    if local_facts.get("watering_compatible"):
        reasons.append(
            f"режим полива подходит под ваш выбор ({watering})"
        )

    if local_facts.get("humidity_compatible"):
        reasons.append(
            f"требование к влажности соответствует ответу ({humidity})"
        )

    if drafts == "сильные" and recommendation.get("draft_sensitivity") != "высокая":
        reasons.append("не выявлено критического конфликта с сильными сквозняками")

    if care_time == "минимальное" and recommendation.get("care_difficulty") == "низкая":
        reasons.append("растение несложно в уходе, что подходит при минимальном времени")

    if size not in (None, "неважно", "не имеет значения", "не знаю"):
        if plant_size.get("category") == size:
            reasons.append(f"подходит желаемый размер ({size})")

    if appearance not in (None, "неважно", "не имеет значения", "не знаю"):
        if plant_type == appearance:
            reasons.append(f"совпадает предпочтение по внешнему виду ({appearance})")

    if pets and pets != "нет":
        reasons.append(
            "при наличии домашних животных выбор проверяется по данным о токсичности "
            "и физическом риске растения"
        )

    if not reasons:
        reasons.append(
            "растение прошло обязательные проверки и получило наивысший итоговый приоритет "
            "среди допущенных кандидатов"
        )

    score = local_facts.get("final_score", local_facts.get("priority_score"))
    text = f"Рекомендуется {_plant_name(recommendation)}. " + "; ".join(reasons) + "."
    if score is not None:
        text += f" Итоговый приоритет: {score}."

    return {
        "title": f"Почему выбрано растение «{_plant_name(recommendation)}»",
        "text": text,
        "fired_rule_ids": fired_ids,
        "reasons": reasons,
    }


def format_explanation(session_facts: dict, inference_result: dict) -> str:
    """Удобная обёртка, возвращающая только текст для консольного интерфейса."""
    explanation = build_explanation(session_facts, inference_result)
    lines = [explanation["title"], explanation["text"]]
    if explanation["fired_rule_ids"]:
        lines.append("Сработавшие правила: " + ", ".join(explanation["fired_rule_ids"]))
    return "\n".join(lines)
