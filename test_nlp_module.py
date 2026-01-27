"""
Functional tests for NLP module components.

These tests validate the implementation without requiring the actual ONNX model.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all required modules can be imported."""
    print("Test 1: Module Imports")
    print("-" * 50)
    
    try:
        from nlp import onnx_nlp_model
        print("✓ Successfully imported nlp.onnx_nlp_model")
    except ImportError as e:
        print(f"✗ Failed to import nlp.onnx_nlp_model: {e}")
        return False
    
    try:
        from nlp.onnx_nlp_model import ONNXNLPModel
        print("✓ Successfully imported ONNXNLPModel class")
    except ImportError as e:
        print(f"✗ Failed to import ONNXNLPModel: {e}")
        return False
    
    try:
        import setup_model
        print("✓ Successfully imported setup_model")
    except ImportError as e:
        print(f"✗ Failed to import setup_model: {e}")
        return False
    
    return True


def test_class_structure():
    """Test that the ONNXNLPModel class has the required methods."""
    print("\nTest 2: Class Structure")
    print("-" * 50)
    
    try:
        from nlp.onnx_nlp_model import ONNXNLPModel
        
        required_methods = [
            '__init__',
            '_load_model',
            '_load_tokenizer',
            'tokenize',
            'predict',
            'batch_predict',
            'get_similarity'
        ]
        
        for method in required_methods:
            if hasattr(ONNXNLPModel, method):
                print(f"✓ Method '{method}' exists")
            else:
                print(f"✗ Method '{method}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking class structure: {e}")
        return False


def test_setup_module_structure():
    """Test that setup_model has required functions."""
    print("\nTest 3: Setup Module Structure")
    print("-" * 50)
    
    try:
        import setup_model
        
        required_functions = [
            'install_dependencies',
            'download_and_convert_model',
            'verify_setup',
            'main'
        ]
        
        for func in required_functions:
            if hasattr(setup_model, func):
                print(f"✓ Function '{func}' exists")
            else:
                print(f"✗ Function '{func}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking setup_model structure: {e}")
        return False


def test_requirements_file():
    """Test that requirements.txt contains all necessary packages."""
    print("\nTest 4: Requirements File")
    print("-" * 50)
    
    try:
        req_file = Path(__file__).parent / "requirements.txt"
        
        if not req_file.exists():
            print("✗ requirements.txt not found")
            return False
        
        with open(req_file) as f:
            requirements = f.read()
        
        required_packages = [
            'onnxruntime',
            'transformers',
            'numpy',
            'torch',
            'aiohttp'
        ]
        
        for package in required_packages:
            if package in requirements:
                print(f"✓ Package '{package}' found in requirements.txt")
            else:
                print(f"✗ Package '{package}' missing from requirements.txt")
                return False
        
        # Check for version constraints
        if '>=' in requirements:
            print("✓ Version constraints specified")
        else:
            print("⚠ Warning: No version constraints found")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking requirements: {e}")
        return False


def test_directory_structure():
    """Test that the directory structure is correct."""
    print("\nTest 5: Directory Structure")
    print("-" * 50)
    
    try:
        base_dir = Path(__file__).parent
        
        required_paths = [
            base_dir / "nlp",
            base_dir / "nlp" / "__init__.py",
            base_dir / "nlp" / "onnx_nlp_model.py",
            base_dir / "nlp" / "onnx",
            base_dir / "setup_model.py",
            base_dir / "requirements.txt"
        ]
        
        for path in required_paths:
            if path.exists():
                print(f"✓ {path.relative_to(base_dir)} exists")
            else:
                print(f"✗ {path.relative_to(base_dir)} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking directory structure: {e}")
        return False


def test_error_handling():
    """Test error handling in ONNXNLPModel."""
    print("\nTest 6: Error Handling")
    print("-" * 50)
    
    try:
        from nlp.onnx_nlp_model import ONNXNLPModel
        
        # Test that initialization fails gracefully when model doesn't exist
        try:
            model = ONNXNLPModel(model_path="/nonexistent/model.onnx")
            print("✗ Should have raised FileNotFoundError")
            return False
        except FileNotFoundError as e:
            if "setup_model.py" in str(e):
                print("✓ Proper error message when model not found")
            else:
                print(f"⚠ Error raised but message could be improved: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing error handling: {e}")
        return False


def test_readme_documentation():
    """Test that README has been updated with NLP documentation."""
    print("\nTest 7: README Documentation")
    print("-" * 50)
    
    try:
        readme_file = Path(__file__).parent / "README.md"
        
        if not readme_file.exists():
            print("✗ README.md not found")
            return False
        
        with open(readme_file) as f:
            readme_content = f.read()
        
        required_sections = [
            'NLP',
            'setup_model',
            'ONNXNLPModel',
            'requirements.txt'
        ]
        
        for section in required_sections:
            if section in readme_content:
                print(f"✓ README mentions '{section}'")
            else:
                print(f"✗ README missing reference to '{section}'")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking README: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("NLP Module Functional Tests")
    print("="*60 + "\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("Class Structure", test_class_structure),
        ("Setup Module", test_setup_module_structure),
        ("Requirements File", test_requirements_file),
        ("Directory Structure", test_directory_structure),
        ("Error Handling", test_error_handling),
        ("README Documentation", test_readme_documentation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n✓ All tests passed!")
        print("\nThe NLP module is ready for use.")
        print("Run 'python setup_model.py' to download and convert the model.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
