#!/usr/bin/env python3
"""
Script to filter criminal cases from Supreme Court judgements.
High accuracy detection using multiple indicators.
"""

import os
import shutil
import re
from pathlib import Path
from typing import List, Tuple

# Try importing PDF libraries in order of preference
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
            print("Install with: pip install pdfplumber (recommended) or pip install PyPDF2")


def extract_text_pdfplumber(pdf_path: str, max_pages: int = 5) -> str:
    """Extract text using pdfplumber (best quality)."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Read first few pages for classification (usually enough)
            pages_to_read = min(max_pages, len(pdf.pages))
            for i in range(pages_to_read):
                page = pdf.pages[i]
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from {pdf_path} with pdfplumber: {e}")
    return text


def extract_text_pypdf2(pdf_path: str, max_pages: int = 5) -> str:
    """Extract text using PyPDF2."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pages_to_read = min(max_pages, len(pdf_reader.pages))
            for i in range(pages_to_read):
                page = pdf_reader.pages[i]
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from {pdf_path} with PyPDF2: {e}")
    return text


def extract_text_pypdf(pdf_path: str, max_pages: int = 5) -> str:
    """Extract text using pypdf (newer version of PyPDF2)."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            pages_to_read = min(max_pages, len(pdf_reader.pages))
            for i in range(pages_to_read):
                page = pdf_reader.pages[i]
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from {pdf_path} with pypdf: {e}")
    return text


def extract_text(pdf_path: str, max_pages: int = 5) -> str:
    """Extract text from PDF using available library."""
    if PDF_LIBRARY == 'pdfplumber':
        return extract_text_pdfplumber(pdf_path, max_pages)
    elif PDF_LIBRARY == 'PyPDF2':
        return extract_text_pypdf2(pdf_path, max_pages)
    elif PDF_LIBRARY == 'pypdf':
        return extract_text_pypdf(pdf_path, max_pages)
    else:
        return ""


def is_criminal_case(text: str) -> Tuple[bool, float, List[str]]:
    """
    Determine if a case is criminal with confidence score.
    Returns: (is_criminal, confidence_score, matched_indicators)
    """
    if not text:
        return False, 0.0, []
    
    text_lower = text.lower()
    matched_indicators = []
    score = 0.0
    
    # High-confidence indicators (strong signals)
    high_confidence_patterns = [
        (r'\bcriminal\s+appeal\b', 10, 'Criminal Appeal'),
        (r'\bcriminal\s+writ\b', 10, 'Criminal Writ'),
        (r'\bcrl\.?\s*a\.?\s*\d+', 10, 'Criminal Appeal Number'),
        (r'\bcrl\.?\s*w\.?\s*p\.?\s*\d+', 10, 'Criminal Writ Petition'),
        (r'\bcrl\.?\s*p\.?\s*\d+', 10, 'Criminal Petition'),
        (r'\bindian\s+penal\s+code\b', 8, 'Indian Penal Code'),
        (r'\bipc\b', 7, 'IPC'),
        (r'\bsection\s+\d+\s+of\s+the\s+indian\s+penal\s+code\b', 9, 'IPC Section'),
        (r'\bsection\s+\d+\s+ipc\b', 9, 'IPC Section'),
    ]
    
    for pattern, weight, name in high_confidence_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            matched_indicators.append(name)
            score += weight
    
    # IPC Section numbers (common criminal sections)
    ipc_sections = [
        r'\bsection\s+(302|304|307|376|354|363|366|363a|363b|363c|363d|365|366a|366b|377|498a|420|406|409|395|396|397|398|399|400|401|402|403|404|405|411|412|413|414|415|416|417|418|419|441|442|443|444|445|446|447|448|449|450|451|452|453|454|455|456|457|458|459|460|461|462|463|464|465|466|467|468|469|470|471|472|473|474|475|476|477|478|479|480|481|482|483|484|485|486|487|488|489|490|491|492|493|494|495|496|497|498|499|500|503|504|505|506|507|508|509|510|511|120a|120b|121|122|123|124|124a|125|126|127|128|129|130|131|132|133|134|135|136|137|138|139|140|141|142|143|144|145|146|147|148|149|150|151|152|153|154|155|156|157|158|159|160|161|162|163|164|165|166|167|168|169|170|171|172|173|174|175|176|177|178|179|180|181|182|183|184|185|186|187|188|189|190|191|192|193|194|195|196|197|198|199|200|201|202|203|204|205|206|207|208|209|210|211|212|213|214|215|216|217|218|219|220|221|222|223|224|225|226|227|228|229|230|231|232|233|234|235|236|237|238|239|240|241|242|243|244|245|246|247|248|249|250|251|252|253|254|255|256|257|258|259|260|261|262|263|264|265|266|267|268|269|270|271|272|273|274|275|276|277|278|279|280|281|282|283|284|285|286|287|288|289|290|291|292|293|294|295|296|297|298|299|300|301)\b',
        8, 'Common IPC Sections'
    ]
    
    if re.search(ipc_sections[0], text_lower, re.IGNORECASE):
        matched_indicators.append(ipc_sections[2])
        score += ipc_sections[1]
    
    # Medium-confidence indicators
    medium_patterns = [
        (r'\bcriminal\s+case\b', 5, 'Criminal Case'),
        (r'\bcriminal\s+proceedings\b', 5, 'Criminal Proceedings'),
        (r'\bcr\.?\s*no\.?\s*\d+', 6, 'Criminal Case Number'),
        (r'\bstate\s+vs\.?\s+', 5, 'State vs (criminal)'),
        (r'\bstate\s+of\s+.*\s+vs\.?\s+', 5, 'State of X vs'),
        (r'\bprosecution\b', 4, 'Prosecution'),
        (r'\baccused\b', 4, 'Accused'),
        (r'\boffence\b', 4, 'Offence'),
        (r'\boffender\b', 4, 'Offender'),
        (r'\bpunishment\b', 3, 'Punishment'),
        (r'\bconviction\b', 4, 'Conviction'),
        (r'\bacquittal\b', 4, 'Acquittal'),
        (r'\bbail\b', 3, 'Bail'),
        (r'\bpenal\b', 5, 'Penal'),
        (r'\bcriminal\s+law\b', 5, 'Criminal Law'),
        (r'\bcriminal\s+justice\b', 4, 'Criminal Justice'),
    ]
    
    for pattern, weight, name in medium_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            if name not in matched_indicators:
                matched_indicators.append(name)
                score += weight
    
    # Additional patterns for Supreme Court specific formats
    sc_patterns = [
        (r'\bcrl\.?\s*a\.?\s*no\.?\s*\d+', 9, 'Crl.A. Number'),
        (r'\bcrl\.?\s*w\.?\s*p\.?\s*no\.?\s*\d+', 9, 'Crl.W.P. Number'),
        (r'\bcrl\.?\s*mp\.?\s*no\.?\s*\d+', 8, 'Crl.M.P. Number'),
        (r'\bcriminal\s+special\s+leave\s+petition', 8, 'Criminal SLP'),
        (r'\bcrl\.?\s*slp\b', 8, 'Crl. SLP'),
    ]
    
    for pattern, weight, name in sc_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            if name not in matched_indicators:
                matched_indicators.append(name)
                score += weight
    
    # Threshold: if score >= 10, likely criminal; >= 15, very likely
    is_criminal = score >= 10
    
    # Normalize confidence score (0-1 scale)
    confidence = min(score / 30.0, 1.0)
    
    return is_criminal, confidence, matched_indicators


def filter_criminal_cases(input_folder: str, output_folder: str, max_pages: int = 5, 
                         min_confidence: float = 0.3, verbose: bool = True):
    """
    Filter criminal cases from PDF judgements.
    
    Args:
        input_folder: Path to folder containing PDF judgements
        output_folder: Path to folder where criminal cases will be copied
        max_pages: Maximum number of pages to read from each PDF (default: 5)
        min_confidence: Minimum confidence score to classify as criminal (0-1)
        verbose: Print progress information
    """
    if PDF_LIBRARY is None:
        print("Please install a PDF library first:")
        print("  pip install pdfplumber  (recommended)")
        print("  or: pip install PyPDF2")
        print("  or: pip install pypdf")
        return
    
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    if not input_path.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return
    
    # Create output folder if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files
    pdf_files = list(input_path.glob("*.pdf"))
    total_files = len(pdf_files)
    
    if total_files == 0:
        print(f"No PDF files found in '{input_folder}'")
        return
    
    print(f"Found {total_files} PDF files in '{input_folder}'")
    print(f"Using PDF library: {PDF_LIBRARY}")
    print(f"Output folder: {output_folder}")
    print(f"Minimum confidence: {min_confidence}")
    print("-" * 60)
    
    criminal_count = 0
    processed = 0
    errors = []
    
    for pdf_file in pdf_files:
        processed += 1
        if verbose and processed % 50 == 0:
            print(f"Processed: {processed}/{total_files}, Criminal cases found: {criminal_count}")
        
        try:
            # Extract text from first few pages
            text = extract_text(str(pdf_file), max_pages=max_pages)
            
            # Check if criminal case
            is_criminal, confidence, indicators = is_criminal_case(text)
            
            # Apply minimum confidence threshold
            if is_criminal and confidence >= min_confidence:
                # Copy file to output folder
                dest_path = output_path / pdf_file.name
                shutil.copy2(pdf_file, dest_path)
                criminal_count += 1
                
                if verbose and processed <= 10:  # Show details for first 10
                    print(f"[{processed}] {pdf_file.name}: CRIMINAL (confidence: {confidence:.2f}, indicators: {', '.join(indicators[:3])})")
        except Exception as e:
            error_msg = f"Error processing {pdf_file.name}: {str(e)}"
            errors.append(error_msg)
            if verbose:
                print(f"ERROR: {error_msg}")
    
    print("-" * 60)
    print(f"\nProcessing complete!")
    print(f"Total files processed: {processed}")
    print(f"Criminal cases found: {criminal_count} ({criminal_count/total_files*100:.1f}%)")
    print(f"Files copied to: {output_folder}")
    
    if errors:
        print(f"\nErrors encountered: {len(errors)}")
        if len(errors) <= 10:
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"  (Showing first 10 errors)")
            for error in errors[:10]:
                print(f"  - {error}")


if __name__ == "__main__":
    import sys
    
    # Configuration
    MAX_PAGES = 5  # Read first 5 pages for classification (usually sufficient)
    MIN_CONFIDENCE = 0.3  # Minimum confidence score (0.3 = 30%)
    
    # Process single year or multiple years
    if len(sys.argv) > 1:
        # Process specific year(s) from command line
        years = [int(y) for y in sys.argv[1:]]
    else:
        # Process years 2020-2025 by default
        years = list(range(2020, 2026))
    
    print("=" * 70)
    print("CRIMINAL CASES FILTERING - MULTI-YEAR PROCESSING")
    print("=" * 70)
    print(f"Years to process: {years}")
    print(f"PDF library: {PDF_LIBRARY}")
    print(f"Max pages per PDF: {MAX_PAGES}")
    print(f"Minimum confidence: {MIN_CONFIDENCE}")
    print("=" * 70)
    print()
    
    total_processed = 0
    total_criminal = 0
    results = []
    
    for year in years:
        input_folder = f"judgments_{year}"
        output_folder = f"criminal_{year}"
        
        # Check if input folder exists, try alternative spelling
        if not os.path.exists(input_folder):
            alt_folder = f"judgement_{year}"
            if os.path.exists(alt_folder):
                input_folder = alt_folder
                print(f"Using '{input_folder}' instead of 'judgments_{year}'")
            else:
                print(f"SKIPPING {year}: Folder 'judgments_{year}' or 'judgement_{year}' not found.")
                continue
        
        print("\n" + "=" * 70)
        print(f"PROCESSING YEAR: {year}")
        print("=" * 70)
        
        # Count files before processing
        pdf_count = len(list(Path(input_folder).glob("*.pdf")))
        
        filter_criminal_cases(
            input_folder=input_folder,
            output_folder=output_folder,
            max_pages=MAX_PAGES,
            min_confidence=MIN_CONFIDENCE,
            verbose=True
        )
        
        # Count criminal cases after processing
        criminal_count = len(list(Path(output_folder).glob("*.pdf"))) if os.path.exists(output_folder) else 0
        
        results.append({
            'year': year,
            'total': pdf_count,
            'criminal': criminal_count,
            'percentage': (criminal_count / pdf_count * 100) if pdf_count > 0 else 0
        })
        
        total_processed += pdf_count
        total_criminal += criminal_count
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY - ALL YEARS")
    print("=" * 70)
    print(f"{'Year':<8} {'Total PDFs':<12} {'Criminal':<12} {'Percentage':<12}")
    print("-" * 70)
    for result in results:
        print(f"{result['year']:<8} {result['total']:<12} {result['criminal']:<12} {result['percentage']:.1f}%")
    print("-" * 70)
    print(f"{'TOTAL':<8} {total_processed:<12} {total_criminal:<12} {(total_criminal/total_processed*100) if total_processed > 0 else 0:.1f}%")
    print("=" * 70)

