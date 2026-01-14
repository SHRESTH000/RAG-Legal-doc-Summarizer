# Criminal Cases Filtering Tool

A Python tool to automatically filter criminal cases from Supreme Court judgement PDFs with high accuracy.

## Features

- **High Accuracy Detection**: Uses multiple detection methods including:
  - Criminal Appeal/Writ patterns (Crl.A., Crl.W.P., etc.)
  - IPC (Indian Penal Code) section numbers
  - Legal terminology (accused, prosecution, conviction, etc.)
  - Case type indicators
- **Confidence Scoring**: Each case is assigned a confidence score (0-100%)
- **Batch Processing**: Processes hundreds or thousands of PDF files efficiently
- **Detailed Reporting**: Generates verification reports with statistics

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

Recommended library: `pdfplumber` (best text extraction quality)
```bash
pip install pdfplumber
```

Alternative libraries (automatically detected if pdfplumber is not available):
```bash
pip install PyPDF2
# or
pip install pypdf
```

## Usage

### Basic Usage

**Process multiple years (2020-2025) by default:**
```bash
python filter_criminal_cases.py
```

This will:
- Process years 2020-2025 automatically
- Read all PDFs from each `judgments_YYYY` folder
- Identify criminal cases
- Copy them to corresponding `criminal_YYYY` folders

**Process specific year(s):**
```bash
python filter_criminal_cases.py 2020 2021 2022
```

**Process single year (2019 example):**
Edit the script configuration section, or use:
```bash
# Modify script to process 2019, or use as module
```

### Custom Configuration

Edit the configuration in `filter_criminal_cases.py`:

```python
INPUT_FOLDER = "judgments_2019"      # Source folder
OUTPUT_FOLDER = "criminal_2019"      # Destination folder
MAX_PAGES = 5                        # Pages to read per PDF (default: 5)
MIN_CONFIDENCE = 0.3                 # Minimum confidence threshold (0.3 = 30%)
```

### Using as a Module

```python
from filter_criminal_cases import filter_criminal_cases

filter_criminal_cases(
    input_folder="judgments_2019",
    output_folder="criminal_2019",
    max_pages=5,
    min_confidence=0.3,
    verbose=True
)
```

## Verification

After filtering, verify the results:
```bash
python verify_criminal_filtering.py
```

This generates:
- Summary statistics
- Confidence score distribution
- Top detection indicators
- Detailed JSON report (`criminal_filtering_report.json`)

## Results

Based on processing judgements from 2019-2025:
- **Total Files Processed (All Years)**: 5,441
- **Total Criminal Cases Found**: 1,705 (31.3%)
- **Average Confidence (2019 sample)**: 94%
- **High Confidence Cases (≥70%)**: 90% of filtered cases

### Year-by-Year Results:
- **2019**: 296/1,050 (28.2%)
- **2020**: 139/571 (24.3%)
- **2021**: 203/708 (28.7%)
- **2022**: 279/1,017 (27.4%)
- **2023**: 276/854 (32.3%)
- **2024**: 296/782 (37.9%)
- **2025**: 216/459 (47.1%)

### Top Detection Indicators:
- Accused (90%)
- Criminal Appeal (87%)
- Prosecution (83%)
- IPC/Indian Penal Code (67%)
- Offence (60%)

## How It Works

1. **Text Extraction**: Reads first 5 pages of each PDF (usually sufficient for classification)
2. **Pattern Matching**: Searches for multiple criminal case indicators:
   - Case number patterns (Crl.A., Crl.W.P., etc.)
   - IPC section references
   - Legal terminology
3. **Scoring**: Assigns weighted scores to different indicators
4. **Classification**: Cases with score ≥ 10 points (confidence ≥ 30%) are classified as criminal

## Detection Indicators

### High Confidence Indicators (strong signals):
- Criminal Appeal/Writ patterns
- IPC section numbers
- Indian Penal Code references
- Case numbers (Crl.A., Crl.W.P., etc.)

### Medium Confidence Indicators:
- Criminal case/proceedings terminology
- Legal terms (accused, prosecution, conviction, etc.)
- State vs. patterns (often criminal cases)

## Accuracy

The tool uses multiple indicators to minimize false positives:
- **Threshold**: Minimum 10 points (30% confidence) required
- **Multiple Signals**: Requires multiple indicators for classification
- **Context-Aware**: Patterns are matched with word boundaries to avoid false matches

## Files

- `filter_criminal_cases.py` - Main filtering script
- `verify_criminal_filtering.py` - Verification and reporting tool
- `requirements.txt` - Python dependencies
- `criminal_filtering_report.json` - Generated verification report

## Notes

- Processing time: ~1-2 seconds per PDF
- First 5 pages are sufficient for classification in most cases
- All original files remain unchanged (files are copied, not moved)
- Can be easily adapted for other years or case types

## Troubleshooting

**No PDF library found:**
```bash
pip install pdfplumber
```

**Poor text extraction quality:**
- Install `pdfplumber` (better than PyPDF2/pypdf)
- Increase `MAX_PAGES` if needed

**Too many/too few cases filtered:**
- Adjust `MIN_CONFIDENCE` threshold (lower = more cases, higher = fewer cases)
- Recommended range: 0.3-0.5

## License

Free to use and modify.
