from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from models.schemas import AnalysisResult
from services.database_service import DatabaseService
from services.pdf_service import PDFExtractionError, PDFService
from services.report_service import ReportService
from services.scoring_service import ScoringService
from utils.config import STATIC_DIR, ensure_directories


st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_directories()
pdf_service = PDFService()
scoring_service = ScoringService()
database_service = DatabaseService()
report_service = ReportService()


def load_styles() -> None:
    css_path = STATIC_DIR / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_metric_card(label: str, value: str, help_text: str | None = None) -> None:
    tooltip = f"<small>{help_text}</small>" if help_text else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>{label}</h3>
            <p>{value}</p>
            {tooltip}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_skill_chips(title: str, skills: list[str]) -> None:
    st.subheader(title)
    if not skills:
        st.info("No skills found in this category.")
        return
    chips = " ".join(f'<span class="skill-chip">{skill}</span>' for skill in skills)
    st.markdown(chips, unsafe_allow_html=True)


def render_score_chart(result: AnalysisResult) -> None:
    chart_data = pd.DataFrame(
        {
            "Metric": ["ATS Score", "Match", "Semantic Fit"],
            "Score": [result.ats_score, result.matching_percentage, result.semantic_similarity],
        }
    )
    fig, ax = plt.subplots(figsize=(7, 3.2))
    colors = ["#2563eb", "#16a34a", "#f59e0b"]
    ax.barh(chart_data["Metric"], chart_data["Score"], color=colors)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Score")
    ax.grid(axis="x", alpha=0.25)
    ax.spines[["top", "right", "left"]].set_visible(False)
    st.pyplot(fig, clear_figure=True)


def render_section_table(result: AnalysisResult) -> None:
    sections = result.resume_sections.model_dump()
    rows = [{"Section": key.title(), "Items Found": len(value)} for key, value in sections.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def analyze_resume(uploaded_file, job_description: str, job_title: str) -> AnalysisResult | None:  # type: ignore[no-untyped-def]
    if not uploaded_file:
        st.warning("Upload a PDF resume to begin.")
        return None
    if not job_description.strip():
        st.warning("Paste the target job description before running analysis.")
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        tmp_path = Path(tmp_file.name)

    try:
        with st.spinner("Extracting resume text and comparing it with the job description..."):
            resume_text = pdf_service.extract_text(tmp_path)
            result = scoring_service.analyze(resume_text, job_description)
            database_service.save_analysis(result, job_title)
            report_service.save_markdown_report(result, job_title)
            st.session_state["last_result"] = result
            st.session_state["resume_text"] = resume_text
            return result
    except PDFExtractionError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error("Something went wrong during analysis. Check the logs for details.")
        st.exception(exc)
    finally:
        tmp_path.unlink(missing_ok=True)
    return None


def dashboard() -> None:
    st.title("AI Resume Analyzer")
    st.caption("Analyze resume fit, ATS readiness, missing skills, and targeted improvements.")

    left, right = st.columns([0.42, 0.58], gap="large")
    with left:
        st.subheader("Inputs")
        uploaded_file = st.file_uploader("Upload resume PDF", type=["pdf"])
        job_title = st.text_input("Job title", value="Data Scientist")
        job_description = st.text_area("Job description", height=280, placeholder="Paste the target role description here...")
        run_analysis = st.button("Analyze Resume", type="primary", use_container_width=True)

    with right:
        result = st.session_state.get("last_result")
        if run_analysis:
            result = analyze_resume(uploaded_file, job_description, job_title)

        if result:
            metrics = st.columns(3)
            with metrics[0]:
                render_metric_card("ATS Score", f"{result.ats_score}/100")
                st.progress(result.ats_score / 100)
            with metrics[1]:
                render_metric_card("Matching", f"{result.matching_percentage:.1f}%")
                st.progress(result.matching_percentage / 100)
            with metrics[2]:
                render_metric_card("Semantic Fit", f"{result.semantic_similarity:.1f}%")
                st.progress(result.semantic_similarity / 100)

            st.divider()
            chart_col, table_col = st.columns([0.58, 0.42])
            with chart_col:
                st.subheader("Score Breakdown")
                render_score_chart(result)
            with table_col:
                st.subheader("Resume Coverage")
                render_section_table(result)
        else:
            st.info("Upload a resume and job description to see the analysis dashboard.")


def results_page() -> None:
    result: AnalysisResult | None = st.session_state.get("last_result")
    st.title("Analysis Results")
    if not result:
        st.info("Run an analysis from the dashboard first.")
        return

    tabs = st.tabs(["Skills", "Extracted Sections", "Recommendations", "Report"])
    with tabs[0]:
        matched_col, missing_col = st.columns(2)
        with matched_col:
            render_skill_chips("Matched Skills", result.matched_skills)
        with missing_col:
            render_skill_chips("Missing Skills", result.missing_skills)
    with tabs[1]:
        sections = result.resume_sections.model_dump()
        for name, values in sections.items():
            with st.expander(name.title(), expanded=name in {"skills", "experience"}):
                if values:
                    for value in values:
                        st.write(f"- {value}")
                else:
                    st.write("No content detected.")
    with tabs[2]:
        for recommendation in result.recommendations:
            st.success(recommendation)
    with tabs[3]:
        st.markdown(result.report)
        st.download_button(
            "Download Markdown Report",
            result.report,
            file_name="resume_improvement_report.md",
            mime="text/markdown",
            use_container_width=True,
        )


def history_page() -> None:
    st.title("Analysis History")
    rows = database_service.list_analyses(limit=50)
    if not rows:
        st.info("No analyses saved yet.")
        return
    data = pd.DataFrame([row.model_dump() for row in rows])
    data["created_at"] = pd.to_datetime(data["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    data["missing_skills"] = data["missing_skills"].apply(lambda values: ", ".join(values[:5]))
    st.dataframe(data, use_container_width=True, hide_index=True)


def about_page() -> None:
    st.title("About")
    st.write(
        "This application extracts resume text from PDF files, identifies resume sections, "
        "compares the profile with a job description, and generates a practical ATS improvement report."
    )
    st.write("Run the FastAPI backend with `uvicorn api:app --reload` for API access.")


def main() -> None:
    load_styles()
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to", ["Dashboard", "Results", "History", "About"], label_visibility="collapsed")
        st.divider()
        st.caption("Production-ready local analyzer with modular services and SQLite persistence.")

    if page == "Dashboard":
        dashboard()
    elif page == "Results":
        results_page()
    elif page == "History":
        history_page()
    else:
        about_page()


if __name__ == "__main__":
    main()
