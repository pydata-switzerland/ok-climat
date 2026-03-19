import subprocess


folder = "../data/"
file_docx = "subventions.docx"


subprocess.run([
    "soffice",
    "--headless",
    "--convert-to", "pdf",
    f"{folder}{file_docx}",
    "--outdir", f"{folder}"
])