import streamlit as st
import requests
import ast

st.title("AI Code Reviewer")
st.write("Review your Python code using Llama 3.2.")

code = st.text_area("Enter your Python code:", height=300)

if st.button("Review Code"):

    if code.strip() == "":
        st.warning("Please enter some code.")

    else:
        # Check Python syntax
        try:
            ast.parse(code)
            syntax_error = None
        except SyntaxError as e:
            syntax_error = e

        # Send code to Llama
        prompt = f"""
Review this Python code.

Tell me:
1. Errors
2. Explanation
3. Improvements
4. Corrected Code

Code:
{code}
"""

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            }
        )

        result = response.json()

        if syntax_error:
            st.error(
                f"Syntax Error: {syntax_error.msg} "
                f"at line {syntax_error.lineno}"
            )

        st.subheader("AI Code Review")
        st.write(result["response"])