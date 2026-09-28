import io
import zipfile
from pathlib import Path
import pytest

from src.analysis.code_analyzer import CodeAnalyzer
from src.analysis.code_parser import CodeParser

def create_in_memory_zip(file_dict: dict) -> io.BytesIO:
    """Helper to construct an in-memory zip archive."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in file_dict.items():
            zf.writestr(filename, content)
    buf.seek(0)
    return buf

class TestCodeAnalyzer:
    def test_analyze_valid_python_repo(self):
        files = {
            "main.py": "def main():\n    print('Hello world')\n\nif __name__ == '__main__':\n    main()\n",
            "utils/helpers.py": "class CalculationEngine:\n    def add(self, a, b):\n        return a + b\n",
            "tests/test_calc.py": "def test_add():\n    assert 1 + 1 == 2\n",
            "README.md": "# My Test Project\nDocumentation content.",
        }
        zip_buf = create_in_memory_zip(files)
        analyzer = CodeAnalyzer()
        summary = analyzer.analyze_zip(zip_buf)

        assert summary.total_files >= 3
        assert hasattr(summary, "test_files")
        assert any("test_calc.py" in f for f in summary.test_files)
        
        # Check that JSON export works cleanly and contains entry points
        json_data = summary.to_json()
        assert "main.py" in str(json_data)

    def test_zip_bomb_single_file_exceeded(self):
        # 501 KB single file
        large_content = "x = 1\n" * 100000
        zip_buf = create_in_memory_zip({"huge.py": large_content})
        
        analyzer = CodeAnalyzer()
        with pytest.raises(ValueError, match="exceeds 500KB uncompressed limit"):
            analyzer.analyze_zip(zip_buf)

    def test_invalid_bad_zip_file(self):
        corrupted_buf = io.BytesIO(b"Not a real zip archive")
        analyzer = CodeAnalyzer()
        with pytest.raises(ValueError, match="Invalid ZIP file provided"):
            analyzer.analyze_zip(corrupted_buf)

    def test_ignored_directories_filtered_out(self):
        files = {
            "app.py": "print('App running')",
            "node_modules/package/index.js": "console.log('ignored')",
            ".venv/lib/site-packages/lib.py": "print('ignored venv')",
            "build/bundle.js": "var x = 1;",
            ".git/config": "[core] bare = false",
        }
        zip_buf = create_in_memory_zip(files)
        analyzer = CodeAnalyzer()
        summary = analyzer.analyze_zip(zip_buf)

        # Only app.py should be processed
        assert summary.total_files == 1

    def test_secret_and_config_exclusion(self):
        files = {
            "app.py": "print('App running')",
            "settings.py": "SECRET_KEY = 'super_secret'",
            ".env": "DB_PASS=12345",
            "config.py": "DATABASE_URI = 'sqlite://'",
            "package-lock.json": "{}",
        }
        zip_buf = create_in_memory_zip(files)
        analyzer = CodeAnalyzer()
        summary = analyzer.analyze_zip(zip_buf)

        # Only app.py should be processed, secrets/configs filtered
        assert summary.total_files == 1

class TestCodeParser:
    def test_parse_python_ast(self):
        parser = CodeParser()
        code = '''
"""Module docstring describing this file."""
import os
from datetime import datetime

class DataTransformer:
    """Transforms raw dictionaries."""
    def transform(self, data: dict) -> dict:
        return data

def process_pipeline():
    """Runs data pipeline."""
    pass
'''
        result = parser.parse_file(Path("transformer.py"), code)
        assert result is not None
        class_names = [c.name for c in result.classes]
        assert "DataTransformer" in class_names
        func_names = [f.name for f in result.functions]
        assert "process_pipeline" in func_names or any("transform" in f for f in func_names)
        assert "os" in result.imports or "datetime" in result.imports
