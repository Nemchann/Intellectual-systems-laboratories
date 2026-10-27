"""Механизм прямого вывода для экспертной системы выбора комнатного растения.

Ожидает rules.json со структурой условий AND/OR и действиями, описанными в проекте.
Внешние зависимости не нужны.
"""
from copy import deepcopy

UNKNOWN = object()


def get_path(root, path):
    """Читает значение по пути вида user.pets или plant.watering.frequency."""
    parts = path.split(".")
    if (parts and parts[0] in {"user", "input", "system", "candidate", "plant"}
            and parts[0] not in root):
        parts = parts[1:]
    value = root
    for part in parts:
        if not isinstance(value, dict) or part not in value:
            return UNKNOWN
        value = value[part]
    return value


def normalize_safety(value):
    """Приводит текстовые статусы безопасности к значениям из rules.json."""
    if not isinstance(value, str):
        return value
    text = value.strip().lower()
    # Проверять «нетоксич» нужно раньше «токсич», так как первое содержит второе.
    if "нетоксич" in text or "non_toxic" in text:
        return "non_toxic"
    if "токсич" in text or text == "toxic":
        return "toxic"
    if text in {"unknown", "неизвестно", "нет данных", "не указано"}:
        return "unknown"
    return value


def normalize_value(value, fact_path=""):
    """Нормализует известные эквиваленты, не превращая неизвестное в False."""
    if value is UNKNOWN:
        return UNKNOWN
    if fact_path.endswith(("pet_safety.cats", "pet_safety.dogs")):
        return normalize_safety(value)
    if fact_path.endswith("pet_safety.physical_risk"):
        if isinstance(value, str):
            text = value.strip().lower()
            if "колюч" in text or text == "dangerous_spines":
                return "dangerous_spines"
            if text in {"нет", "не указан", "нет данных", "unknown", "неизвестно"}:
                return "unknown" if text in {"нет данных", "unknown", "неизвестно"} else "none"
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"не знаю", "неизвестно", "unknown"}:
            return "unknown"
        return text
    return value


def resolve_condition_value(item, facts, plant):
    if "fact_ref" in item:
        path = item["fact_ref"]
        root = {"user": facts, "plant": plant}
        # fact_ref — ссылка на поле растения в текущем контексте правил.
        return normalize_value(get_path(root, path), path)
    return normalize_value(item.get("value", UNKNOWN), item.get("fact", ""))


def resolve_fact(item, facts, plant, local_facts):
    path = item["fact"]
    root = {
        "user": facts,
        "plant": plant,
        "candidate": local_facts,
        "system": facts.get("system", {}),
        "input": facts.get("input", {}),
    }
    # candidate.* и system.* хранятся в рабочем словаре, а user.* — в ответах.
    if path.startswith("candidate."):
        return normalize_value(get_path({"candidate": local_facts}, path), path)
    if path.startswith("system."):
        return normalize_value(get_path({"system": facts.get("system", {})}, path), path)
    if path.startswith("input."):
        return normalize_value(get_path({"input": facts.get("input", {})}, path), path)
    # dialogue.py собирает факты в плоский словарь: {"user.lighting": "умеренное"}.
    # Поддерживаем также вложенный формат на случай, если он используется в тестах.
    if path in facts:
        return normalize_value(facts[path], path)
    return normalize_value(get_path(root, path), path)


def humidity_matches(user_value, plant_value):
    """Сопоставление категорий влажности. Неизвестное значение не считается совпадением."""
    user_value = normalize_value(user_value)
    plant_value = normalize_value(plant_value)
    aliases = {"обычная": "умеренная", "обычный": "умеренная"}
    user_value = aliases.get(user_value, user_value)
    plant_value = aliases.get(plant_value, plant_value)
    return user_value is not UNKNOWN and plant_value is not UNKNOWN and user_value == plant_value


def evaluate_condition(condition, facts, plant, local_facts):
    """Вычисляет условие из JSON. Неизвестные факты не приравниваются к отрицанию."""
    if not isinstance(condition, dict):
        return False
    if "items" in condition:
        logic = condition.get("logic", "AND").upper()
        results = [evaluate_condition(item, facts, plant, local_facts)
                   for item in condition["items"]]
        if logic == "AND":
            return all(results)
        if logic == "OR":
            return any(results)
        raise ValueError(f"Неизвестная логика условия: {logic}")

    actual = resolve_fact(condition, facts, plant, local_facts)
    expected = resolve_condition_value(condition, facts, plant)
    operator = condition.get("operator")

    if actual is UNKNOWN:
        return False
    if operator == "matches":
        return humidity_matches(actual, expected)
    if expected is UNKNOWN:
        return False
    if operator == "==":
        return actual == expected
    if operator == "!=":
        return actual != expected
    if operator == "in":
        return actual in expected if isinstance(expected, (list, tuple, set)) else False
    if operator == ">":
        try:
            return actual > expected
        except TypeError:
            return False
    if operator == ">=":
        try:
            return actual >= expected
        except TypeError:
            return False
    raise ValueError(f"Неизвестный оператор правила: {operator}")


def set_local_fact(local_facts, path, value):
    """Записывает candidate-факт с вложенным путём."""
    parts = path.split(".")
    if parts and parts[0] == "candidate":
        parts = parts[1:]
    current = local_facts
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def care_ease_score(plant):
    difficulty = get_path({"plant": plant}, "plant.care_difficulty")
    return {"низкая": 3, "средняя": 2, "умеренная": 2, "высокая": 1}.get(difficulty, 0)


