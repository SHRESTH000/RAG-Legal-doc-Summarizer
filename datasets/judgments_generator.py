#!/usr/bin/env python3
"""
Generator for Sample Supreme Court Judgments dataset.
Extracts 5 judgments from PDF files and creates summaries.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Try importing PDF libraries
try:
    import pdfplumber
    PDF_LIBRARY = 'pdfplumber'
except ImportError:
    try:
        import PyPDF2
        PDF_LIBRARY = 'PyPDF2'
    except ImportError:
        try:
            import pypdf
            PDF_LIBRARY = 'pypdf'
        except ImportError:
            PDF_LIBRARY = None
            print("ERROR: No PDF library found. Please install one of: pdfplumber, PyPDF2, or pypdf")


def extract_text_pdfplumber(pdf_path: str, max_pages: Optional[int] = None) -> str:
    """Extract text using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_read = len(pdf.pages) if max_pages is None else min(max_pages, len(pdf.pages))
            for i in range(pages_to_read):
                page = pdf.pages[i]
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from {pdf_path} with pdfplumber: {e}")
    return text


def extract_text_pypdf2(pdf_path: str, max_pages: Optional[int] = None) -> str:
    """Extract text using PyPDF2."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pages_to_read = len(pdf_reader.pages) if max_pages is None else min(max_pages, len(pdf_reader.pages))
            for i in range(pages_to_read):
                page = pdf_reader.pages[i]
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from {pdf_path} with PyPDF2: {e}")
    return text


def extract_text_pypdf(pdf_path: str, max_pages: Optional[int] = None) -> str:
    """Extract text using pypdf."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            pages_to_read = len(pdf_reader.pages) if max_pages is None else min(max_pages, len(pdf_reader.pages))
            for i in range(pages_to_read):
                page = pdf_reader.pages[i]
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from {pdf_path} with pypdf: {e}")
    return text


def extract_text(pdf_path: str, max_pages: Optional[int] = None) -> str:
    """Extract text from PDF using available library."""
    if PDF_LIBRARY == 'pdfplumber':
        return extract_text_pdfplumber(pdf_path, max_pages)
    elif PDF_LIBRARY == 'PyPDF2':
        return extract_text_pypdf2(pdf_path, max_pages)
    elif PDF_LIBRARY == 'pypdf':
        return extract_text_pypdf(pdf_path, max_pages)
    else:
        raise ImportError("No PDF library available")


