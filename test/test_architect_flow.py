import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from src.blast.architect import Architect, Blueprint, DocumentNode
from src.blast.ants.base_ant import AntResult

class TestArchitectFlow(unittest.TestCase):
    
    def setUp(self):
        self.mock_summary = MagicMock()
        self.blueprint = Blueprint(self.mock_summary)
        self.architect = Architect(self.blueprint)

    @patch('src.blast.architect.Architect._select_ant')
    def test_retry_logic_success_after_failure(self, mock_select_ant):
        # Setup
        node = DocumentNode(type="paragraph", text="Intro", id="node_1")
        self.blueprint.document_structure = [node]
        
        mock_ant = MagicMock()
        # First call fails, second call succeeds
        mock_ant.execute.side_effect = [
            AntResult(success=False, error="Temporary Glitch"),
            AntResult(success=True, content="Recovered Content")
        ]
        
        mock_select_ant.return_value = mock_ant
        
        # Execute
        # We manually call _process_node_with_retry to isolate logic
        success = self.architect._process_node_with_retry(node)
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(node.content, "Recovered Content")
        self.assertEqual(mock_ant.execute.call_count, 2)

    @patch('src.blast.architect.Architect._select_ant')
    def test_retry_logic_failure_exhausted(self, mock_select_ant):
        # Setup
        node = DocumentNode(type="paragraph", text="Intro", id="node_2")
        self.blueprint.document_structure = [node]
        
        mock_ant = MagicMock()
        # All calls fail (default max_retries=3)
        mock_ant.execute.return_value = AntResult(success=False, error="Permanent Failure")
        
        mock_select_ant.return_value = mock_ant
        
        # Execute
        success = self.architect._process_node_with_retry(node)
        
        # Verify
        self.assertFalse(success)
        self.assertEqual(mock_ant.execute.call_count, 3)

if __name__ == '__main__':
    unittest.main()
