import os
from fpdf import FPDF
from pathlib import Path

class KynikosDoc(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'KYNIKOS - REPORTE DE SOBERANÍA TÉCNICA', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        # Clean text for PDF (remove emojis)
        clean_text = body.encode('ascii', 'ignore').decode('ascii')
        self.multi_cell(0, 7, clean_text)
        self.ln()

def generate():
    pdf = KynikosDoc()
    pdf.add_page()
    
    # Master Architect Blueprint
    master_path = Path("workspace/KYNIKOS_MASTER_ARCH.md")
    if master_path.exists():
        content = master_path.read_text(encoding='utf-8')
        pdf.chapter_title("ARCHITECT BLUEPRINT - KYNIKOS V2.0")
        pdf.chapter_body(content)

    output_path = "workspace/KYNIKOS_MASTER_ARCH_BLUEPRINT.pdf"
    pdf.output(output_path)
    print(f"PDF generado: {output_path}")

if __name__ == "__main__":
    generate()
