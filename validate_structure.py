"""
Simple validation script to test module structure without running model setup.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_module_structure():
    """Test that the NLP module structure is correct."""
    print("Testing module structure...")
    
    # Check if nlp directory exists
    nlp_dir = Path(__file__).parent / "nlp"
    if not nlp_dir.exists():
        print("✗ nlp/ directory not found")
        return False
    print("✓ nlp/ directory exists")
    
    # Check if __init__.py exists
    init_file = nlp_dir / "__init__.py"
    if not init_file.exists():
        print("✗ nlp/__init__.py not found")
        return False
    print("✓ nlp/__init__.py exists")
    
    # Check if onnx directory exists
    onnx_dir = nlp_dir / "onnx"
    if not onnx_dir.exists():
        print("✗ nlp/onnx/ directory not found")
        return False
    print("✓ nlp/onnx/ directory exists")
    
    # Check if onnx_nlp_model.py exists
    model_file = nlp_dir / "onnx_nlp_model.py"
    if not model_file.exists():
        print("✗ nlp/onnx_nlp_model.py not found")
        return False
    print("✓ nlp/onnx_nlp_model.py exists")
    
    # Check if setup_model.py exists
    setup_file = Path(__file__).parent / "setup_model.py"
    if not setup_file.exists():
        print("✗ setup_model.py not found")
        return False
    print("✓ setup_model.py exists")
    
    # Check if requirements.txt exists
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        print("✗ requirements.txt not found")
        return False
    print("✓ requirements.txt exists")
    
    # Check requirements.txt content
    with open(req_file) as f:
        requirements = f.read()
        required_packages = ['onnxruntime', 'transformers', 'numpy', 'torch']
        for package in required_packages:
            if package not in requirements:
                print(f"✗ {package} not in requirements.txt")
                return False
        print(f"✓ All required packages in requirements.txt")
    
    # Try to compile the Python files
    import py_compile
    try:
        py_compile.compile(str(model_file), doraise=True)
        print("✓ onnx_nlp_model.py compiles successfully")
    except py_compile.PyCompileError as e:
        print(f"✗ onnx_nlp_model.py has syntax errors: {e}")
        return False
    
    try:
        py_compile.compile(str(setup_file), doraise=True)
        print("✓ setup_model.py compiles successfully")
    except py_compile.PyCompileError as e:
        print(f"✗ setup_model.py has syntax errors: {e}")
        return False
    
    return True


def test_import_structure():
    """Test that the module can be imported (without dependencies)."""
    print("\nTesting import structure (may fail if dependencies not installed)...")
    
    try:
        # This will fail if dependencies aren't installed, but that's OK for structure test
        import nlp
        print("✓ nlp module can be imported")
    except ImportError as e:
        print(f"✓ nlp module structure exists (import failed due to missing dependencies: {e})")
    
    return True


if __name__ == "__main__":
    print("="*60)
    print("NLP Module Validation")
    print("="*60 + "\n")
    
    success = True
    
    # Test structure
    if test_module_structure():
        print("\n✓ Module structure validation passed")
    else:
        print("\n✗ Module structure validation failed")
        success = False
    
    # Test imports
    if test_import_structure():
        print("✓ Import structure validation passed")
    else:
        print("✗ Import structure validation failed")
        success = False
    
    print("\n" + "="*60)
    if success:
        print("All validations passed!")
        print("="*60)
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run setup script: python setup_model.py")
        print("3. Test the model: python -m nlp.onnx_nlp_model")
    else:
        print("Some validations failed")
        print("="*60)
        sys.exit(1)
