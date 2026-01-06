#!/usr/bin/env python3
"""Verify that the created structure matches the problem statement."""

import os

# Required structure from problem statement
required_structure = {
    "investor-agent/app/main.py": "file",
    "investor-agent/app/config.py": "file",
    "investor-agent/app/fmp_client.py": "file",
    "investor-agent/app/metrics.py": "file",
    "investor-agent/app/scoring.py": "file",
    "investor-agent/app/writers/sheets_writer.py": "file",
    "investor-agent/app/writers/excel_writer.py": "file",
    "investor-agent/app/storage/drive_store.py": "file",
    "investor-agent/app/storage/gcs_store.py": "file",
    "investor-agent/requirements.txt": "file",
    "investor-agent/Dockerfile": "file",
    "investor-agent/cloudrun.yaml": "file",
}

print("Verifying repository structure against problem statement...")
print("=" * 70)

all_present = True
for path, type_expected in required_structure.items():
    exists = os.path.exists(path)
    if type_expected == "file":
        is_correct = os.path.isfile(path) if exists else False
    else:
        is_correct = os.path.isdir(path) if exists else False
    
    status = "✓" if is_correct else "✗"
    print(f"{status} {path}")
    
    if not is_correct:
        all_present = False

print("=" * 70)
if all_present:
    print("✅ SUCCESS: All required files from problem statement are present!")
else:
    print("❌ FAILURE: Some required files are missing!")

print("\nBonus files added for completeness:")
bonus_files = [
    "investor-agent/README.md",
    "investor-agent/.env.example",
    "investor-agent/.gitignore",
    "investor-agent/app/__init__.py",
    "investor-agent/app/writers/__init__.py",
    "investor-agent/app/storage/__init__.py",
]

for path in bonus_files:
    if os.path.exists(path):
        print(f"✓ {path}")
