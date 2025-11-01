# decision.py
import requests
import json

class Decision:
    def __init__(self, llm_url="http://localhost:11434/api/chat"):
        self.llm_url = llm_url

    def decide_action(self, query, memory_results):
        memory_summary = "\n".join(memory_results) if memory_results else "No memory found."
        prompt = f"""
        The user asked: "{query}"
        You have these memory results:
        {memory_summary}

        Respond in JSON:
        {{
            "decision": "use_memory" | "search_web",
            "reason": "why you chose it"
        }}
        """

        payload = {"model": "llama3.1", "messages": [{"role": "user", "content": prompt}]}
        response = requests.post(self.llm_url, json=payload)
        text = response.json().get("message", {}).get("content", "")
        try:
            return json.loads(text)
        except Exception:
            return {"decision": "search_web", "reason": "Parsing failed"}
