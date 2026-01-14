#!/usr/bin/env python3
"""
Generator for Indian Evidence Act dataset.
Creates 167 sections.
"""

import json
import os
from typing import Dict, Any


def generate_evidence_section(section_num: int, title: str, text: str, 
                               part: str = "", chapter: int = None) -> Dict[str, Any]:
    """Generate a single Evidence Act section object."""
    return {
        "section_number": section_num,
        "title": title,
        "text": text,
        "part": part,
        "chapter": chapter,
        "metadata": {
            "act": "Indian Evidence Act, 1872",
            "act_year": 1872,
            "category": "Evidence Law"
        }
    }


def generate_evidence_dataset(output_dir: str = "datasets"):
    """Generate complete Evidence Act dataset with 167 sections."""
    
    sections = []
    
    # Generate all 167 sections
    # Note: This is a template structure. Actual text content should be populated
    # from authoritative sources or legal databases.
    
    for section_num in range(1, 168):
        # Determine part and chapter based on section number (simplified mapping)
        part = "I"
        chapter = 1
        
        if section_num >= 1 and section_num <= 4:
            part = "I"
            chapter = 1  # Preliminary
        elif section_num >= 5 and section_num <= 55:
            part = "II"
            chapter = 2  # Of the Relevancy of Facts
        elif section_num >= 56 and section_num <= 58:
            part = "II"
            chapter = 3  # Facts which need not be proved
        elif section_num >= 59 and section_num <= 90:
            part = "III"
            chapter = 4  # Of Oral Evidence
        elif section_num >= 61 and section_num <= 90:
            part = "IV"
            chapter = 5  # Of Documentary Evidence
        elif section_num >= 91 and section_num <= 100:
            part = "IV"
            chapter = 6  # Exclusion of oral by documentary evidence
        elif section_num >= 101 and section_num <= 114:
            part = "V"
            chapter = 7  # Of the Burden of Proof
        elif section_num >= 115 and section_num <= 117:
            part = "VI"
            chapter = 8  # Estoppel
        elif section_num >= 118 and section_num <= 134:
            part = "VII"
            chapter = 9  # Of Witnesses
        elif section_num >= 135 and section_num <= 166:
            part = "VIII"
            chapter = 10  # Of the Examination of Witnesses
        elif section_num == 167:
            part = "IX"
            chapter = 11  # Improper admission or rejection of evidence
        
        title = f"Section {section_num}"
        text = f"[Text for Evidence Act Section {section_num} - to be populated from authoritative source]"
        
        # Add specific content for key sections
        if section_num == 3:
            title = "Interpretation clause"
            text = "[Text for Evidence Act Section 3 - to be populated from authoritative source]"
        elif section_num == 5:
            title = "Evidence may be given of facts in issue and relevant facts"
            text = "[Text for Evidence Act Section 5 - to be populated from authoritative source]"
        elif section_num == 101:
            title = "Burden of proof"
            text = "[Text for Evidence Act Section 101 - to be populated from authoritative source]"
        elif section_num == 115:
            title = "Estoppel"
            text = "[Text for Evidence Act Section 115 - to be populated from authoritative source]"
        elif section_num == 118:
            title = "Who may testify"
            text = "[Text for Evidence Act Section 118 - to be populated from authoritative source]"
        elif section_num == 137:
            title = "Examination-in-chief, Cross-examination and Re-examination"
            text = "[Text for Evidence Act Section 137 - to be populated from authoritative source]"
        
        section_obj = generate_evidence_section(
            section_num, title, text, part, chapter
        )
        sections.append(section_obj)
    
    dataset = {
        "dataset_name": "Indian Evidence Act",
        "total_sections": 167,
        "act_name": "Indian Evidence Act, 1872",
        "act_year": 1872,
        "sections": sections
    }
    
    # Save to file
    output_path = os.path.join(output_dir, "evidence_act", "evidence_act_sections.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"Evidence Act dataset generated: {len(sections)} sections")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    generate_evidence_dataset()
