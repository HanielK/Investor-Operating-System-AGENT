#!/usr/bin/env python3
"""
Validation script to verify the investor-agent structure.
"""

import os
import sys

def validate_structure():
    """Validate that all required files exist."""
    required_files = [
        "app/main.py",
        "app/config.py",
        "app/fmp_client.py",
        "app/metrics.py",
        "app/scoring.py",
        "app/writers/sheets_writer.py",
        "app/writers/excel_writer.py",
        "app/storage/drive_store.py",
        "app/storage/gcs_store.py",
        "requirements.txt",
        "Dockerfile",
        "cloudrun.yaml",
        "README.md",
        ".env.example",
        ".gitignore"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("✓ All required files present")
    
    # Check that __init__.py files exist
    init_files = [
        "app/__init__.py",
        "app/writers/__init__.py",
        "app/storage/__init__.py"
    ]
    
    missing_init = []
    for file_path in init_files:
        if not os.path.exists(file_path):
            missing_init.append(file_path)
    
    if missing_init:
        print("❌ Missing __init__.py files:")
        for file_path in missing_init:
            print(f"  - {file_path}")
        return False
    
    print("✓ All __init__.py files present")
    
    # Verify Python syntax
    print("\nChecking Python syntax...")
    python_files = []
    for root, dirs, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    for py_file in python_files:
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), py_file, 'exec')
            print(f"  ✓ {py_file}")
        except SyntaxError as e:
            print(f"  ❌ {py_file}: {e}")
            return False
    
    print("\n✅ Structure validation passed!")
    return True

if __name__ == "__main__":
    success = validate_structure()
    sys.exit(0 if success else 1)
