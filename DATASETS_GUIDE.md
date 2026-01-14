# Legal Judgment Summarization Datasets Guide

This document provides an overview of the datasets created for legal judgment summarization and RAG implementation.

## Dataset Overview

All datasets have been successfully generated and are stored in the `datasets/` directory. Each dataset is in JSON format for easy integration with RAG systems.

## 1. IPC Dataset (Indian Penal Code)

**Location**: `datasets/ipc/ipc_sections.json`

**Contents**:
- **Total Sections**: 302 sections
- **Format**: JSON array of section objects
- **Structure**: Each section includes:
  - `section_number`: Section number (1-302)
  - `title`: Section title
  - `text`: Full text of the section (placeholder text for most sections)
  - `classification`: Cognizable/Non-cognizable, Bailable/Non-bailable
  - `punishment`: Punishment details
  - `triable_by`: Which court can try the case
  - `compoundable`: Whether the offence is compoundable
  - `chapter`: Chapter number (1-23)
  - `metadata`: Additional metadata including act name, year, category

**Key Sections Included**:
- Section 302: Punishment for Murder (with full text)
- Section 304: Culpable Homicide not Amounting to Murder
- Section 307: Attempt to Murder
- Section 376: Punishment for Rape

**Note**: Most sections contain placeholder text that should be populated from authoritative legal sources.

## 2. CrPC Dataset (Criminal Procedure Code)

**Location**: `datasets/crpc/crpc_sections.json`

**Contents**:
- **Total Sections**: 484 sections
- **Format**: JSON array of section objects
- **Structure**: Each section includes:
  - `section_number`: Section number (1-484)
  - `title`: Section title
  - `text`: Full text of the section (placeholder text for most sections)
  - `chapter`: Chapter number (1-37)
  - `part`: Part number (I-XXX)
  - `metadata`: Additional metadata including act name, year, category

**Key Sections Mapped**:
- Section 41: When police may arrest without warrant
- Section 154: Information in cognizable cases
- Section 156: Police officer's power to investigate
- Section 161: Examination of witnesses by police
- Section 167: Procedure when investigation cannot be completed
- Section 173: Report of police officer on completion of investigation
- Section 190: Cognizance of offences by Magistrates
- Section 313: Power to examine the accused
- Section 438: Direction for grant of bail (Anticipatory Bail)

## 3. Evidence Act Dataset

**Location**: `datasets/evidence_act/evidence_act_sections.json`

**Contents**:
- **Total Sections**: 167 sections
- **Format**: JSON array of section objects
- **Structure**: Each section includes:
  - `section_number`: Section number (1-167)
  - `title`: Section title
  - `text`: Full text of the section (placeholder text for most sections)
  - `part`: Part number (I-IX)
  - `chapter`: Chapter number (1-11)
  - `metadata`: Additional metadata including act name, year, category

**Key Sections Mapped**:
- Section 3: Interpretation clause
- Section 5: Evidence may be given of facts in issue and relevant facts
- Section 101: Burden of proof
- Section 115: Estoppel
- Section 118: Who may testify
- Section 137: Examination-in-chief, Cross-examination and Re-examination

## 4. Constitution Dataset

**Location**: `datasets/constitution/constitution_articles.json`

**Contents**:
- **Total Articles**: 395 articles
- **Total Schedules**: 12 schedules
- **Format**: JSON object with articles and schedules arrays
- **Structure**: 
  - **Articles**: Each article includes:
    - `article_number`: Article number (as string, e.g., "1", "14", "21")
    - `title`: Article title
    - `text`: Full text of the article (placeholder text for most articles)
    - `part`: Part number (I-XXII)
    - `schedule`: Schedule reference if applicable
    - `metadata`: Additional metadata including enacted year, category
  
  - **Schedules**: Each schedule includes:
    - `schedule_number`: Schedule number (1-12)
    - `title`: Schedule title
    - `content`: Schedule content (placeholder text)
    - `metadata`: Additional metadata

**Parts Covered**:
- Part I: The Union and its Territory (Articles 1-4)
- Part II: Citizenship (Articles 5-11)
- Part III: Fundamental Rights (Articles 12-35)
- Part IV: Directive Principles (Articles 36-51)
- Part IVA: Fundamental Duties (Article 51A)
- Part V: The Union (Articles 52-151)
- Part VI: The States (Articles 152-237)
- Part VIII: The Union Territories (Articles 239-242)
- Part IX: The Panchayats (Articles 243+)
- Part X: The Scheduled and Tribal Areas (Articles 244-244A)
- Part XI: Relations between the Union and the States (Articles 245-263)
- Part XII: Finance, Property, Contracts and Suits (Articles 264-300A)
- Part XIII: Trade, Commerce and Intercourse (Articles 301-307)
- Part XIV: Services under the Union and the States (Articles 308-323)
- Part XV: Elections (Articles 324-329A)
- Part XVI: Special provisions (Articles 330-342)
- Part XVII: Official Language (Articles 343-351)
- Part XVIII: Emergency Provisions (Articles 352-360)
- Part XIX: Miscellaneous (Articles 361-367)
- Part XX: Amendment of the Constitution (Article 368)
- Part XXI: Temporary, Transitional and Special Provisions (Articles 369-392)
- Part XXII: Short title, commencement, etc. (Articles 393-395)

