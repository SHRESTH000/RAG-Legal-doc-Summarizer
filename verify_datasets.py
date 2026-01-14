#!/usr/bin/env python3
"""
Script to verify generated datasets.
"""

import json
import os
from pathlib import Path

datasets = {
    "IPC": "datasets/ipc/ipc_sections.json",
    "CrPC": "datasets/crpc/crpc_sections.json",
    "Evidence Act": "datasets/evidence_act/evidence_act_sections.json",
    "Constitution": "datasets/constitution/constitution_articles.json",
    "Judgments": "datasets/judgments/sample_judgments.json"
}

print("Dataset Verification")
print("=" * 60)

for name, path in datasets.items():
    file_path = Path(path)
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            size_kb = file_path.stat().st_size / 1024
            
            if name == "IPC":
                count = data.get("total_sections", len(data.get("sections", [])))
                print(f"{name:20s}: {count:4d} sections, {size_kb:8.1f} KB - Valid JSON")
            elif name == "CrPC":
                count = data.get("total_sections", len(data.get("sections", [])))
                print(f"{name:20s}: {count:4d} sections, {size_kb:8.1f} KB - Valid JSON")
            elif name == "Evidence Act":
                count = data.get("total_sections", len(data.get("sections", [])))
                print(f"{name:20s}: {count:4d} sections, {size_kb:8.1f} KB - Valid JSON")
            elif name == "Constitution":
                articles = data.get("total_articles", len(data.get("articles", [])))
                schedules = data.get("total_schedules", len(data.get("schedules", [])))
                print(f"{name:20s}: {articles:4d} articles, {schedules:2d} schedules, {size_kb:8.1f} KB - Valid JSON")
            elif name == "Judgments":
                count = data.get("total_judgments", len(data.get("judgments", [])))
                print(f"{name:20s}: {count:4d} judgments, {size_kb:8.1f} KB - Valid JSON")
        except Exception as e:
            print(f"{name:20s}: ERROR - {e}")
    else:
        print(f"{name:20s}: NOT FOUND")

print("=" * 60)
