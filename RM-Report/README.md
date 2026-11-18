# RM-Report — reports and thesis for the TRMP project

Everything that presents the work (as opposed to the code and experiment logs, which are in `../Differential_RL_TRMP/`).

| Path | What it is |
|---|---|
| `TRMP_BTech_Thesis.pdf` | Final B.Tech thesis (IIIT Allahabad template), 71 pages — all experiments, results, decisions |
| `thesis/` | LaTeX project of the thesis (`main.tex`, `frontmatter.tex`, `Chapters/`, `Appendices/`, `refs.bib`, `Figures/`, `Thesis.cls`); build with `latexmk -xelatex main.tex` (see `thesis/README.md`) |
| `project_report/` | The 9-page project report (`TRMP_RL_Project_Report.pdf`, built from the `.html`) and the full-length write-up `FINAL_REPORT.md` / `.docx` |
| `figures/` | Figures used by the reports (`fig1`–`fig8`) |
| `data/` | Numeric outputs behind the tables (full-protocol comparison, paired comparison, diagnostics) |
| `scripts/` | Generators: `make_report_figures.py` (fig 6–8), `make_thesis_tables.py` (thesis Appendix B), `html_to_pdf.js` (HTML → PDF) |

Regenerating (run from `../Differential_RL_TRMP/`, which holds the experiment outputs under `out/`):

    .venv/bin/python ../RM-Report/scripts/make_report_figures.py     # fig6-8 -> RM-Report/figures
    .venv/bin/python ../RM-Report/scripts/make_thesis_tables.py      # thesis/Appendices/AppendixB.tex
    node ../RM-Report/scripts/html_to_pdf.js ../RM-Report/project_report/TRMP_RL_Project_Report.html ../RM-Report/project_report/TRMP_RL_Project_Report.pdf

The thesis still contains the placeholders `[Student Name]`, `[Roll No.]`, `[Supervisor Name]` (see `thesis/README.md`).
