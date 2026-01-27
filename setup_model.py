"""
Automatic Setup Script for ONNX Model

This script:
1. Installs necessary dependencies from requirements.txt
2. Downloads the MiniLM pre-trained model via Hugging Face
3. Converts it to ONNX format using transformers.onnx utility
4. Saves the converted ONNX model to the nlp/onnx/ directory
"""

import os
import sys
import subprocess
from pathlib import Path


def install_dependencies():
    """Install required packages from requirements.txt."""
    print("="*60)
    print("Step 1: Installing Dependencies")
    print("="*60)
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"Error: requirements.txt not found at {requirements_file}")
        sys.exit(1)
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✓ Dependencies installed successfully\n")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)


def download_and_convert_model():
    """Download and convert the MiniLM model to ONNX format."""
    print("="*60)
    print("Step 2: Downloading and Converting Model")
    print("="*60)
    
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch
        from pathlib import Path
        
        # Model name
        model_name = "microsoft/MiniLM-L6-H384-uncased"
        
        # Output directory
        base_dir = Path(__file__).parent / "nlp" / "onnx"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = base_dir / "minilm-l6-h384-uncased.onnx"
        
        print(f"Model: {model_name}")
        print(f"Output: {output_path}\n")
        
        # Download tokenizer and model
        print("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        print("Downloading model...")
        model = AutoModel.from_pretrained(model_name)
        model.eval()
        
        # Prepare dummy input for export
        print("Preparing model export...")
        dummy_input = tokenizer(
            "This is a sample sentence.",
            return_tensors="pt",
            padding='max_length',
            max_length=128,
            truncation=True
        )
        
        # Extract input_ids and attention_mask
        input_ids = dummy_input['input_ids']
        attention_mask = dummy_input['attention_mask']
        
        # Export to ONNX
        print("Converting to ONNX format...")
        torch.onnx.export(
            model,
            (input_ids, attention_mask),
            str(output_path),
            input_names=['input_ids', 'attention_mask'],
            output_names=['last_hidden_state'],
            dynamic_axes={
                'input_ids': {0: 'batch_size', 1: 'sequence_length'},
                'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
                'last_hidden_state': {0: 'batch_size', 1: 'sequence_length'}
            },
            opset_version=14,
            do_constant_folding=True
        )
        
        print(f"✓ Model successfully converted and saved to {output_path}\n")
        
    except ImportError as e:
        print(f"Error: Missing required package - {e}")
        print("Please install torch: pip install torch")
        sys.exit(1)
    except Exception as e:
        print(f"Error during model download/conversion: {e}")
        sys.exit(1)


def verify_setup():
    """Verify that the setup was successful."""
    print("="*60)
    print("Step 3: Verifying Setup")
    print("="*60)
    
    try:
        # Check if ONNX model exists
        model_path = Path(__file__).parent / "nlp" / "onnx" / "minilm-l6-h384-uncased.onnx"
        
        if not model_path.exists():
            print(f"✗ Model file not found at {model_path}")
            return False
        
        print(f"✓ ONNX model found at {model_path}")
        
        # Try to load the model using onnxruntime
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(
                str(model_path),
                providers=['CPUExecutionProvider']
            )
            print("✓ ONNX model loads successfully")
            
            # Print input/output info
            print("\nModel Information:")
            print(f"  Inputs: {[inp.name for inp in session.get_inputs()]}")
            print(f"  Outputs: {[out.name for out in session.get_outputs()]}")
            
        except Exception as e:
            print(f"✗ Failed to load ONNX model: {e}")
            return False
        
        print("\n✓ Setup verification successful!")
        return True
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return False


def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("ONNX NLP Model Setup")
    print("="*60 + "\n")
    
    print("This script will:")
    print("  1. Install required dependencies")
    print("  2. Download MiniLM model from Hugging Face")
    print("  3. Convert model to ONNX format")
    print("  4. Verify the setup\n")
    
    try:
        # Step 1: Install dependencies
        install_dependencies()
        
        # Step 2: Download and convert model
        download_and_convert_model()
        
        # Step 3: Verify setup
        if verify_setup():
            print("\n" + "="*60)
            print("Setup Complete!")
            print("="*60)
            print("\nYou can now use the NLP model:")
            print("  python -m nlp.onnx_nlp_model")
            print("\nOr import it in your code:")
            print("  from nlp.onnx_nlp_model import ONNXNLPModel")
        else:
            print("\n✗ Setup verification failed. Please check the errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
