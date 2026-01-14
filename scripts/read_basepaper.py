"""Script to read and analyze base paper"""
import sys
from pathlib import Path

try:
    import pdfplumber
    PDF_LIB = 'pdfplumber'
except ImportError:
    try:
        import PyPDF2
        PDF_LIB = 'PyPDF2'
    except ImportError:
        try:
            import pypdf
            PDF_LIB = 'pypdf'
        except ImportError:
            PDF_LIB = None

def read_pdf(file_path):
    if PDF_LIB == 'pdfplumber':
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages[:10]:  # First 10 pages
                text += page.extract_text() or ""
            return text
    elif PDF_LIB == 'PyPDF2':
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf.pages[:10]:
                text += page.extract_text() or ""
            return text
    elif PDF_LIB == 'pypdf':
        with open(file_path, 'rb') as f:
            pdf = pypdf.PdfReader(f)
            text = ""
            for page in pdf.pages[:10]:
                text += page.extract_text() or ""
            return text
    else:
        return "No PDF library available"

if __name__ == "__main__":
    basepaper_path = Path(__file__).parent.parent / "basepaper.pdf"
    output_path = Path(__file__).parent.parent / "basepaper_analysis.txt"
    if basepaper_path.exists():
        print(f"Reading base paper ({PDF_LIB})...")
        text = read_pdf(str(basepaper_path))
        
        # Save to file to avoid encoding issues
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("BASE PAPER CONTENT (First 10000 characters)\n")
            f.write("="*80 + "\n\n")
            f.write(text[:10000])
            f.write("\n\n" + "="*80 + "\n")
            f.write(f"Total text length: {len(text)} characters\n")
            f.write("="*80 + "\n")
        
        print(f"\nBase paper content saved to: {output_path}")
        print(f"Total text length: {len(text)} characters")
        print(f"Preview: {text[:500]}")
    else:
        print(f"Base paper not found at {basepaper_path}")
