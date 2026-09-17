from agents.response_agent import generate_response


test_result = {
    "scheme_id": "S039",
    "status": "not_eligible",
    "passed_rules": [
        {
            "attribute": "state",
            "actual": "Maharashtra",
            "expected": "Maharashtra"
        }
    ],
    "failed_rules": [
        {
            "attribute": "gender",
            "actual": "male",
            "operator": "==",
            "expected": "female",
            "evidence_text": "Applicant must be female."
        }
    ],
    "missing_information": []
}


profile = {
    "name": "Akarsh",
    "age": 24,
    "gender": "male",
    "state": "Maharashtra"
}


response = generate_response(
    task="eligibility",
    user_query="Am I eligible for S039?",
    specialist_result=test_result,
    profile=profile,
    scheme_id="S039",
    citations=[]
)


print("\n========== FINAL RESPONSE ==========\n")
print(response.model_dump_json(indent=2))