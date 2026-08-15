import os
import json
import requests

project_folder = "project"

all_reviews = []

for root, dirs, files in os.walk(project_folder):

    for file in files:

        if file.endswith(".py"):

            path = os.path.join(root, file)

            with open(path, "r", encoding="utf-8") as f:
                code = f.read()

            prompt = f"""
You are a professional Python code reviewer.

Review this Python file:

FILE: {path}

CODE:
{code}

Find:
1. Bugs
2. Potential runtime errors
3. Security problems
4. Performance problems
5. Code quality issues

Return ONLY valid JSON.

Use exactly this format:

{{
    "issues": [
        {{
            "severity": "CRITICAL",
            "type": "bug",
            "line": 1,
            "message": "Short explanation of the problem",
            "suggestion": "How to fix it"
        }}
    ]
}}

Severity must be one of:
CRITICAL, HIGH, MEDIUM, LOW

Type must be one of:
bug, security, performance, code_quality

If there are no issues, return:

{{
    "issues": []
}}

Do not include markdown.
Do not include ```json.
Return JSON only.
"""

            print("\nReviewing:", path)
            print("Waiting for Ollama...")

            try:

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

                result = response.json()

                ai_response = result.get("response", "").strip()

                if not ai_response:

                    print("WARNING: Ollama returned an empty response.")
                    print("Skipping:", path)
                    continue

                # Remove accidental markdown fences
                if ai_response.startswith("```json"):
                    ai_response = ai_response[7:]

                if ai_response.startswith("```"):
                    ai_response = ai_response[3:]

                if ai_response.endswith("```"):
                    ai_response = ai_response[:-3]

                ai_response = ai_response.strip()

                try:

                    review = json.loads(ai_response)

                except json.JSONDecodeError:

                    print("WARNING: Ollama did not return valid JSON.")
                    print("Raw response:")
                    print(ai_response)

                    print("Skipping:", path)
                    continue

                all_reviews.append({
                    "file": path,
                    "review": review
                })

                print("\n" + "=" * 60)
                print("AI REVIEW:", path)
                print("=" * 60)
                print(json.dumps(review, indent=4))

            except requests.exceptions.RequestException as e:

                print("ERROR communicating with Ollama:")
                print(e)

                continue


# ============================================================
# PR REVIEW SUMMARY
# ============================================================

critical = 0
high = 0
medium = 0
low = 0

for item in all_reviews:

    for issue in item["review"].get("issues", []):

        severity = issue.get("severity", "LOW")

        if severity == "CRITICAL":
            critical += 1

        elif severity == "HIGH":
            high += 1

        elif severity == "MEDIUM":
            medium += 1

        elif severity == "LOW":
            low += 1


# ============================================================
# SCORE
# ============================================================

score = 100

score -= critical * 30
score -= high * 20
score -= medium * 10
score -= low * 3

score = max(0, score)


# ============================================================
# FINAL PR REPORT
# ============================================================

print("\n" + "=" * 60)
print("PR REVIEW SUMMARY")
print("=" * 60)

print(f"Files reviewed: {len(all_reviews)}")
print(f"Critical: {critical}")
print(f"High:     {high}")
print(f"Medium:   {medium}")
print(f"Low:      {low}")

print(f"\nOverall score: {score}/100")

if critical > 0 or high > 0:

    print("\n❌ CHANGES REQUESTED")
    print("Critical or high-severity issues must be fixed.")

else:

    print("\n✅ APPROVED")
    print("No critical or high-severity issues found.")
