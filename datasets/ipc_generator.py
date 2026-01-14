#!/usr/bin/env python3
"""
Generator for IPC (Indian Penal Code) dataset.
Creates 302 sections with metadata.
"""

import json
import os
from typing import List, Dict, Any


def get_ipc_chapters() -> Dict[int, str]:
    """Return IPC chapters mapping."""
    return {
        1: "Introduction",
        2: "General Explanations",
        3: "Of Punishments",
        4: "General Exceptions",
        5: "Of Abetment",
        6: "Of Criminal Conspiracy",
        7: "Of Offences Against The State",
        8: "Of Offences Relating To The Army, Navy And Air Force",
        9: "Of Offences By Or Relating To Public Servants",
        10: "Of Contempts Of The Lawful Authority Of Public Servants",
        11: "Of False Evidence And Offences Against Public Justice",
        12: "Of Offences Relating To Coin And Government Stamps",
        13: "Of Offences Relating To Weights And Measures",
        14: "Of Offences Affecting The Public Health, Safety, Convenience, Decency And Morals",
        15: "Of Offences Relating To Religion",
        16: "Of Offences Affecting The Human Body",
        17: "Of Offences Against Property",
        18: "Of Offences Relating To Documents And To Property Marks",
        19: "Of The Criminal Breach Of Contracts Of Service",
        20: "Of Offences Relating To Marriage",
        21: "Of Defamation",
        22: "Of Criminal Intimidation, Insult And Annoyance",
        23: "Of Attempts To Commit Offences"
    }


def generate_ipc_section(section_num: int, title: str, text: str, 
                         classification: str = "", punishment: str = "",
                         triable_by: str = "", compoundable: str = "",
                         chapter: int = None) -> Dict[str, Any]:
    """Generate a single IPC section object."""
    return {
        "section_number": section_num,
        "title": title,
        "text": text,
        "classification": classification,
        "punishment": punishment,
        "triable_by": triable_by,
        "compoundable": compoundable,
        "chapter": chapter,
        "metadata": {
            "act": "Indian Penal Code, 1860",
            "act_year": 1860,
            "category": "Criminal Law"
        }
    }


def generate_ipc_dataset(output_dir: str = "datasets"):
    """Generate complete IPC dataset with 302 sections."""
    
    sections = []
    chapters = get_ipc_chapters()
    
    # Generate all 302 sections
    # Note: This is a template structure. Actual text content should be populated
    # from authoritative sources or legal databases.
    
    for section_num in range(1, 303):
        # Determine chapter based on section number (simplified mapping)
        chapter = 1
        if section_num >= 2 and section_num <= 52:
            chapter = 2  # General Explanations
        elif section_num >= 53 and section_num <= 75:
            chapter = 3  # Of Punishments
        elif section_num >= 76 and section_num <= 106:
            chapter = 4  # General Exceptions
        elif section_num >= 107 and section_num <= 120:
            chapter = 5  # Of Abetment
        elif section_num == 120:  # 120A and 120B handled separately if needed
            chapter = 6  # Criminal Conspiracy
        elif section_num >= 121 and section_num <= 130:
            chapter = 7  # Offences Against The State
        elif section_num >= 131 and section_num <= 140:
            chapter = 8  # Offences Relating To Army, Navy And Air Force
        elif section_num >= 141 and section_num <= 160:
            chapter = 9  # Offences By Or Relating To Public Servants
        elif section_num >= 166 and section_num <= 171:
            chapter = 9
        elif section_num >= 172 and section_num <= 190:
            chapter = 10  # Contempts Of Lawful Authority
        elif section_num >= 191 and section_num <= 229:
            chapter = 11  # False Evidence
        elif section_num >= 230 and section_num <= 263:
            chapter = 12  # Coin And Stamps
        elif section_num >= 264 and section_num <= 267:
            chapter = 13  # Weights And Measures
        elif section_num >= 268 and section_num <= 294:
            chapter = 14  # Public Health, Safety
        elif section_num >= 295 and section_num <= 298:
            chapter = 15  # Religion
        elif section_num >= 299 and section_num <= 377:
            chapter = 16  # Human Body
        elif section_num >= 378 and section_num <= 462:
            chapter = 17  # Property
        elif section_num >= 463 and section_num <= 489:
            chapter = 18  # Documents
        elif section_num >= 490 and section_num <= 492:
            chapter = 19  # Breach Of Service
        elif section_num >= 493 and section_num <= 498:
            chapter = 20  # Marriage
        elif section_num >= 499 and section_num <= 502:
            chapter = 21  # Defamation
        elif section_num >= 503 and section_num <= 510:
            chapter = 22  # Criminal Intimidation
        elif section_num >= 511:
            chapter = 23  # Attempts
        
        # Some key sections with sample content
        title = f"Section {section_num}"
        text = f"[Text for IPC Section {section_num} - to be populated from authoritative source]"
        classification = ""
        punishment = ""
        triable_by = ""
        compoundable = ""
        
        # Add specific content for well-known sections
        if section_num == 302:
            title = "Punishment for Murder"
            text = "Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine."
            classification = "Cognizable, Non-bailable"
            punishment = "Death or Imprisonment for life, and fine"
            triable_by = "Court of Session"
            compoundable = "Non-compoundable"
            chapter = 16
        elif section_num == 304:
            title = "Punishment for Culpable Homicide not Amounting to Murder"
            text = "Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life, or imprisonment of either description for a term which may extend to ten years, and shall also be liable to fine, if the act by which the death is caused is done with the intention of causing death, or of causing such bodily injury as is likely to cause death; or with imprisonment of either description for a term which may extend to ten years, or with fine, or with both, if the act is done with the knowledge that it is likely to cause death, but without any intention to cause death, or to cause such bodily injury as is likely to cause death."
            classification = "Cognizable, Non-bailable"
            punishment = "Imprisonment for life or up to 10 years and fine"
            triable_by = "Court of Session"
            compoundable = "Non-compoundable"
            chapter = 16
        elif section_num == 307:
            title = "Attempt to Murder"
            text = "Whoever does any act with such intention or knowledge, and under such circumstances that, if he by that act caused death, he would be guilty of murder, shall be punished with imprisonment of either description for a term which may extend to ten years, and shall also be liable to fine; and if hurt is caused to any person by such act, the offender shall be liable either to imprisonment for life, or to such punishment as is hereinbefore mentioned."
            classification = "Cognizable, Non-bailable"
            punishment = "Imprisonment up to 10 years and fine"
            triable_by = "Court of Session"
            compoundable = "Non-compoundable"
            chapter = 16
        elif section_num == 376:
            title = "Punishment for Rape"
            text = "[Text for IPC Section 376 - to be populated from authoritative source]"
            classification = "Cognizable, Non-bailable"
            punishment = "Rigorous imprisonment not less than 10 years"
            triable_by = "Court of Session"
            compoundable = "Non-compoundable"
            chapter = 16
        
        section_obj = generate_ipc_section(
            section_num, title, text, classification, 
            punishment, triable_by, compoundable, chapter
        )
        sections.append(section_obj)
    
    dataset = {
        "dataset_name": "Indian Penal Code (IPC)",
        "total_sections": 302,
        "act_name": "Indian Penal Code, 1860",
        "act_year": 1860,
        "sections": sections
    }
    
    # Save to file
    output_path = os.path.join(output_dir, "ipc", "ipc_sections.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"IPC dataset generated: {len(sections)} sections")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    generate_ipc_dataset()
