import os
import json
import requests


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_FOLDER = "project"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

GITHUB_MODELS_URL = (
    "https://models.github.ai/inference/chat/completions"
)

MODEL = "openai/gpt-4.1"

all_reviews = []


# ============================================================
# AI REVIEW
# ============================================================

def ask_ai(prompt):
    """
    Call GitHub Models when running inside GitHub Actions.
    Call Ollama when running locally.
    """

    if os.getenv("GITHUB_ACTIONS") == "true":

        if not GITHUB_TOKEN:
            raise RuntimeError(
                "GITHUB_TOKEN is not available."
            )

        response = requests.post(
            GITHUB_MODELS_URL,
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional Python "
                            "code reviewer. Return only valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "temperature": 0.1,
            },
            timeout=300,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data["choices"][0]["message"]["content"]
            .strip()
        )

    # --------------------------------------------------------
    # LOCAL OLLAMA
    # --------------------------------------------------------

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5-coder:7b",
            "prompt": prompt,
            "stream": False,
        },
        timeout=300,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("response", "").strip()


# ============================================================
# CLEAN AI RESPONSE
# ============================================================

def clean_ai_response(response):
    response = response.strip()

    if response.startswith("```json"):
        response = response[7:]

    elif response.startswith("```"):
        response = response[3:]

    if response.endswith("```"):
        response = response[:-3]

    response = response.strip()

    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1:
        response = response[start:end + 1]

    return response


# ============================================================
# REVIEW PROMPT
# ============================================================

def create_prompt(path, code):

    return f"""
You are a professional Python code reviewer.

Review this Python file carefully.

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

Pay special attention to:

- Incorrect calculations
- Logic errors
- Incorrect percentages
- Edge cases
- Invalid assumptions
- Exception handling
- Unsafe operations

Return ONLY valid JSON.

Use exactly this format:

{{
    "issues": [
        {{
            "severity": "HIGH",
            "type": "bug",
            "line": 10,
            "message": "Short explanation",
            "suggestion": "How to fix it"
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

If there are no issues, return:

{{
    "issues": []
}}

Do not use Markdown.
Do not use ```json.
Return JSON only.
"""


# ============================================================
# REVIEW FILE
# ============================================================

def review_file(path):

    print()
    print("=" * 60)
    print("Reviewing:", path)
    print("=" * 60)

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

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

        print("WARNING: AI returned empty response.")
        return

    ai_response = clean_ai_response(
        ai_response
    )

    try:

        review = json.loads(ai_response)

    except json.JSONDecodeError:

        print("WARNING: AI returned invalid JSON.")
        print(ai_response)

        return

    if not isinstance(review, dict):

        print("WARNING: Invalid review format.")
        return

    if "issues" not in review:

        review["issues"] = []

    all_reviews.append(
        {
            "file": path,
            "review": review,
        }
    )

    print()
    print("AI REVIEW")
    print("-" * 60)

    print(
        json.dumps(
            review,
            indent=4
        )
    )


# ============================================================
# FIND PYTHON FILES
# ============================================================

def find_python_files():

    python_files = []

    if not os.path.exists(
        PROJECT_FOLDER
    ):

        print(
            f"Project folder '{PROJECT_FOLDER}' "
            "does not exist."
        )

        return python_files

    for root, dirs, files in os.walk(
        PROJECT_FOLDER
    ):

        for file in files:

            if file.endswith(".py"):

                python_files.append(
                    os.path.join(
                        root,
                        file
                    )
                )

    return python_files


# ============================================================
# BUILD REVIEW COMMENT
# ============================================================

