# AI Resume Analyzer

A production-quality local application for analyzing PDF resumes against job descriptions. It combines Streamlit, FastAPI, SQLite, pdfplumber, spaCy, Transformers, pandas, and matplotlib to produce ATS scores, missing skill analysis, and actionable improvement reports.

## Features

- Upload a resume as a PDF.
- Extract readable text with `pdfplumber`.
- Parse resume sections:
  - Skills
  - Education
  - Experience
  - Projects
  - Certifications
- Paste or submit a job description.
- Compare resume content against role requirements.
- Calculate an ATS score from 0 to 100.
- Display missing skills and matched skills.
- Show matching percentage and semantic fit.
- Generate an improvement report in Markdown.
- Save analysis history to SQLite.
- Use a modern Streamlit dashboard with sidebar navigation, cards, progress bars, charts, and tables.
- Expose backend endpoints with FastAPI.

## Project Structure

```text
resume-analyzer/
├── app.py
├── api.py
├── requirements.txt
├── README.md
├── .gitignore
├── LICENSE
├── database.db
├── models/
├── utils/
├── services/
├── static/
├── uploads/
└── reports/
```

## Installation

Use Python 3.11.

```bash
cd resume-analyzer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Install the recommended spaCy model:

```bash
python -m spacy download en_core_web_sm
```

The app still runs without the spaCy model by falling back to a blank English pipeline.

For transformer embeddings instead of the built-in TF-IDF fallback, install PyTorch:

```bash
pip install torch
```

## Usage

Run the Streamlit dashboard:

```bash
streamlit run app.py
```

Run the FastAPI backend:

```bash
uvicorn api:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

- `GET /health` checks service health.
- `POST /analyze/text` analyzes raw resume text and a job description.
- `POST /analyze/pdf` uploads a PDF resume and analyzes it against a job description.
- `GET /analyses` lists recent analysis summaries.
- `GET /reports/{filename}` downloads a generated Markdown report.

## Screenshots

Add screenshots after running the app locally.

```text
screenshots/dashboard.png
screenshots/results.png
screenshots/history.png
```

## Architecture

The codebase uses a modular service-oriented design:

- `PDFService` extracts text from resume PDFs.
- `NLPService` parses sections and extracts skills.
- `TransformerService` calculates semantic similarity with Hugging Face Transformers when available, with TF-IDF fallback.
- `ScoringService` computes ATS and matching scores.
- `DatabaseService` stores analysis history in SQLite.
- `ReportService` writes Markdown improvement reports.

## Scoring Model

The ATS score is a weighted score:

- 45% skill overlap
- 35% semantic similarity
- 12% resume section coverage
- 8% content depth

This makes the output explainable and easy to tune for specific industries or organizations.

## Future Improvements

- Add authentication and multi-user workspaces.
- Export reports as PDF and DOCX.
- Add configurable skill taxonomies per job family.
- Support DOCX resumes.
- Add background processing for large files.
- Add Docker and deployment manifests.
- Add automated tests and CI.

## License

MIT License. See `LICENSE`.
