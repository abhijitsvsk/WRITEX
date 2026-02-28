import time
from typing import Optional, List
from .blueprint import Blueprint, DocumentNode

# We will import Ants later to avoid circular imports if any,
# or we can import them here if they are independent.


class Architect:
    """
    The Architect orchestrates the execution flow.
    It selects the right Ant for the job and handles retry logic.
    """

    def __init__(self, blueprint: Blueprint):
        self.blueprint = blueprint
        self.max_retries = 3

    def plan(self):
        """Analyze the blueprint and determine next steps."""
        # For this phase, the plan is simple: process all pending nodes.
        pass

    def run(self):
        """Main execution loop."""
        print("Architect: Starting execution loop...")

        while True:
            remote_work = False
            pending_nodes = self.blueprint.get_pending_nodes()

            if not pending_nodes:
                break

            for node in pending_nodes:
                print(f"Architect: Processing node {node.id} ({node.type})")

                # Special handling for expansion BEFORE execution? No, execute first.
                success = self._process_node_with_retry(node)

                if success:
                    self.blueprint.update_node(node.id, status="completed")
                    remote_work = True

                    # --- Post-Processing / Expansion ---
                    if node.type == "structure_analysis" and node.content:
                        # The content is the JSON structure strings or list dicts
                        # We need to expand this into new nodes
                        self._expand_structure(node.content)

                else:
                    self.blueprint.update_node(node.id, status="failed")
                    print(f"Architect: Node {node.id} failed after retries.")

            if not remote_work:
                # No work was done in this pass, and pending nodes exist (failed ones?)
                # Prevent infinite loop
                break

        print("Architect: Execution finished.")
        self.blueprint.save()

    def _expand_structure(self, structure_data):
        """Expands structure JSON into blueprint nodes."""
        import json

        try:
            if isinstance(structure_data, str):
                data = json.loads(structure_data)
            else:
                data = structure_data

            print(f"Architect: Expanding {len(data)} nodes from structure...")

            for item in data:
                # Create new nodes from the structure
                # We map 'type' and 'text'
                # We also need to map them to ants.
                # 'heading' -> 'section_content' (to trigger ContentAnt)
                # 'paragraph' -> 'section_content'

                new_type = item.get("type")
                if new_type in ["heading", "subheading", "chapter", "paragraph"]:
                    # For now, let's treat them all as content generation targets
                    # But 'paragraph' from `structurer` is usually existing text.
                    # If we are generating a report, we often start with outlines.
                    # Let's assume the structure returned IS the outline we want to generate content for.
                    pass

                # In this specific app flow, 'structurer' analyzes EXISTING text.
                # If we want to GENERATE a report, we usually start with an outline.
                # But here we are demonstrating "Blast" on an existing doc or creating one?

                # If the user wants to "Run it" based on previous context,
                # they likely want to run the Report Generation flow.
                # But wait, `StructureAnt` wraps `structurer.py` which detects structure from RAW TEXT.

                # Let's assume we are re-generating or processing.
                # For the demo, let's just add them.

                node = DocumentNode(
                    type=item.get("type", "unknown"),
                    text=item.get("text", ""),
                    id=f"gen_{int(time.time()*1000)}_{item.get('text')[:5]}",
                    status=(
                        "pending"
                        if item.get("type") in ["heading", "subheading", "chapter"]
                        else "completed"
                    ),  # Only generate content for headings?
                )
                self.blueprint.document_structure.append(node)

        except Exception as e:
            print(f"Architect: Expansion failed: {e}")

    def _process_node_with_retry(self, node: DocumentNode) -> bool:
        """Execute the appropriate Ant with retry logic."""
        attempt = 0
        while attempt < self.max_retries:
            try:
                # Select Ant based on Node Type
                ant = self._select_ant(node)
                if not ant:
                    # Some nodes like 'title' might not need processing content generation
                    # or they are already processed.
                    if node.type in ["title", "reference", "code"]:
                        # Passive nodes
                        return True
                    if node.type in ["paragraph"]:
                        # If it's just a paragraph node from structure, maybe we don't need to do anything
                        return True

                    print(f"Architect: No Ant found for node type {node.type}")
                    return False

                # Prepare payload
                # Some Ants expect dict, some string.
                # StructureAnt expects text.
                # StyleAnt expects file path (in text or metadata).
                payload = node.text
                if node.type == "style_analysis":
                    payload = node.metadata  # Pass metadata which has file_path

                result = ant.execute(payload, self.blueprint.get_context())

                if result.success:
                    # For structure analysis, data is the content
                    content = result.content
                    if result.data is not None:
                        content = result.data  # Store structured data

                    self.blueprint.update_node(node.id, content=content)

                    # Update context if needed (e.g. style guide)
                    if node.type == "style_analysis" and result.data:
                        self.blueprint.set_context(
                            "style_guide", result.data.get("style_guide")
                        )
                        self.blueprint.set_context(
                            "visual_style", result.data.get("visual_style")
                        )

                    return True
                else:
                    error_msg = f"Architect: Ant failed (Attempt {attempt+1}/{self.max_retries}): {result.error}"
                    if result.content:
                        error_msg += f"\n   Raw Content: {result.content[:500]}..."  # Log first 500 chars
                    print(error_msg)
                    attempt += 1
                    time.sleep(1)  # Simple backoff

            except Exception as e:
                print(f"Architect: Critical Error (Attempt {attempt+1}): {e}")
                attempt += 1
                time.sleep(1)

        return False

    def finalize(self, output_path: str = "blast_output.docx"):
        """Compiles the blueprint into a final document."""
        print("Architect: Finalizing document...")

        # 1. Construct structure for FormatAnt
        structure_for_format = []

        # Sort nodes by some order? They are in list order in document_structure
        for node in self.blueprint.document_structure:
            if node.type in ["style_analysis", "structure_analysis"]:
                continue

            # Add the element itself (e.g. the Heading)
            structure_for_format.append({"type": node.type, "text": node.text})

            # If it has generated content, add that as a paragraph following it
            if node.content and isinstance(node.content, str):
                # Check if content is just the text (which happens if Ant didn't run)
                # No, AntResult.content is usually the generated text.
                # Avoid duplicating if content == text (unlikely for Headings)
                if node.content.strip() != node.text.strip():
                    structure_for_format.append(
                        {"type": "paragraph", "text": node.content}
                    )

        # 2. Get Visual Style
        context = self.blueprint.get_context()
        visual_style = context.get("visual_style", {})

        # 3. Call FormatAnt
        from .ants.format_ant import FormatAnt

        formatter = FormatAnt()
        payload = {
            "structure": structure_for_format,
            "output_path": output_path,
            "visual_style": visual_style,
            "style_name": "Standard",  # Could come from context
        }

        result = formatter.execute(payload, context)

        if result.success:
            print(f"Architect: Finalization complete. Output: {output_path}")
            return True
        else:
            print(f"Architect: Finalization failed: {result.error}")
            return False

    def _select_ant(self, node: DocumentNode):
        """Factory method to get the right Ant."""
        # Lazy import to avoid circular dependency issues during init
        from .ants.content_ant import ContentAnt
        from .ants.structure_ant import StructureAnt
        from .ants.style_ant import StyleAnt

        if node.type == "structure_analysis":
            return StructureAnt()
        if node.type == "style_analysis":
            return StyleAnt()
        if node.type in ["heading", "subheading", "chapter", "section_content"]:
            return ContentAnt()
        return None
