#!/usr/bin/env python3
"""
Verification script for Star Map Editor installation.

This script checks that:
1. All required directories exist
2. All Python modules can be imported
3. The application can be launched

Run this before testing the application.
"""

import sys
from pathlib import Path

def check_directories():
    """Check that all required directories exist."""
    print("🔍 Checking directory structure...")
    
    base_dir = Path(__file__).parent
    required_dirs = [
        "core",
        "Saves",
        "Exports",
        "resources",
        "resources/icons",
        "resources/example_templates"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ - MISSING!")
            all_exist = False
    
    return all_exist

def check_files():
    """Check that all required Python files exist."""
    print("\n🔍 Checking Python files...")
    
    base_dir = Path(__file__).parent
    required_files = [
        "main.py",
        "gui.py",
        "core/__init__.py",
        "core/project_model.py",
        "core/project_io.py",
        "core/systems.py",
        "core/templates.py"
    ]
    
    all_exist = True
    for file_name in required_files:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} - MISSING!")
            all_exist = False
    
    return all_exist

def check_imports():
    """Check that core modules can be imported."""
    print("\n🔍 Checking module imports...")
    
    try:
        print("  📦 Importing PySide6...", end=" ")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        print("✅")
    except ImportError as e:
        print(f"❌\n  Error: {e}")
        print("  Please install: pip install PySide6")
        return False
    
    try:
        print("  📦 Importing core modules...", end=" ")
        sys.path.insert(0, str(Path(__file__).parent))
        from core import (
            MapProject, TemplateData, SystemData, 
            SystemItem, SystemDialog, TemplateItem
        )
        from core.project_io import save_project, load_project, export_map_data
        print("✅")
    except ImportError as e:
        print(f"❌\n  Error: {e}")
        return False
    
    return True

def check_syntax():
    """Check Python syntax of all modules."""
    print("\n🔍 Checking Python syntax...")
    
    import py_compile
    
    base_dir = Path(__file__).parent
    python_files = [
        "main.py",
        "gui.py",
        "core/__init__.py",
        "core/project_model.py",
        "core/project_io.py",
        "core/systems.py",
        "core/templates.py"
    ]
    
    all_valid = True
    for file_name in python_files:
        file_path = base_dir / file_name
        try:
            py_compile.compile(str(file_path), doraise=True)
            print(f"  ✅ {file_name}")
        except py_compile.PyCompileError as e:
            print(f"  ❌ {file_name} - SYNTAX ERROR!")
            print(f"     {e}")
            all_valid = False
    
    return all_valid

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Star Map Editor - Installation Verification")
    print("=" * 60)
    
    checks = [
        ("Directory structure", check_directories),
        ("Required files", check_files),
        ("Python syntax", check_syntax),
        ("Module imports", check_imports),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n❌ Error during '{check_name}': {e}")
            results[check_name] = False
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All checks passed! You can run the application:")
        print("   python main.py\n")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