**Schedules**:
1. Lists of States and Union Territories
2. Emoluments, etc., of the President and Governors
3. Forms of Oaths or Affirmations
4. Allocation of seats in the Council of States
5. Provisions as to the Administration and Control of Scheduled Areas and Scheduled Tribes
6. Provisions as to the Administration of Tribal Areas
7. Union List, State List, Concurrent List
8. Languages
9. Validation of certain Acts and Regulations
10. Provisions as to disqualification on ground of defection
11. Powers, authority and responsibilities of Panchayats
12. Powers, authority and responsibilities of Municipalities

## 5. Sample Judgments Dataset

**Location**: `datasets/judgments/sample_judgments.json`

**Contents**:
- **Total Judgments**: 5 Supreme Court judgments
- **Source**: Extracted from `judgments_2024/` directory
- **Format**: JSON array of judgment objects
- **Structure**: Each judgment includes:
  - `case_number`: Case number (extracted from PDF)
  - `parties`: Parties to the case (Petitioner vs Respondent)
  - `date`: Date of judgment
  - `court`: Court name (Supreme Court of India)
  - `judges`: List of judges who decided the case
  - `full_text`: Full extracted text from PDF (limited to 50,000 characters)
  - `summary`: Generated summary of the judgment
  - `key_points`: Key points extracted from the judgment
  - `relevant_sections`: List of relevant legal sections (IPC, CrPC, Evidence Act)
  - `metadata`: Source file, directory, text length, extraction method

**Extraction Method**:
- Automatically extracts text from PDF files
- Identifies case numbers, parties, dates, judges
- Extracts relevant legal sections referenced
- Generates summaries and key points

## Usage

### Generate All Datasets

```bash
python generate_datasets.py
```

### Generate Specific Dataset

```bash
python generate_datasets.py --dataset ipc
python generate_datasets.py --dataset crpc
python generate_datasets.py --dataset evidence
python generate_datasets.py --dataset constitution
python generate_datasets.py --dataset judgments
```

### Generate Multiple Datasets

```bash
python generate_datasets.py --dataset ipc --dataset crpc
```

## Dataset Statistics

| Dataset | Count | File Size (approx) | Status |
|---------|-------|-------------------|--------|
| IPC | 302 sections | ~500 KB | ✅ Generated |
| CrPC | 484 sections | ~800 KB | ✅ Generated |
| Evidence Act | 167 sections | ~300 KB | ✅ Generated |
| Constitution | 395 articles + 12 schedules | ~600 KB | ✅ Generated |
| Judgments | 5 judgments | Varies (5-20 MB) | ✅ Generated |

## Notes for RAG Implementation

1. **Text Content**: Most legal sections contain placeholder text. For production use, populate with actual legal text from authoritative sources (e.g., India Code, legal databases).

2. **Metadata**: All datasets include rich metadata that can be used for:
   - Filtering by act, year, category
   - Chapter/Part-based organization
   - Section/article number indexing

3. **Judgment Dataset**: The sample judgments dataset includes:
   - Full text for comprehensive search
   - Summaries for quick reference
   - Key points for structured information
   - Relevant sections for cross-referencing

4. **JSON Format**: All datasets use JSON format for easy:
   - Loading into vector databases
   - Integration with LLM frameworks
   - Programmatic access
   - Serialization/deserialization

5. **Encoding**: All files are UTF-8 encoded to support Unicode characters.

## Next Steps for RAG Implementation

1. **Populate Legal Text**: Fill in the actual text for IPC, CrPC, Evidence Act sections, and Constitution articles from authoritative sources.

2. **Vector Database**: Load datasets into a vector database (e.g., Pinecone, Weaviate, ChromaDB) for semantic search.

3. **Embedding Model**: Choose an appropriate embedding model (e.g., sentence-transformers, OpenAI embeddings) for legal text.

4. **Chunking Strategy**: Implement chunking strategy for large sections/articles/judgments.

5. **Metadata Filtering**: Leverage metadata for filtering and refinement in RAG queries.

6. **Judgment Processing**: Process more judgments to expand the judgment dataset.

## File Structure

```
datasets/
├── README.md
├── __init__.py
├── ipc/
│   └── ipc_sections.json
├── crpc/
│   └── crpc_sections.json
├── evidence_act/
│   └── evidence_act_sections.json
├── constitution/
│   └── constitution_articles.json
├── judgments/
│   └── sample_judgments.json
├── ipc_generator.py
├── crpc_generator.py
├── evidence_generator.py
├── constitution_generator.py
└── judgments_generator.py
```

## Generation Scripts

Each dataset has its own generator script in the `datasets/` directory:
- `ipc_generator.py`: Generates IPC dataset
- `crpc_generator.py`: Generates CrPC dataset
- `evidence_generator.py`: Generates Evidence Act dataset
- `constitution_generator.py`: Generates Constitution dataset
- `judgments_generator.py`: Generates sample judgments dataset

These can be run independently or through the main `generate_datasets.py` script.
