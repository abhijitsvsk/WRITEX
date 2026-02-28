import argparse
import sys
import os
from pathlib import Path

# Ensure project root is in path
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from src.blast.blueprint import Blueprint, DocumentNode
from src.blast.architect import Architect
from src.analysis.project_summary import ProjectSummary
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Trigger:
    """
    Entry point for the Blast Framework.
    Parses arguments and initializes the Architect.
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Blast Framework Trigger")
        self.parser.add_argument(
            "--action", type=str, default="run", help="Action to perform: run, init"
        )
        self.parser.add_argument(
            "--project_dir", type=str, default=".", help="Project directory"
        )
        self.parser.add_argument(
            "--file", type=str, help="Specific file to process", required=False
        )

        # Context Arguments
        self.parser.add_argument("--title", type=str, default="Project Blast")
        self.parser.add_argument(
            "--student_name", type=str, help="Student Name(s) separated by newline"
        )
        self.parser.add_argument("--guide", type=str, default="Guide Name")
        self.parser.add_argument("--hod", type=str, default="HOD Name")
        self.parser.add_argument("--principal", type=str, default="Principal Name")
        self.parser.add_argument("--university", type=str, default="University Name")
        self.parser.add_argument("--department", type=str, default="Department Name")

    def execute(self):
        args = self.parser.parse_args()

        print(f"Blast Trigger Activated: Action={args.action}")

        # Initialize State
        summary = ProjectSummary(project_type="Automated Report")
        blueprint = Blueprint(summary)

        # Load existing memory if available
        if os.path.exists("project_memory.json"):
            print("Loading project memory...")
            blueprint.load()

        # Update context from args (overrides memory)
        context_update = {
            "title": args.title,
            "guide": args.guide,
            "hod": args.hod,
            "principal": args.principal,
            "university": args.university,
            "department": args.department,
        }
        if args.student_name:
            context_update["student_name"] = args.student_name.replace(
                "\\n", "\n"
            )  # Handle escaped newlines

        for k, v in context_update.items():
            blueprint.set_context(k, v)

        if args.file and os.path.exists(args.file):
            print(f"Seeding tasks for file: {args.file}")
            from src.analysis.style_analyzer import StyleAnalyzer

            # 1. Style Analysis Node
            style_node = DocumentNode(
                type="style_analysis",
                text="Analyze Style",
                id="style_task_1",
                status="pending",
                metadata={"file_path": args.file},
            )
            blueprint.document_structure.append(style_node)

            # 2. Structure Analysis Node
            # We need to extract text first to be efficiently passed?
            # Or let Architect/Ant handle extraction?
            # My current Architect implementation expects node.text to be the PAYLOAD for StructureAnt
            # So let's extract here.

            print("Extracting text for structure analysis...")
            # Use StyleAnalyzer purely for extraction utility
            analyzer = StyleAnalyzer()
            text = analyzer.extract_text(args.file, args.file)

            structure_node = DocumentNode(
                type="structure_analysis",
                text=text,  # Passing raw text as payload
                id="struct_task_1",
                status="pending",
            )
            blueprint.document_structure.append(structure_node)

            blueprint.save()

        architect = Architect(blueprint)

        if args.action == "init":
            print("Project Initialized.")
            blueprint.save()

        elif args.action == "run":
            architect.run()
            architect.finalize("d:/writex/blast_output.docx")

        else:
            print(f"Unknown action: {args.action}")


if __name__ == "__main__":
    trigger = Trigger()
    trigger.execute()