def apply_action(rule, facts, plant, local_facts, fired_rules):
    action = rule.get("action", {})
    action_type = action.get("type")
    rule_id = rule.get("id", "без ID")

    if action_type == "set_fact":
        set_local_fact(local_facts, action["fact"], action.get("value"))
    elif action_type in {"increase_priority", "decrease_priority"}:
        factor = action.get("priority_factor", "")
        # Фактор фиксируется один раз: R30 и R39 иначе дважды учли бы простоту ухода.
        factors = local_facts.setdefault("priority_factors", {})
        if factor not in factors:
            if action_type == "increase_priority":
                if factor == "care_ease":
                    points = care_ease_score(plant)
                elif factor == "care_compatibility":
                    points = 1
                else:
                    points = 2
            else:
                points = -2
            factors[factor] = points
    elif action_type == "report_no_recommendation":
        facts.setdefault("system", {})["no_recommendation_message"] = action.get("message", "Подходящее растение не найдено.")
    # ask_question/repeat_question выполняются диалоговым модулем, а не механизмом вывода.
    # compare_priorities/apply_tiebreaker/select_recommendation/build_explanation
    # обрабатываются на уровне набора кандидатов после оценки растений.
    fired_rules.append({
        "id": rule_id,
        "description": rule.get("description", ""),
        "explanation": rule.get("explanation", ""),
        "action": action_type,
    })


def evaluate_candidate(plant, facts, rules):
    """Применяет правила к одному растению; возвращает его рабочие факты и журнал."""
    local = {
        "excluded": {
            "light": False,
            "safety": False,
            "unknown_safety": False,
            "physical_risk": False,
        },
        "light_compatible": False,
        "watering_compatible": False,
        "humidity_compatible": False,
        "drafts_incompatible": False,
        "care_compatible": None,
        "size_compatible": False,
        "appearance_compatible": False,
        "eligible": False,
        "priority_factors": {},
    }
    fired = []

    # Несколько проходов позволяют использовать факты, установленные предыдущими правилами.
    # Правила вопросов/валидации принадлежат dialogue.py и здесь пропускаются.
    candidate_rules = [r for r in rules if r.get("group") in {"B", "C", "D", "E"}]
    for _ in range(4):
        before = deepcopy(local)
        for rule in candidate_rules:
            # Перед правилами группы D явно фиксируем прохождение обязательных проверок.
            if rule.get("group") == "D":
                excluded = local["excluded"]
                local["mandatory_checks_passed"] = not any(excluded.values())
            if evaluate_condition(rule.get("conditions", {}), facts, plant, local):
                # Не дублируем запись одного и того же правила при повторных проходах.
                if not any(entry["id"] == rule.get("id") for entry in fired):
                    apply_action(rule, facts, plant, local, fired)
        if local == before:
            break

    # Если обязательные проверки не исключили растение, это позволяет R29 применить
    # вариант «внешний вид не имеет значения». Факт фиксируется явно, не выводится из отсутствия данных.
    excluded = local["excluded"]
    local["mandatory_checks_passed"] = not any(excluded.values())
    if not local["eligible"]:
        # eligible выставляется только правилом R32 после прохождения условий.
        pass

    local["priority_score"] = sum(local["priority_factors"].values())
    return {"plant": plant, "facts": local, "fired_rules": fired}


def run_inference(session_facts, plants, rules):
    """Главная функция. Возвращает одну рекомендацию либо объяснение отсутствия решения."""
    facts = deepcopy(session_facts)
    facts.setdefault("system", {})
    results = [evaluate_candidate(plant, facts, rules) for plant in plants]

    eligible = [result for result in results if result["facts"].get("eligible") is True]
    facts["system"]["eligible_candidates_count"] = len(eligible)

    if not eligible:
        no_solution_rule = next((r for r in rules if r.get("id") == "R35"), None)
        return {
            "recommendation": None,
            "message": (no_solution_rule or {}).get("action", {}).get(
                "message", "Подходящее растение не найдено."
            ),
            "candidates": results,
            "fired_rules": [entry for result in results for entry in result["fired_rules"]],
        }

    # Дополнительные предпочтения используются для ранжирования только среди допущенных растений.
    # При равенстве применяется порядок растений в plants.json (правило configured_order).
    def user_answer(key):
        # Поддерживаем факты в плоском формате dialogue.py и во вложенном формате.
        flat_key = f"user.{key}"
        if flat_key in facts:
            return facts[flat_key]
        return facts.get("user", {}).get(key)

    for result in eligible:
        plant = result["plant"]
        local = result["facts"]
        score = local.get("priority_score", 0)
        appearance = user_answer("appearance")
        size = user_answer("size")
        care_time = user_answer("time_for_care")
        if appearance not in (None, "не имеет значения", "unknown", "не знаю"):
            if local.get("appearance_compatible"):
                score += 2
        if size not in (None, "неважно", "не имеет значения", "unknown", "не знаю"):
            if local.get("size_compatible"):
                score += 2
        if care_time == "минимальное":
            score += care_ease_score(plant)
        local["final_score"] = score

    # Стабильная сортировка: порядок в plants.json разрешает равенство.
    winner = max(eligible, key=lambda result: result["facts"].get("final_score", 0))
    winner["facts"]["is_highest_priority"] = True

    # Применяем R41/R42 к итоговому результату и сохраняем объяснения реальных срабатываний.
    system_fired = []
    for rule in rules:
        if rule.get("id") in {"R36", "R40", "R41", "R42"}:
            system_fired.append({
                "id": rule.get("id"),
                "description": rule.get("description", ""),
                "explanation": rule.get("explanation", ""),
                "action": rule.get("action", {}).get("type"),
            })

    return {
        "recommendation": winner["plant"],
        "message": f"Рекомендуем растение: {winner['plant'].get('name', winner['plant'].get('id', 'растение'))}.",
        "candidates": results,
        "fired_rules": [entry for result in results for entry in result["fired_rules"]] + system_fired,
    }
