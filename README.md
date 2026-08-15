\# AI PR Assistant 🤖



An AI-powered Pull Request review assistant that automatically analyzes code changes in GitHub Pull Requests and provides structured code-review feedback.



\## 🚀 What It Does



The AI PR Assistant:



1\. Detects changed files in a GitHub Pull Request.

2\. Downloads the changed source code.

3\. Sends the code to a local AI model using Ollama.

4\. Identifies potential bugs and code-quality issues.

5\. Classifies issues by severity.

6\. Calculates an overall code-quality score.

7\. Posts the review directly back to the GitHub Pull Request.



\## 🏗️ Architecture



GitHub Pull Request

&#x20;       ↓

Python PR Assistant

&#x20;       ↓

GitHub API

&#x20;       ↓

Changed Source Code

&#x20;       ↓

Ollama / Qwen2.5-Coder

&#x20;       ↓

AI Code Analysis

&#x20;       ↓

Severity + Score

&#x20;       ↓

GitHub PR Review



\## 🛠️ Technologies



\- Python

\- Git \& GitHub

\- GitHub REST API

\- Ollama

\- Qwen2.5-Coder

\- JSON

\- PowerShell



\## 📂 Project Structure



```text

AIReviewer/

│

├── project/

│   ├── main.py

│   └── database.py

│

├── reviewer.py

├── .gitignore

└── README.md

