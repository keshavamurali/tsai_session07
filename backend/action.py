# action.py
class Action:
    def execute(self, decision):
        if decision.get("decision") == "use_memory":
            return {"action": "show_memory"}
        else:
            return {"action": "search_web"}
