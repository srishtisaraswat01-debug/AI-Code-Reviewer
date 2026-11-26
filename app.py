import ast
import json
import re
from datetime import datetime

import requests
import streamlit as st

st.set_page_config(page_title="AI Code Reviewer Pro", page_icon="🔎", layout="wide")
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2"

st.title("🔎 AI Code Reviewer Pro")
st.caption("Static analysis + local AI review powered by Ollama")

with st.sidebar:
    st.header("Review settings")
    model_name = st.text_input("Ollama model", value=DEFAULT_MODEL)
    st.caption("Use a model name shown by `ollama list`.")
    show_debug = st.toggle("Show technical details", value=False)
    st.divider()
    st.markdown("**Checks included**")
    st.markdown("- Python syntax\n- Optional Pyflakes checks\n- Selected logic heuristics\n- AI review with line-specific findings\n- Syntax validation of suggested fixes")

st.info("This app reviews code but does not execute submitted code. AI suggestions can be wrong; verify them before using.")

DEFAULT_CODE = '''marks = 75

if marks >= 40:
    print("Fail")
else:
    print("Pass")
'''
code = st.text_area("Paste Python code to review", value=DEFAULT_CODE, height=260)
col1, col2 = st.columns(2)
with col1:
    run_review = st.button("🔍 Review code", type="primary", use_container_width=True)
with col2:
    clear_code = st.button("Clear code", use_container_width=True)
if clear_code:
    st.rerun()


def get_static_findings(source):
    """Run static checks only; submitted code is never executed."""
    findings = []
    try:
        ast.parse(source)
    except SyntaxError as exc:
        findings.append({
            "severity": "Error", "source": "Python parser",
            "line": exc.lineno or 1, "title": "Syntax error",
            "message": exc.msg,
            "suggestion": "Fix the syntax error before running the program."
        })
        return False, findings

    # Pyflakes is optional. If installed, it checks undefined and unused names.
    try:
        from pyflakes.api import check
        from pyflakes.reporter import Reporter
        import io
        output = io.StringIO()
        reporter = Reporter(output, output)
        check(source, "<submitted code>", reporter)
        for raw in output.getvalue().splitlines():
            match = re.search(r":(\d+):\s*(.*)", raw)
            line_no = int(match.group(1)) if match else 1
            message = match.group(2) if match else raw
            findings.append({
                "severity": "Error" if "undefined name" in message else "Warning",
                "source": "Pyflakes", "line": line_no,
                "title": "Static analysis finding", "message": message,
                "suggestion": "Check the name and surrounding code."
            })
    except ImportError:
        findings.append({
            "severity": "Info", "source": "Static analysis", "line": 1,
            "title": "Optional checker not installed",
            "message": "Pyflakes is not installed, so undefined-name and unused-name checks are limited.",
            "suggestion": "Install it with: python -m pip install pyflakes"
        })

    # A deliberately narrow heuristic for the reversed pass/fail example.
    # It does not claim to detect arbitrary logic bugs.
    pattern = r'if\s+marks?\s*>=\s*40\s*:\s*print\s*\(\s*[\'\"]fail[\'\"]\s*\)'
    if re.search(pattern, source, re.IGNORECASE):
        findings.append({
            "severity": "Warning", "source": "Logic heuristic", "line": 1,
            "title": "Possible reversed pass/fail logic",
            "message": "The code prints 'Fail' when marks are 40 or above. If 40 is the passing threshold, the result appears reversed.",
            "suggestion": "Consider printing 'Pass' in the true branch and 'Fail' in the else branch."
        })
    return True, findings


def extract_code_block(text):
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


