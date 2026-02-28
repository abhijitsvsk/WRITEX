
import os
import sys
import time

# Add project root to path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_path)

try:
    print("Attempting to import generate_with_retry...")
    from src.ai.utils import generate_with_retry
    print("Import successful.")

    class MockModel:
        def __init__(self):
            self.attempts = 0
            
        def generate_content(self, prompt, generation_config=None):
            self.attempts += 1
            print(f"MockModel call #{self.attempts}")
            if self.attempts < 3:
                raise Exception("429 Resource exhausted")
            return type('obj', (object,), {'text': "Success after retry"})

    print("Testing retry logic...")
    model = MockModel()
    # Use small backoff for test speed
    result = generate_with_retry(model, "test prompt", max_retries=5, base_delay=0.1)
    
    if result == "Success after retry":
        print(f"SUCCESS: Result obtained after {model.attempts} attempts.")
    else:
        print(f"FAILURE: Unexpected result: {result}")

except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
