# 🤖 AI Code Reviewer

An AI-powered code review application built using Python, Streamlit, Ollama, and Llama 3.2.

## Features

- Paste code and get an AI review
- Detect Python syntax errors
- Get explanations of errors
- Get code improvement suggestions
- Generate corrected code
- Supports Python programming
- Simple Streamlit interface

## Technologies Used

- Python
- Streamlit
- Ollama
- Llama 3.2
- Requests
- AST

## How to Run

1. Install the required packages:

   pip install -r requirements.txt

2. Make sure Ollama is running.

3. Make sure Llama 3.2 is installed:

   ollama list

4. Run the application:

   python -m streamlit run app.py

5. Open the local Streamlit URL in your browser.

## Project Flow

User enters code → Python syntax check → Llama 3.2 → AI code review → Results displayed in Streamlit