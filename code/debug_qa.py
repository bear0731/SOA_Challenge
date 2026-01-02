from main import ExplanationSystem
import json

app = ExplanationSystem()

print("--- DEBUGGING External Knowledge ---")
case = {
    "issue_age": 70,
    "smoker_status": "Non-Smoker"
}
result = app.run(case)
user_prompt = result['final_user_prompt']
print(user_prompt)

print("\n--- DEBUGGING High Risk ---")
case_high = {
    "issue_age": 75,
    "smoker_status": "Smoker",
    "preferred_class": "Standard",
    "duration": 10
}
result_high = app.run(case_high)
print(result_high['final_user_prompt'])
