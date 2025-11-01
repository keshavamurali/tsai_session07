# perception.py
import requests

class Perception:
    def __init__(self, llm_url="http://localhost:11434/api/chat"):
        self.llm_url = llm_url

    def understand_query(self, query: str):
        payload = {
            "model": "llama3.1",
            "messages": [
                {"role": "system", "content": "Extract the user's intent or key topic from this input."},
                {"role": "user", "content": query}
            ]
        }
        response = requests.post(self.llm_url, json=payload)
        result = response.json()
        return result.get("message", {}).get("content", query)
