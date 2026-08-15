# 🤖 AI PR Assistant

An AI-powered GitHub Pull Request review assistant that analyzes Python code and provides structured code-quality feedback.

## 🚀 What It Does

The AI PR Assistant:

1. Detects Python source files in the project.
2. Sends the code to an AI model for analysis.
3. Identifies potential bugs and code-quality issues.
4. Classifies issues by severity.
5. Calculates an overall code-quality score.
6. Produces a structured review summary.
7. Integrates with GitHub Actions for automated PR checks.

## 🏗️ Architecture

```text
GitHub Pull Request
        ↓
GitHub Actions
        ↓
Python AI Reviewer
        ↓
AI Model
        ↓
Code Analysis
        ↓
Severity Classification
        ↓
Quality Score
        ↓
PR Review Report
