# =====================================================
# WEATHER AI AGENT (SambaNova + Tools + ReAct Loop)
# Stable + JSON-safe version
# =====================================================

# =========================
# IMPORTS
# =========================
from sambanova import SambaNova
from dotenv import load_dotenv
import os
import json
import requests
import time

load_dotenv()


# =========================
# API CLIENT
# =========================
client = SambaNova(
    api_key=os.getenv("SAMBANOVA_API_KEY"),
    base_url="https://api.sambanova.ai/v1",
)

SELECTED_MODEL = "Llama-3.3-Swallow-70B-Instruct-v0.4"


# =========================
# SYSTEM PROMPT (Agent Brain)
# =========================
SYSTEM_PROMPT = """
You are an AI Weather Agent.

Follow START → PLAN → TOOL → OUTPUT steps.

Strict rules:
- Always return ONLY valid JSON
- No extra text
- One step at a time

JSON format:
{
 "step": "PLAN" | "TOOL" | "OUTPUT",
 "content": "string",
 "tool": "string",
 "input": "string"
}

Available tools:
- get_weather(city:str)
"""


# =========================
# TOOL: WEATHER API
# =========================
def get_weather(city: str):
    try:
        url = f"https://wttr.in/{city.lower()}?format=%C+%t"
        r = requests.get(url, timeout=5)

        if r.status_code == 200:
            return f"The weather in {city} is {r.text}"

        return "Weather service unavailable"

    except Exception:
        return "Weather API error"


tools = {
    "get_weather": get_weather
}


# =========================
# MEMORY
# =========================
message_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


# =========================
# AGENT LOOP
# =========================
def run_agent(user_query):

    message_history.append({"role": "user", "content": user_query})

    while True:

        response = client.chat.completions.create(
            model=SELECTED_MODEL,
            messages=message_history,
            temperature=0.3,
            response_format={"type": "json_object"}  # ⭐ FORCE JSON
        )

        raw = response.choices[0].message.content.strip()

        # Save assistant message
        message_history.append({"role": "assistant", "content": raw})

        # =====================
        # SAFE JSON PARSE
        # =====================
        try:
            step = json.loads(raw)
        except Exception:
            print("⚠️ Invalid JSON from model, retrying...")
            print("RAW:", raw)
            continue

        step_type = step.get("step")

        # =====================
        # PLAN
        # =====================
        if step_type == "PLAN":
            print("🧠", step.get("content"))
            continue

        # =====================
        # TOOL
        # =====================
        if step_type == "TOOL":
            tool_name = step.get("tool")
            tool_input = step.get("input")

            print(f"🔧 Calling {tool_name}({tool_input})")

            result = tools[tool_name](tool_input)

            print("📡 Tool result:", result)

            # send observation back to model
            message_history.append({
                "role": "developer",
                "content": json.dumps({
                    "step": "OBSERVE",
                    "tool": tool_name,
                    "output": result
                })
            })

            continue

        # =====================
        # OUTPUT
        # =====================
        if step_type == "OUTPUT":
            print("\n🌤️ Weather Agent:", step.get("content"), "\n")
            break


# =========================
# MAIN
# =========================
def main():

    print("🌦️ Weather Agent Ready (type 'exit')\n")

    while True:
        q = input("You: ")

        if q.lower() == "exit":
            print("👋 Bye!")
            break

        run_agent(q)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