def build_comment(
    critical,
    high,
    medium,
    low,
    score
):

    comment = "## 🤖 AI PR Assistant Review\n\n"

    comment += "### Summary\n\n"

    comment += "| Severity | Count |\n"
    comment += "|---|---:|\n"
    comment += f"| 🔴 Critical | {critical} |\n"
    comment += f"| 🟠 High | {high} |\n"
    comment += f"| 🟡 Medium | {medium} |\n"
    comment += f"| 🟢 Low | {low} |\n\n"

    comment += f"**Overall Score: {score}/100**\n\n"

    if critical > 0 or high > 0:

        comment += (
            "### ❌ Changes Requested\n\n"
            "Critical or high-severity issues "
            "were detected.\n\n"
        )

    else:

        comment += (
            "### ✅ Approved\n\n"
            "No critical or high-severity "
            "issues were detected.\n\n"
        )

    comment += "---\n\n"
    comment += "### Detailed Review\n\n"

    for item in all_reviews:

        filename = item["file"]

        comment += f"#### `{filename}`\n\n"

        issues = item["review"].get(
            "issues",
            []
        )

        if not issues:

            comment += "✅ No issues found.\n\n"
            continue

        for issue in issues:

            severity = issue.get(
                "severity",
                "LOW"
            )

            issue_type = issue.get(
                "type",
                "bug"
            )

            line = issue.get(
                "line",
                "N/A"
            )

            message = issue.get(
                "message",
                "No message provided."
            )

            suggestion = issue.get(
                "suggestion",
                "No suggestion provided."
            )

            comment += (
                f"**{severity} — {issue_type}**\n\n"
            )

            comment += (
                f"**Line:** {line}\n\n"
            )

            comment += (
                f"**Issue:** {message}\n\n"
            )

            comment += (
                f"**Suggestion:** {suggestion}\n\n"
            )

    comment += (
        "---\n\n"
        "*Generated automatically by "
        "AI PR Assistant.*"
    )

    return comment


# ============================================================
# POST COMMENT TO PR
# ============================================================

def post_pr_comment(comment):

    if os.getenv("GITHUB_ACTIONS") != "true":
        print(
            "\nRunning locally — "
            "PR comment will not be posted."
        )
        return

    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN is not available."
        )

    if not GITHUB_REPOSITORY:
        raise RuntimeError(
            "GITHUB_REPOSITORY is not available."
        )

    if not PR_NUMBER:
        raise RuntimeError(
            "PR_NUMBER is not available."
        )

    url = (
        "https://api.github.com/repos/"
        f"{GITHUB_REPOSITORY}/issues/"
        f"{PR_NUMBER}/comments"
    )

    response = requests.post(
        url,
        headers={
            "Authorization": (
                f"Bearer {GITHUB_TOKEN}"
            ),
            "Accept": (
                "application/vnd.github+json"
            ),
            "X-GitHub-Api-Version": (
                "2026-03-10"
            ),
        },
        json={
            "body": comment
        },
        timeout=60,
    )

    response.raise_for_status()

    print()
    print(
        "✅ AI review posted to GitHub PR."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("AI PR ASSISTANT")
    print("=" * 60)

    python_files = find_python_files()

    print(
        f"Python files found: "
        f"{len(python_files)}"
    )

    if not python_files:

        print(
            "ERROR: No Python files found."
        )

        raise SystemExit(1)

    for path in python_files:

        review_file(path)

    # --------------------------------------------------------
    # IMPORTANT: DO NOT FALSELY APPROVE
    # --------------------------------------------------------

    if not all_reviews:

        print()
        print("❌ AI REVIEW FAILED")
        print(
            "No files were successfully reviewed."
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # COUNT ISSUES
    # --------------------------------------------------------

    critical = 0
    high = 0
    medium = 0
    low = 0

    for item in all_reviews:

        issues = item["review"].get(
            "issues",
            []
        )

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

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = 100

    score -= critical * 30
    score -= high * 20
    score -= medium * 10
    score -= low * 3

    score = max(
        0,
        score
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PR REVIEW SUMMARY")
    print("=" * 60)

    print(
        f"Files reviewed: {len(all_reviews)}"
    )

    print(
        f"Critical: {critical}"
    )

    print(
        f"High:     {high}"
    )

    print(
        f"Medium:   {medium}"
    )

    print(
        f"Low:      {low}"
    )

    print()
    print(
        f"Overall score: {score}/100"
    )

    if critical > 0 or high > 0:

        print(
            "\n❌ CHANGES REQUESTED"
        )

    else:

        print(
            "\n✅ APPROVED"
        )

    # --------------------------------------------------------
    # POST TO PR
    # --------------------------------------------------------

    comment = build_comment(
        critical,
        high,
        medium,
        low,
        score
    )

    post_pr_comment(comment)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
