import os
import json
import requests


PROJECT_FOLDER = "project"

all_reviews = []


# ============================================================
# AI FUNCTION
# ============================================================

def ask_ai(prompt):
    """
    Use GitHub Models inside GitHub Actions.
    Use Ollama locally when running on your own PC.
    """

    # --------------------------------------------------------
    # GITHUB ACTIONS
    # --------------------------------------------------------

    if os.getenv("GITHUB_ACTIONS") == "true":

        token = os.getenv("GITHUB_TOKEN")

        if not token:
            raise RuntimeError("GITHUB_TOKEN is not available.")

        response = requests.post(
            "https://models.github.ai/inference/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github+json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional Python code reviewer. "
                            "Return only valid JSON."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            },
            timeout=300
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    # --------------------------------------------------------
    # LOCAL OLLAMA
    # --------------------------------------------------------

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5-coder:7b",
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    return data.get("response", "").strip()


# ============================================================
# CLEAN AI RESPONSE
# ============================================================

def clean_json_response(response):
    """
    Remove accidental markdown code fences and extract JSON.
    """

    response = response.strip()

    if response.startswith("```json"):
        response = response[7:]

    elif response.startswith("```"):
        response = response[3:]

    if response.endswith("```"):
        response = response[:-3]

    response = response.strip()

    # Find JSON object if the model added extra text
    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1:
        response = response[start:end + 1]

    return response


# ============================================================
# CREATE REVIEW PROMPT
# ============================================================

def create_prompt(path, code):

    return f"""
You are a professional Python code reviewer.

Review the following Python file.

FILE:
{path}

CODE:
{code}

Find:

1. Bugs
2. Potential runtime errors
3. Security problems
4. Performance problems
5. Code quality issues

Return ONLY valid JSON.

Use exactly this structure:

{{
    "issues": [
        {{
            "severity": "CRITICAL",
            "type": "bug",
            "line": 10,
            "message": "Short explanation of the problem",
            "suggestion": "How to fix the problem"
        }}
    ]
}}

Severity MUST be one of:

CRITICAL
HIGH
MEDIUM
LOW

Type MUST be one of:

bug
security
performance
code_quality

The line number should be the approximate line where the problem occurs.

If there are no issues, return:

{{
    "issues": []
}}

IMPORTANT:

- Return JSON only.
- Do not use Markdown.
- Do not use ```json.
- Do not add explanations outside the JSON.
"""


# ============================================================
# REVIEW PYTHON FILE
# ============================================================

def review_file(path):

    print()
    print("=" * 60)
    print("Reviewing:", path)
    print("=" * 60)

    try:

        with open(path, "r", encoding="utf-8") as file:
            code = file.read()

    except Exception as error:

        print("ERROR reading file:")
        print(error)

        return

    prompt = create_prompt(path, code)

    print("Waiting for AI...")

    try:

        ai_response = ask_ai(prompt)

    except Exception as error:

        print("ERROR communicating with AI:")
        print(error)

        return

    if not ai_response:

        print("WARNING: AI returned an empty response.")
        return

    ai_response = clean_json_response(ai_response)

    try:

        review = json.loads(ai_response)

    except json.JSONDecodeError:

        print("WARNING: AI returned invalid JSON.")

        print("Raw response:")
        print(ai_response)

        return

    # Make sure the expected structure exists
    if not isinstance(review, dict):
        print("WARNING: Invalid review format.")
        return

    if "issues" not in review:
        review["issues"] = []

    all_reviews.append(
        {
            "file": path,
            "review": review
        }
    )

    print()
    print("AI REVIEW")
    print("-" * 60)

    print(json.dumps(review, indent=4))


# ============================================================
# FIND PYTHON FILES
# ============================================================

def find_python_files():

    python_files = []

    if not os.path.exists(PROJECT_FOLDER):

        print(
            f"WARNING: Project folder '{PROJECT_FOLDER}' "
            "does not exist."
        )

        return python_files

    for root, dirs, files in os.walk(PROJECT_FOLDER):

        for file in files:

            if file.endswith(".py"):

                path = os.path.join(root, file)

                python_files.append(path)

    return python_files


# ============================================================
# MAIN REVIEW
# ============================================================

def main():

    print()
    print("=" * 60)
    print("AI CODE REVIEWER")
    print("=" * 60)

    python_files = find_python_files()

    print(f"Python files found: {len(python_files)}")

    if not python_files:

        print("No Python files found.")
        return

    for path in python_files:

        review_file(path)


    # ========================================================
    # SUMMARY COUNTERS
    # ========================================================

    critical = 0
    high = 0
    medium = 0
    low = 0


    for item in all_reviews:

        issues = item["review"].get("issues", [])

        for issue in issues:

            severity = issue.get(
                "severity",
                "LOW"
            ).upper()

            if severity == "CRITICAL":
                critical += 1

            elif severity == "HIGH":
                high += 1

            elif severity == "MEDIUM":
                medium += 1

            elif severity == "LOW":
                low += 1


    # ========================================================
    # SCORE
    # ========================================================

    score = 100

    score -= critical * 30
    score -= high * 20
    score -= medium * 10
    score -= low * 3

    score = max(0, score)


    # ========================================================
    # FINAL REPORT
    # ========================================================

    print()
    print("=" * 60)
    print("PR REVIEW SUMMARY")
    print("=" * 60)

    print(f"Files reviewed: {len(all_reviews)}")
    print(f"Critical:       {critical}")
    print(f"High:            {high}")
    print(f"Medium:          {medium}")
    print(f"Low:             {low}")

    print()
    print(f"Overall score: {score}/100")


    if critical > 0 or high > 0:

        print()
        print("❌ CHANGES REQUESTED")
        print(
            "Critical or high-severity issues "
            "must be fixed."
        )

    else:

        print()
        print("✅ APPROVED")
        print(
            "No critical or high-severity issues found."
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
