
import json

from knowledge_base import load_knowledge_base
from dialogue import collect_facts
from inference import run_inference
from explanation import format_explanation


kb = load_knowledge_base()
facts = collect_facts(kb["questions"])

result = run_inference(
    facts,
    kb["plants"],
    kb["rules"]
)

if result["recommendation"] is not None:
    plant = result["recommendation"]
    print("\nРекомендация:", plant.get("name", plant.get("id")))
else:
    print("\n", result["message"])


result = run_inference(facts, kb["plants"], kb["rules"])
print(format_explanation(facts, result))