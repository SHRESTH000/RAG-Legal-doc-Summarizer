#!/usr/bin/env python3
"""
Generator for CrPC (Criminal Procedure Code) dataset.
Creates 484 sections.
"""

import json
import os
from typing import Dict, Any


def generate_crpc_section(section_num: int, title: str, text: str, 
                          chapter: int = None, part: str = "") -> Dict[str, Any]:
    """Generate a single CrPC section object."""
    return {
        "section_number": section_num,
        "title": title,
        "text": text,
        "chapter": chapter,
        "part": part,
        "metadata": {
            "act": "Code of Criminal Procedure, 1973",
            "act_year": 1973,
            "category": "Criminal Procedure"
        }
    }


def generate_crpc_dataset(output_dir: str = "datasets"):
    """Generate complete CrPC dataset with 484 sections."""
    
    sections = []
    
    # Generate all 484 sections
    # Note: This is a template structure. Actual text content should be populated
    # from authoritative sources or legal databases.
    
    for section_num in range(1, 485):
        # Determine part and chapter based on section number (simplified mapping)
        part = "I"  # Preliminary
        chapter = 1
        
        if section_num >= 1 and section_num <= 5:
            part = "I"
            chapter = 1  # Preliminary
        elif section_num >= 6 and section_num <= 25:
            part = "I"
            chapter = 2  # Constitution of Criminal Courts
        elif section_num >= 26 and section_num <= 35:
            part = "I"
            chapter = 3  # Powers of Courts
        elif section_num >= 36 and section_num <= 40:
            part = "I"
            chapter = 4  # Aid and Information to the Magistrates
        elif section_num >= 41 and section_num <= 60:
            part = "II"
            chapter = 5  # Arrest of Persons
        elif section_num >= 61 and section_num <= 90:
            part = "III"
            chapter = 6  # Processes to Compel Appearance
        elif section_num >= 91 and section_num <= 105:
            part = "IV"
            chapter = 7  # Processes to Compel the Production of Things
        elif section_num >= 106 and section_num <= 124:
            part = "V"
            chapter = 8  # Security for Keeping the Peace
        elif section_num >= 125 and section_num <= 128:
            part = "V"
            chapter = 9  # Order for Maintenance
        elif section_num >= 129 and section_num <= 148:
            part = "V"
            chapter = 10  # Maintenance of Public Order
        elif section_num >= 149 and section_num <= 153:
            part = "VI"
            chapter = 11  # Preventive Action of the Police
        elif section_num >= 154 and section_num <= 176:
            part = "VII"
            chapter = 12  # Information to the Police and their Powers
        elif section_num >= 177 and section_num <= 189:
            part = "VIII"
            chapter = 13  # Jurisdiction of the Criminal Courts
        elif section_num >= 190 and section_num <= 199:
            part = "IX"
            chapter = 14  # Conditions Requisite for Initiation of Proceedings
        elif section_num >= 200 and section_num <= 203:
            part = "IX"
            chapter = 15  # Complaints to Magistrates
        elif section_num >= 204 and section_num <= 210:
            part = "IX"
            chapter = 16  # Commencement of Proceedings
        elif section_num >= 211 and section_num <= 224:
            part = "X"
            chapter = 17  # The Charge
        elif section_num >= 225 and section_num <= 237:
            part = "X"
            chapter = 18  # Trial before a Court of Session
        elif section_num >= 238 and section_num <= 250:
            part = "XI"
            chapter = 19  # Trial of Warrant-Cases
        elif section_num >= 251 and section_num <= 259:
            part = "XII"
            chapter = 20  # Trial of Summons-Cases
        elif section_num >= 260 and section_num <= 265:
            part = "XIII"
            chapter = 21  # Summary Trials
        elif section_num >= 266 and section_num <= 300:
            part = "XIV"
            chapter = 22  # Provisions as to Bail and Bonds
        elif section_num >= 301 and section_num <= 310:
            part = "XV"
            chapter = 23  # General Provisions as to Inquiries and Trials
        elif section_num >= 311 and section_num <= 326:
            part = "XVI"
            chapter = 24  # Provisions as to Accused Persons
        elif section_num >= 327 and section_num <= 356:
            part = "XVII"
            chapter = 25  # Evidence in Inquiries and Trials
        elif section_num >= 357 and section_num <= 360:
            part = "XVIII"
            chapter = 26  # Judgment
        elif section_num >= 361 and section_num <= 370:
            part = "XIX"
            chapter = 27  # Submission of Death Sentences
        elif section_num >= 371 and section_num <= 388:
            part = "XX"
            chapter = 28  # Appeals
        elif section_num >= 389 and section_num <= 394:
            part = "XXI"
            chapter = 29  # Reference and Revision
        elif section_num >= 395 and section_num <= 405:
            part = "XXII"
            chapter = 30  # Special Provisions
        elif section_num >= 406 and section_num <= 412:
            part = "XXIII"
            chapter = 31  # Transfer of Criminal Cases
        elif section_num >= 413 and section_num <= 416:
            part = "XXIV"
            chapter = 32  # Execution, Suspension, Remission and Commutation
        elif section_num >= 417 and section_num <= 442:
            part = "XXV"
            chapter = 33  # Provisions as to Bail and Bonds
        elif section_num >= 443 and section_num <= 450:
            part = "XXVI"
            chapter = 34  # Disposal of Property
        elif section_num >= 451 and section_num <= 459:
            part = "XXVII"
            chapter = 35  # Irregular Proceedings
        elif section_num >= 460 and section_num <= 466:
            part = "XXVIII"
            chapter = 36  # Limitation for Taking Cognizance
        elif section_num >= 467 and section_num <= 473:
            part = "XXIX"
            chapter = 37  # Miscellaneous
        else:
            part = "XXX"
            chapter = 38
        
        title = f"Section {section_num}"
        text = f"[Text for CrPC Section {section_num} - to be populated from authoritative source]"
        
        # Add specific content for key sections
        if section_num == 41:
            title = "When police may arrest without warrant"
            text = "[Text for CrPC Section 41 - to be populated from authoritative source]"
        elif section_num == 154:
            title = "Information in cognizable cases"
            text = "[Text for CrPC Section 154 - to be populated from authoritative source]"
        elif section_num == 156:
            title = "Police officer's power to investigate cognizable case"
            text = "[Text for CrPC Section 156 - to be populated from authoritative source]"
        elif section_num == 161:
            title = "Examination of witnesses by police"
            text = "[Text for CrPC Section 161 - to be populated from authoritative source]"
        elif section_num == 167:
            title = "Procedure when investigation cannot be completed in twenty four hours"
            text = "[Text for CrPC Section 167 - to be populated from authoritative source]"
        elif section_num == 173:
            title = "Report of police officer on completion of investigation"
            text = "[Text for CrPC Section 173 - to be populated from authoritative source]"
        elif section_num == 190:
            title = "Cognizance of offences by Magistrates"
            text = "[Text for CrPC Section 190 - to be populated from authoritative source]"
        elif section_num == 313:
            title = "Power to examine the accused"
            text = "[Text for CrPC Section 313 - to be populated from authoritative source]"
        elif section_num == 438:
            title = "Direction for grant of bail to person apprehending arrest"
            text = "[Text for CrPC Section 438 - to be populated from authoritative source]"
        
        section_obj = generate_crpc_section(
            section_num, title, text, chapter, part
        )
        sections.append(section_obj)
    
    dataset = {
        "dataset_name": "Code of Criminal Procedure (CrPC)",
        "total_sections": 484,
        "act_name": "Code of Criminal Procedure, 1973",
        "act_year": 1973,
        "sections": sections
    }
    
    # Save to file
    output_path = os.path.join(output_dir, "crpc", "crpc_sections.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"CrPC dataset generated: {len(sections)} sections")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    generate_crpc_dataset()
