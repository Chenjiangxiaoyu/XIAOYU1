# core/loader.py

import os
import json

def load_skills(path="skills"):
    skills = []

    for file in os.listdir(path):
        if file.endswith(".json"):
            with open(f"{path}/{file}", "r", encoding="utf-8") as f:
                skills.append(json.load(f))

    return skills