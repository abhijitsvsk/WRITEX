
import sys
import unittest
from unittest.mock import MagicMock
import os

# Mock streamlit BEFORE importing app
sys.modules["streamlit"] = MagicMock()
import streamlit as st
# Configure st.tabs to return 3 mocks to avoid unpacking error
st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock()]
st.columns.return_value = [MagicMock(), MagicMock()] 
st.file_uploader.return_value = None # Simulate no file uploaded initially
st.button.return_value = False # Simulate no button clicks unexpectedly # Also columns might need this

# Function to run the verification
def verify_startup():
    print("Verifying app.py startup...")
    try:
        # Import app.py. This will execute top-level code.
        # We need to make sure src is in path or we import from src
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        
        import src.app
        
        print("✅ Import successful.")
        
        # Check if set_page_config was called
        if st.set_page_config.called:
            print("✅ st.set_page_config called.")
        else:
            print("❌ st.set_page_config NOT called.")
            return False
            
        return True
    except ImportError as e:
        print(f"❌ ImportError during startup: {e}")
        return False
    except Exception as e:
        print(f"❌ Exception during startup: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if verify_startup():
        print("App startup verification PASSED.")
        sys.exit(0)
    else:
        print("App startup verification FAILED.")
        sys.exit(1)