if run_review:
    if not code.strip():
        st.warning("Please enter some Python code first.")
        st.stop()

    with st.spinner("Running local static checks..."):
        syntax_valid, static_findings = get_static_findings(code)

    errors = sum(item["severity"] == "Error" for item in static_findings)
    warnings = sum(item["severity"] == "Warning" for item in static_findings)
    infos = sum(item["severity"] == "Info" for item in static_findings)
    st.subheader("Review overview")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Errors", errors)
    m2.metric("Warnings", warnings)
    m3.metric("Info", infos)
    m4.metric("Syntax", "Valid" if syntax_valid else "Invalid")

    findings_tab, ai_tab, fix_tab, report_tab = st.tabs(
        ["🧪 Static findings", "🤖 AI review", "🛠️ Suggested fix", "📄 Report"]
    )

    with findings_tab:
        st.markdown("### Local analysis findings")
        if not static_findings:
            st.success("No findings from the enabled local checks.")
        else:
            for item in static_findings:
                title = f'{item["severity"]}: {item["title"]} — line {item["line"]}'
                if item["severity"] == "Error":
                    st.error(title)
                elif item["severity"] == "Warning":
                    st.warning(title)
                else:
                    st.info(title)
                st.write(item["message"])
                st.caption(f'Source: {item["source"]} · Suggestion: {item["suggestion"]}')
        st.caption("Heuristics cover selected patterns only; they cannot detect every possible logic bug.")

    prompt = f'''You are a careful senior Python code reviewer. Review this code without executing it.
Return these sections:
1. Summary
2. Bugs and risks (separate definite errors from possible logic concerns)
3. Line-specific findings (line number, severity: Error/Warning/Info, explanation)
4. Readability and maintainability improvements
5. Corrected code, only if useful, in one fenced ```python code block
6. Tests the developer should try

Rules:
- Do not invent bugs. Label uncertain concerns as possible issues.
- Distinguish syntax errors, runtime errors, and logical errors.
- Do not claim the code was executed or tested.
- Keep fixes close to the original behavior.
- Do not add arbitrary exception handling or change requirements without explaining why.
- If intended behavior is unclear, state your assumption.

Code:
```python
{code}
```'''

    ai_review = ""
    with ai_tab:
        st.markdown("### AI analysis")
        try:
            with st.spinner(f"Requesting review from Ollama ({model_name})..."):
                response = requests.post(
                    OLLAMA_URL,
                    json={"model": model_name, "prompt": prompt, "stream": False},
                    timeout=120
                )
            response.raise_for_status()
            ai_review = response.json().get("response", "").strip()
            if ai_review:
                st.markdown(ai_review)
            else:
                st.error("Ollama returned an empty response.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to Ollama at localhost:11434. Make sure Ollama is running.")
        except requests.exceptions.Timeout:
            st.error("Ollama took too long to respond. Try again or use a smaller model.")
        except (requests.exceptions.RequestException, ValueError) as exc:
            st.error("The request to Ollama failed.")
            if show_debug:
                st.code(str(exc))

    with fix_tab:
        st.markdown("### Suggested correction")
        suggested_code = extract_code_block(ai_review) if ai_review else None
        if not suggested_code:
            st.info("A fenced Python code block from the AI response will appear here if provided.")
        else:
            st.code(suggested_code, language="python")
            try:
                ast.parse(suggested_code)
                st.success("Syntax validation passed. This checks parsing only, not whether the logic is correct.")
            except SyntaxError as exc:
                st.error(f"Suggested code still has a syntax error: {exc.msg} (line {exc.lineno or 'unknown'}).")
            st.download_button(
                "Download suggested code", data=suggested_code,
                file_name="suggested_fix.py", mime="text/x-python"
            )

    report = {
        "project": "AI Code Reviewer Pro",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model": model_name,
        "syntax_valid": syntax_valid,
        "static_findings": static_findings,
        "submitted_code": code,
        "ai_review": ai_review
    }
    with report_tab:
        st.markdown("### Export review")
        st.download_button(
            "Download review report (JSON)",
            data=json.dumps(report, indent=2, ensure_ascii=False),
            file_name="code_review_report.json", mime="application/json"
        )

    with st.expander("Original submitted code"):
        st.code(code, language="python")
