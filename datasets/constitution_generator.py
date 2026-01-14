#!/usr/bin/env python3
"""
Generator for Constitution of India dataset.
Creates all articles and schedules.
"""

import json
import os
from typing import Dict, Any, List


def generate_constitution_article(article_num: str, title: str, text: str, 
                                  part: str = "", schedule: str = None) -> Dict[str, Any]:
    """Generate a single Constitution article object."""
    return {
        "article_number": article_num,
        "title": title,
        "text": text,
        "part": part,
        "schedule": schedule,
        "metadata": {
            "act": "Constitution of India",
            "enacted_year": 1950,
            "category": "Constitutional Law"
        }
    }


def generate_constitution_dataset(output_dir: str = "datasets"):
    """Generate complete Constitution dataset with all articles and schedules."""
    
    articles = []
    
    # Part I: The Union and its Territory (Articles 1-4)
    for i in range(1, 5):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "I"
        if i == 1:
            title = "Name and territory of the Union"
        elif i == 2:
            title = "Admission or establishment of new States"
        elif i == 3:
            title = "Formation of new States and alteration of areas, boundaries or names of existing States"
        elif i == 4:
            title = "Laws made under articles 2 and 3 to provide for the amendment of the First and the Fourth Schedules"
        
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part II: Citizenship (Articles 5-11)
    for i in range(5, 12):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "II"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part III: Fundamental Rights (Articles 12-35)
    for i in range(12, 36):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "III"
        if i == 14:
            title = "Equality before law"
        elif i == 19:
            title = "Protection of certain rights regarding freedom of speech, etc."
        elif i == 21:
            title = "Protection of life and personal liberty"
        elif i == 32:
            title = "Remedies for enforcement of rights conferred by this Part"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part IV: Directive Principles (Articles 36-51)
    for i in range(36, 52):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "IV"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part IVA: Fundamental Duties (Article 51A)
    articles.append(generate_constitution_article("51A", "Fundamental duties", 
        "[Text for Constitution Article 51A - to be populated from authoritative source]", "IVA"))
    
    # Part V: The Union (Articles 52-151)
    for i in range(52, 152):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "V"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part VI: The States (Articles 152-237)
    for i in range(152, 238):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "VI"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part VII: The States in Part B of the First Schedule (repealed)
    # Part VIII: The Union Territories (Articles 239-242)
    for i in range(239, 243):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "VIII"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part IX: The Panchayats (Articles 243-243O)
    for i in range(243, 244):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "IX"
        articles.append(generate_constitution_article(article_num, title, text, part))
    # Add 243A-243O if needed
    
    # Part IXA: The Municipalities (Articles 243P-243ZG)
    # Part X: The Scheduled and Tribal Areas (Articles 244-244A)
    for i in range(244, 245):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "X"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XI: Relations between the Union and the States (Articles 245-263)
    for i in range(245, 264):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XI"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XII: Finance, Property, Contracts and Suits (Articles 264-300A)
    for i in range(264, 301):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XII"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XIII: Trade, Commerce and Intercourse (Articles 301-307)
    for i in range(301, 308):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XIII"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XIV: Services under the Union and the States (Articles 308-323)
    for i in range(308, 324):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XIV"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XIVA: Tribunals (Articles 323A-323B)
    # Part XV: Elections (Articles 324-329A)
    for i in range(324, 330):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XV"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XVI: Special provisions (Articles 330-342)
    for i in range(330, 343):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XVI"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XVII: Official Language (Articles 343-351)
    for i in range(343, 352):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XVII"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XVIII: Emergency Provisions (Articles 352-360)
    for i in range(352, 361):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XVIII"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XIX: Miscellaneous (Articles 361-367)
    for i in range(361, 368):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XIX"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XX: Amendment of the Constitution (Articles 368)
    articles.append(generate_constitution_article("368", "Power of Parliament to amend the Constitution", 
        "[Text for Constitution Article 368 - to be populated from authoritative source]", "XX"))
    
    # Part XXI: Temporary, Transitional and Special Provisions (Articles 369-392)
    for i in range(369, 393):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XXI"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Part XXII: Short title, commencement, etc. (Articles 393-395)
    for i in range(393, 396):
        article_num = str(i)
        title = f"Article {article_num}"
        text = f"[Text for Constitution Article {article_num} - to be populated from authoritative source]"
        part = "XXII"
        articles.append(generate_constitution_article(article_num, title, text, part))
    
    # Generate schedules (12 schedules)
    schedules = []
    schedule_names = [
        "First Schedule: Lists of States and Union Territories",
        "Second Schedule: Emoluments, etc., of the President and Governors",
        "Third Schedule: Forms of Oaths or Affirmations",
        "Fourth Schedule: Allocation of seats in the Council of States",
        "Fifth Schedule: Provisions as to the Administration and Control of Scheduled Areas and Scheduled Tribes",
        "Sixth Schedule: Provisions as to the Administration of Tribal Areas in the States of Assam, Meghalaya, Tripura and Mizoram",
        "Seventh Schedule: List I - Union List, List II - State List, List III - Concurrent List",
        "Eighth Schedule: Languages",
        "Ninth Schedule: Validation of certain Acts and Regulations",
        "Tenth Schedule: Provisions as to disqualification on ground of defection",
        "Eleventh Schedule: Powers, authority and responsibilities of Panchayats",
        "Twelfth Schedule: Powers, authority and responsibilities of Municipalities"
    ]
    
    for i, schedule_name in enumerate(schedule_names, 1):
        schedule_obj = {
            "schedule_number": i,
            "title": schedule_name,
            "content": f"[Content for {schedule_name} - to be populated from authoritative source]",
            "metadata": {
                "act": "Constitution of India",
                "enacted_year": 1950,
                "category": "Constitutional Law"
            }
        }
        schedules.append(schedule_obj)
    
    dataset = {
        "dataset_name": "Constitution of India",
        "total_articles": len(articles),
        "total_schedules": 12,
        "enacted_year": 1950,
        "articles": articles,
        "schedules": schedules
    }
    
    # Save to file
    output_path = os.path.join(output_dir, "constitution", "constitution_articles.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"Constitution dataset generated: {len(articles)} articles, {len(schedules)} schedules")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    generate_constitution_dataset()