def extract_case_info(text: str) -> Dict[str, Any]:
    """Extract case information from judgment text."""
    case_info = {
        "case_number": "",
        "parties": "",
        "date": "",
        "court": "Supreme Court of India",
        "judges": [],
        "relevant_sections": []
    }
    
    # Extract case number (patterns like Crl.A. No. 1234/2020, W.P.(C) No. 123/2020, etc.)
    case_patterns = [
        r'(Crl\.?A\.?\s*No\.?\s*\d+/\d+)',
        r'(W\.?P\.?\s*\(?C\)?\s*No\.?\s*\d+/\d+)',
        r'(Civil Appeal No\.?\s*\d+/\d+)',
        r'(Criminal Appeal No\.?\s*\d+/\d+)',
        r'(Special Leave Petition \(Criminal\) No\.?\s*\d+/\d+)',
        r'(Special Leave Petition \(Civil\) No\.?\s*\d+/\d+)',
        r'(SLP\s*\(?Crl?\)?\s*No\.?\s*\d+/\d+)',
    ]
    
    for pattern in case_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            case_info["case_number"] = match.group(1)
            break
    
    # Extract parties (common pattern: "Petitioner" vs "Respondent" or "Appellant" vs "Respondent")
    party_patterns = [
        r'([A-Z][^.]{10,100}?)\s+v[eo]rs?\.?\s+([A-Z][^.]{10,100}?)',
        r'([A-Z][^.]{10,100}?)\s+vs\.?\s+([A-Z][^.]{10,100}?)',
    ]
    
    for pattern in party_patterns:
        match = re.search(pattern, text[:2000], re.IGNORECASE)
        if match:
            case_info["parties"] = f"{match.group(1).strip()} vs {match.group(2).strip()}"
            break
    
    # Extract date (patterns like "Dated: 15.01.2020", "Decided on 15-01-2020", etc.)
    date_patterns = [
        r'Dated[:\s]+(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
        r'Decided on[:\s]+(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
        r'(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text[:1000])
        if match:
            case_info["date"] = match.group(1)
            break
    
    # Extract judges (patterns like "HON'BLE MR. JUSTICE X", "JUSTICE X", etc.)
    judge_patterns = [
        r"HON'?BLE\s+MR\.?\s+JUSTICE\s+([A-Z][A-Z\s.]+)",
        r"JUSTICE\s+([A-Z][A-Z\s.]+)",
    ]
    
    judges = set()
    for pattern in judge_patterns:
        matches = re.findall(pattern, text[:3000])
        for match in matches:
            judge_name = match.strip()
            if len(judge_name) > 3 and len(judge_name) < 50:
                judges.add(judge_name)
    
    case_info["judges"] = list(judges)[:5]  # Limit to 5 judges
    
    # Extract relevant sections (IPC, CrPC, Evidence Act sections)
    section_patterns = [
        r'Section\s+(\d+)\s+of\s+the\s+Indian\s+Penal\s+Code',
        r'Section\s+(\d+)\s+of\s+IPC',
        r'IPC\s+Section\s+(\d+)',
        r'Section\s+(\d+)\s+of\s+Cr\.?P\.?C\.?',
        r'Cr\.?P\.?C\.?\s+Section\s+(\d+)',
        r'Section\s+(\d+)\s+of\s+the\s+Evidence\s+Act',
    ]
    
    sections = set()
    for pattern in section_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        sections.update(matches)
    
    case_info["relevant_sections"] = sorted(list(sections), key=lambda x: int(x))[:20]  # Limit to 20 sections
    
    return case_info


def generate_summary(text: str, max_length: int = 500) -> str:
    """Generate a basic summary of the judgment."""
    # Extract first few sentences from the text
    sentences = re.split(r'[.!?]+', text[:3000])
    sentences = [s.strip() for s in sentences if len(s.strip()) > 50]
    
    summary = ""
    for sentence in sentences[:10]:  # Take first 10 meaningful sentences
        if len(summary) + len(sentence) < max_length:
            summary += sentence + ". "
        else:
            break
    
    if not summary:
        summary = text[:max_length] + "..."
    
    return summary.strip()


def extract_key_points(text: str, num_points: int = 5) -> List[str]:
    """Extract key points from the judgment."""
    key_points = []
    
    # Look for common judgment structure markers
    markers = [
        "HELD:",
        "HELD THAT:",
        "IT WAS HELD:",
        "THE COURT HELD:",
        "KEY POINTS:",
        "FINDINGS:",
    ]
    
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            snippet = text[idx:idx+1000]
            sentences = re.split(r'[.!?]+', snippet)
            for sentence in sentences[:num_points]:
                s = sentence.strip()
                if len(s) > 30 and len(s) < 300:
                    key_points.append(s)
                    if len(key_points) >= num_points:
                        break
            break
    
    # If no markers found, extract from conclusion
    if not key_points:
        conclusion_idx = text.lower().find("conclusion")
        if conclusion_idx != -1:
            snippet = text[conclusion_idx:conclusion_idx+1000]
            sentences = re.split(r'[.!?]+', snippet)
            for sentence in sentences[:num_points]:
                s = sentence.strip()
                if len(s) > 30 and len(s) < 300:
                    key_points.append(s)
                    if len(key_points) >= num_points:
                        break
    
    return key_points[:num_points]


def generate_judgments_dataset(output_dir: str = "datasets", 
                                judgments_dir: str = "judgments_2024",
                                num_judgments: int = 5):
    """Generate sample judgments dataset from PDF files."""
    
    if PDF_LIBRARY is None:
        print("ERROR: No PDF library available. Please install pdfplumber, PyPDF2, or pypdf")
        return
    
    judgments_path = Path(judgments_dir)
    if not judgments_path.exists():
        print(f"ERROR: Judgments directory not found: {judgments_dir}")
        print("Trying alternative directories...")
        # Try other years
        for year in [2023, 2022, 2021, 2020, 2019]:
            alt_path = Path(f"judgments_{year}")
            if alt_path.exists():
                judgments_path = alt_path
                judgments_dir = str(alt_path)
                print(f"Using directory: {judgments_dir}")
                break
        else:
            print("No judgments directory found. Creating sample dataset structure.")
            # Create empty dataset
            dataset = {
                "dataset_name": "Sample Supreme Court Judgments",
                "total_judgments": 0,
                "judgments": []
            }
            output_path = os.path.join(output_dir, "judgments", "sample_judgments.json")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            return
    
    pdf_files = list(judgments_path.glob("*.pdf"))[:num_judgments]
    
    if not pdf_files:
        print(f"No PDF files found in {judgments_dir}")
        return
    
    judgments = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"Processing judgment {i}/{len(pdf_files)}: {pdf_file.name}")
        
        try:
            # Extract full text
            full_text = extract_text(str(pdf_file))
            
            if not full_text or len(full_text.strip()) < 100:
                print(f"  Warning: Could not extract sufficient text from {pdf_file.name}")
                continue
            
            # Extract case information
            case_info = extract_case_info(full_text)
            
            # Generate summary
            summary = generate_summary(full_text)
            
            # Extract key points
            key_points = extract_key_points(full_text)
            
            judgment_obj = {
                "case_number": case_info["case_number"] or f"Case_{i}",
                "parties": case_info["parties"] or "Not identified",
                "date": case_info["date"] or "Not identified",
                "court": case_info["court"],
                "judges": case_info["judges"],
                "full_text": full_text[:50000],  # Limit text length for JSON
                "summary": summary,
                "key_points": key_points,
                "relevant_sections": case_info["relevant_sections"],
                "metadata": {
                    "source_file": pdf_file.name,
                    "source_directory": judgments_dir,
                    "text_length": len(full_text),
                    "extraction_method": PDF_LIBRARY
                }
            }
            
            judgments.append(judgment_obj)
            print(f"  [OK] Extracted: {judgment_obj['case_number']}")
            
        except Exception as e:
            print(f"  [ERROR] Error processing {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    dataset = {
        "dataset_name": "Sample Supreme Court Judgments",
        "total_judgments": len(judgments),
        "judgments": judgments
    }
    
    # Save to file
    output_path = os.path.join(output_dir, "judgments", "sample_judgments.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\nJudgments dataset generated: {len(judgments)} judgments")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    generate_judgments_dataset()
