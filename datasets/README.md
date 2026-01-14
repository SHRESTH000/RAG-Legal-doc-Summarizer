# Legal Judgment Summarization Datasets

This directory contains structured datasets for legal judgment summarization and RAG implementation.

## Dataset Structure

### 1. IPC Dataset (Indian Penal Code)
- **File**: `datasets/ipc/ipc_sections.json`
- **Format**: JSON array of section objects
- **Total Sections**: 302
- **Fields**: 
  - section_number
  - title
  - text
  - classification (cognizable/non-cognizable, bailable/non-bailable)
  - punishment
  - triable_by
  - compoundable
  - chapter
  - metadata

### 2. CrPC Dataset (Criminal Procedure Code)
- **File**: `datasets/crpc/crpc_sections.json`
- **Format**: JSON array of section objects
- **Total Sections**: 484
- **Fields**:
  - section_number
  - title
  - text
  - chapter
  - part
  - metadata

### 3. Evidence Act Dataset
- **File**: `datasets/evidence_act/evidence_act_sections.json`
- **Format**: JSON array of section objects
- **Total Sections**: 167
- **Fields**:
  - section_number
  - title
  - text
  - part
  - chapter
  - metadata

### 4. Constitution Dataset
- **File**: `datasets/constitution/constitution_articles.json`
- **Format**: JSON array of article objects
- **Fields**:
  - article_number
  - title
  - text
  - part
  - schedule (if applicable)
  - metadata

### 5. Sample Judgments Dataset
- **File**: `datasets/judgments/sample_judgments.json`
- **Format**: JSON array of judgment objects
- **Total**: 5 Supreme Court judgments
- **Fields**:
  - case_number
  - parties
  - date
  - court
  - judges
  - full_text
  - summary
  - key_points
  - relevant_sections
  - metadata

## Usage

Generate all datasets:
```bash
python generate_datasets.py
```

Generate specific dataset:
```bash
python generate_datasets.py --dataset ipc
python generate_datasets.py --dataset crpc
python generate_datasets.py --dataset evidence
python generate_datasets.py --dataset constitution
python generate_datasets.py --dataset judgments
```

## Dataset Format

All datasets use JSON format for easy integration with RAG systems:

```json
{
  "dataset_name": "IPC",
  "total_sections": 302,
  "sections": [
    {
      "section_number": 302,
      "title": "Punishment for Murder",
      "text": "...",
      "metadata": {
        "classification": "...",
        "punishment": "...",
        "triable_by": "..."
      }
    }
  ]
}
```
