# 🤖 AI PR Assistant

An AI-powered GitHub Pull Request review assistant that analyzes code changes and provides structured code-quality feedback.

## 🚀 What It Does

The AI PR Assistant:

1. Detects changed files in a GitHub Pull Request.
2. Downloads the changed source code.
3. Sends the code to a local AI model using Ollama.
4. Identifies potential bugs and code-quality issues.
5. Classifies issues by severity.
6. Calculates an overall code-quality score.
7. Posts the review back to the GitHub Pull Request.

## 🏗️ Architecture

GitHub Pull Request
↓
Python PR Assistant
↓
GitHub REST API
↓
Changed Source Code
↓
Ollama / Qwen2.5-Coder
↓
AI Code Analysis
↓
Severity Classification + Score
↓
GitHub PR Review

## 🛠️ Technologies

- Python
- Git & GitHub
- GitHub REST API
- Ollama
- Qwen2.5-Coder
- JSON
- PowerShell
- pytest
- GitHub Actions

## 📁 Project Structure

```text
AIReviewer/
│
├── project/
│   ├── main.py
│   └── database.py
│
├── reviewer.py
├── tests/
│   └── test_main.py
│
├── .github/
AI reviewer workflow test.
│   └── workflows/
│       └── tests.yml
│
├── .gitignore
└── README.md
