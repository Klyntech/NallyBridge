import requests
import json

resp = requests.post(
    "http://localhost:5000/api/chat",
    headers={"Authorization": "Bearer Clintonally", "Content-Type": "application/json"},
    json={"message": "Use bridge_execute to run system_health on device desktop", "session_id": "web:default"},
    stream=True,
    timeout=120,
)
for line in resp.iter_lines():
    if line:
        decoded = line.decode()
        if decoded.startswith("data: "):
            data = decoded[6:]
            if "done" in data:
                break
            try:
                obj = json.loads(data)
                if obj.get("type") == "response":
                    print("RESPONSE:", obj.get("text", "")[:500])
                elif obj.get("type") == "error":
                    print("ERROR:", obj.get("text", "")[:500])
                elif obj.get("type") == "thought":
                    print("THOUGHT:", obj.get("text", "")[:200])
                elif obj.get("type") == "tool_call":
                    print("TOOL CALL:", obj.get("name", ""), json.dumps(obj.get("args", {}), indent=2)[:300])
                elif obj.get("type") == "tool_result":
                    print("TOOL RESULT:", obj.get("result", "")[:300])
            except Exception:
                pass
