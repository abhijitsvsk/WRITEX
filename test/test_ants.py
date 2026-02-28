import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from src.blast.ants.content_ant import ContentAnt
from src.blast.ants.structure_ant import StructureAnt
from src.blast.blueprint import DocumentNode

class TestAnts(unittest.TestCase):

    @patch('src.blast.ants.content_ant.ReportGenerator')
    def test_content_ant_success(self, MockGenerator):
        # Setup
        mock_gen_instance = MockGenerator.return_value
        mock_gen_instance.generate_section.return_value = "Generated Content"
        
        ant = ContentAnt()
        node = DocumentNode(type="paragraph", text="Introduction")
        context = {
            "api_key": "mock_key", 
            "project_summary": {},
            "user_context": {}
        }

        # Execute
        result = ant.execute(node, context)

        # Verify
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Generated Content")
        mock_gen_instance.generate_section.assert_called_once()

    @patch('src.blast.ants.content_ant.ReportGenerator')
    def test_content_ant_failure_no_key(self, MockGenerator):
        ant = ContentAnt()
        node = DocumentNode(type="paragraph", text="Introduction")
        context = {} # No API Key

        result = ant.execute(node, context)

        self.assertFalse(result.success)
        self.assertIn("Missing API Key", result.error)

    @patch('src.blast.ants.structure_ant.structure_text')
    def test_structure_ant_success(self, mock_structure):
        # Setup
        mock_structure.return_value = '[{"type": "title", "text": "Test Title"}]'
        
        ant = StructureAnt()
        payload = "Some raw text"
        context = {"api_key": "mock_key"}

        # Execute
        result = ant.execute(payload, context)

        # Verify
        self.assertTrue(result.success)
        self.assertIsInstance(result.data, list)
        self.assertEqual(result.data[0]['text'], "Test Title")

if __name__ == '__main__':
    unittest.main()
