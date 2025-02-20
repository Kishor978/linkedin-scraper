import requests

# API Endpoint
url = "http://localhost:8000/get-candidate"

# Example Payload
payload = {
    "parent_company": "Google",
    "position": "Data Scientist",
    "city": "San Francisco",
    "state": "CA",
    "country": "USA",
    "skills": ["Python", "Machine Learning"],
    "flag": "TARGET"
}

# Sending POST request
response = requests.post(url, json=payload)

# Handling the Response
if response.status_code == 200:
    candidates = response.json()
    if candidates:
        for idx, candidate in enumerate(candidates, 1):
            print(f"{idx}. {candidate}")
    else:
        print("No candidates found or the function returned None.")

    print("Found Candidates:")
    for idx, candidate in enumerate(candidates, 1):
        print(f"\nCandidate #{idx}:")
        print(f"Name: {candidate.get('name')}")
        print(f"LinkedIn: {candidate.get('linkedin_url')}")
        print(f"Position: {candidate.get('position')}")
        print(f"Location: {candidate.get('location')}")
        print(f"Skills: {', '.join(candidate.get('skills', []))}")
else:
    print(f"Failed to fetch candidates. Status Code: {response.status_code}")
    print(f"Error: {response.json()}")
