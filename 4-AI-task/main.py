from inference import run_expert_system, load_knowledge_base

answers = {
    "lighting": "moderate",
    "watering": "rare",
    "humidity": "moderate",
    "draft_exposure": "no",
    "size": "medium",
    "care_capacity": "moderate",
    "appearance": ["foliage"],
    "any_pet": "cats",
    "pet_risks": "false",
    "mistake_tolerance": "low"
}

knowledge_base = load_knowledge_base()

results = run_expert_system(
    answers,
    knowledge_base["plants"],
    knowledge_base["compatibility"],
    knowledge_base["graph"]
)

for result in results:
    print(
        result["name"],
        round(result["q_final"], 3)
    )