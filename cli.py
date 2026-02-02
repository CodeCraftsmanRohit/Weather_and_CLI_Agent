# =====================================================
# FINAL V2 — STABLE CLI CODING AGENT
# Windows-safe • JSON tools • Rate-limit safe
# =====================================================

# =========================
# IMPORTS
# =========================
from sambanova import SambaNova
from dotenv import load_dotenv
import subprocess
import os
import json
import time

load_dotenv()


# =========================
# API CLIENT
# =========================
client = SambaNova(
    api_key=os.getenv("SAMBANOVA_API_KEY"),
    base_url="https://api.sambanova.ai/v1",
)

MODEL = "Llama-3.3-Swallow-70B-Instruct-v0.4"


# =====================================================
# SYSTEM PROMPT (IMPORTANT)
# =====================================================
SYSTEM_PROMPT = """
You are an autonomous CLI Coding Agent.

Your goal:
Help user by creating files, writing code and executing commands.

Follow steps:
PLAN → TOOL → OUTPUT

Rules:
- ALWAYS return ONLY JSON
- One step at a time
- NEVER use shell tricks like echo/touch/cat
- Use write_file tool to create files

JSON format:
{
 "step":"PLAN" | "TOOL" | "OUTPUT",
 "content":"string",
 "tool":"string",
 "input":"string"
}

Available tools:

run_command:
  input -> command string

write_file:
  input -> JSON string:
  {"filename":"file.py","content":"code"}

read_file:
  input -> filename string
"""


# =====================================================
# TOOLS (SAFE + CROSS PLATFORM)
# =====================================================

# -------- RUN COMMAND --------
def run_command(cmd: str):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        output = result.stdout or result.stderr
        return output.strip() if output else "Done."

    except Exception as e:
        return str(e)


# -------- WRITE FILE (JSON SAFE) --------
def write_file(payload: str):
    try:
        data = json.loads(payload)

        filename = data["filename"]
        content = data["content"]

        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return f"{filename} written successfully"

    except Exception as e:
        return f"Write error: {str(e)}"


# -------- READ FILE --------
def read_file(filename: str):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        return f"Read error: {str(e)}"


tools = {
    "run_command": run_command,
    "write_file": write_file,
    "read_file": read_file
}


# =====================================================
# MEMORY
# =====================================================
message_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


# =====================================================
# SAFE LLM CALL (RATE LIMIT HANDLING)
# =====================================================
def safe_llm_call():
    while True:
        try:
            return client.chat.completions.create(
                model=MODEL,
                messages=message_history,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            if "429" in str(e):
                print("⏳ Rate limit hit… waiting 5s")
                time.sleep(5)
            else:
                raise


# =====================================================
# AGENT LOOP
# =====================================================
def run_agent(user_query):

    message_history.append({"role": "user", "content": user_query})

    while True:

        response = safe_llm_call()

        raw = response.choices[0].message.content.strip()

        message_history.append({"role": "assistant", "content": raw})

        # -------------------
        # SAFE JSON PARSE
        # -------------------
        try:
            step = json.loads(raw)
        except:
            print("⚠️ Invalid JSON, retrying...")
            continue

        step_type = step.get("step")

        # -------------------
        # PLAN
        # -------------------
        if step_type == "PLAN":
            print("🧠", step.get("content"))
            continue

        # -------------------
        # TOOL
        # -------------------
        if step_type == "TOOL":
            tool_name = step.get("tool")
            tool_input = step.get("input")

            print(f"🔧 {tool_name}")

            result = tools[tool_name](tool_input)

            print("📡 Result:\n", result[:600])

            message_history.append({
                "role": "developer",
                "content": json.dumps({
                    "step": "OBSERVE",
                    "tool": tool_name,
                    "output": result
                })
            })

            continue

        # -------------------
        # OUTPUT
        # -------------------
        if step_type == "OUTPUT":
            print("\n🤖 Agent:", step.get("content"), "\n")
            break


# =====================================================
# MAIN
# =====================================================
def main():

    print("💻 Coding Agent V2 Ready (type 'exit')\n")

    while True:
        user = input("You: ")

        if user.lower() == "exit":
            print("👋 Bye Rohit!")
            break

        run_agent(user)


# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    main()
