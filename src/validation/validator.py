import re
from typing import List, Dict


class DocumentValidator:
    """
    Self-healing structural validation engine.
    Runs mathematically verified checks against the abstract structure array
    before delegating to the formatting layer.
    """

    def __init__(self):
        self.validation_run_count = 0
        self.max_heals = 3

    def validate_and_heal(self, structure: List[Dict]) -> List[Dict]:
        """
        Runs the full verification suite. If errors are found, attempts to heal the structure natively.
        Returns the mathematically verified structure list.
        """
        healed_structure = structure.copy()

        while self.validation_run_count < self.max_heals:
            self.validation_run_count += 1
            is_clean, errors, healed_structure = self._run_pass(healed_structure)

            if is_clean:
                return healed_structure

        raise ValueError(
            f"Document Structure critically irrecoverable after {self.max_heals} auto-heal attempts. Remaining errors: {errors}"
        )

    def _run_pass(self, structure: List[Dict]) -> tuple[bool, List[str], List[Dict]]:
        errors = []
        is_clean = True

        # Pass 1: Count Figures and structural elements
        body_figures = 0
        lof_found = False
        has_certificate = False
        has_acknowledgement = False
        has_reference_placeholder = False

        for idx, item in enumerate(structure):
            itype = item.get("type", "")
            text = item.get("text", "")

            # Track LOF type
            if itype == "lof" or "list of figures" in text.lower():
                lof_found = True

            # Track certificate/acknowledgement headers
            if itype == "section_header":
                if "certificate" in text.lower():
                    has_certificate = True
                elif (
                    "acknowledgement" in text.lower()
                    or "acknowledgment" in text.lower()
                ):
                    has_acknowledgement = True

            # Track Figure declarations in body text
            if itype == "paragraph":
                if (
                    re.search(
                        r"^\*?\[?(?:Fig|Figure)\s*[\d\.]+\]?\*?[:\-]?\s*(.*)",
                        text,
                        re.IGNORECASE,
                    )
                    or text.startswith("[Figure")
                    or text.startswith("Figure")
                ):
                    body_figures += 1
                # Check for reference placeholders
                if (
                    "add your references here" in text.lower()
                    or text.strip() == "[1] Add your references here."
                ):
                    has_reference_placeholder = True

        # Verification 1: Figure Parity (Heal missing LOF)
        if body_figures > 0 and not lof_found:
            is_clean = False
            errors.append("Validation Failure: Figures detected, but LOF missing.")
            structure = self._heal_missing_lof(structure)

        # Verification 2: White Space Density (Healing stacked page breaks)
        structure, whitespace_healed = self._heal_whitespace(structure)
        if whitespace_healed:
            is_clean = False
            errors.append(
                "Validation Failure: Poor whitespace density (stacked page breaks or empty paragraphs). Healed."
            )

        # Verification 3: Remove Hallucinated Errors (Healing failed code extractions)
        structure, extraction_healed = self._heal_failed_extraction(structure)
        if extraction_healed:
            is_clean = False
            errors.append(
                "Validation Failure: Failed code extraction logic detected in text. Healed."
            )

        # Verification 4: Remove Text Artifacts (Hanging brackets, fake citations)
        structure, artifacts_healed = self._heal_text_artifacts(structure)
        if artifacts_healed:
            is_clean = False
            errors.append(
                "Validation Failure: Textual formatting artifacts detected (brackets, fake citations). Healed."
            )

        # Verification 5: Certificate/Acknowledgement presence
        if not has_certificate:
            errors.append(
                "Validation Warning: No Certificate section found in structure."
            )
        if not has_acknowledgement:
            errors.append(
                "Validation Warning: No Acknowledgement section found in structure."
            )

        # Verification 6: Reference placeholder detection
        if has_reference_placeholder:
            is_clean = False
            errors.append(
                "Validation Failure: Reference section still contains placeholder text. Healed."
            )
            structure = [
                item
                for item in structure
                if not (
                    item.get("type") == "paragraph"
                    and (
                        "add your references here" in item.get("text", "").lower()
                        or "replace this placeholder" in item.get("text", "").lower()
                    )
                )
            ]

        return is_clean, errors, structure

    def _heal_missing_lof(self, structure: List[Dict]) -> List[Dict]:
        """Injects the LOF into the Front Matter dynamically using the native Word field type."""
        new_structure = []

        for item in structure:
            if item.get("type") == "toc":
                # Inject LOF right before the Table of Contents
                new_structure.append(
                    {"type": "section_header", "text": "LIST OF FIGURES"}
                )
                new_structure.append({"type": "lof", "text": "LIST OF FIGURES"})

            new_structure.append(item)

        return new_structure

    def _heal_whitespace(self, structure: List[Dict]) -> tuple[List[Dict], bool]:
        """Mathematically strips consecutive page breaks, empty abstract paragraphs, and redundant breaks before headers."""
        healed: List[Dict] = []
        was_healed = False

        for item in structure:
            itype = item.get("type")

            # 1. Strip useless paragraphs
            if itype == "paragraph" and not str(item.get("text", "")).strip():
                was_healed = True
                continue

            # 2. If the current item forces a native DOCX page break (e.g. Chapter 1, Heading)
            if itype in ["section_header", "chapter", "toc", "lof"]:
                # If the immediate preceding item in the healed array was a manual page_break, pop it out!
                if healed and healed[-1].get("type") == "page_break":
                    healed.pop()
                    was_healed = True

            # 3. Strip stacked manual page breaks
            if (
                itype == "page_break"
                and healed
                and healed[-1].get("type") == "page_break"
            ):
                was_healed = True
                continue

            healed.append(item)

        return healed, was_healed

    def _heal_failed_extraction(self, structure: List[Dict]) -> tuple[List[Dict], bool]:
        """Strips out paragraphs where the generator failed to locate native code."""
        healed: List[Dict] = []
        was_healed = False

        idx = 0
        while idx < len(structure):
            item = structure[idx]
            if item.get("type") == "paragraph" and "[Error: Code for" in item.get(
                "text", ""
            ):
                was_healed = True
                # We also want to strip the preceding paragraph which inherently says "The implementation is shown below:"
                if (
                    healed
                    and healed[-1].get("type") == "paragraph"
                    and "implementation of" in healed[-1].get("text", "")
                ):
                    healed.pop()
            else:
                healed.append(item)
            idx += 1

        return healed, was_healed

    def _heal_text_artifacts(self, structure: List[Dict]) -> tuple[List[Dict], bool]:
        """Scans every text node and mathematically scrubs hanging brackets and LLM hallucination markers."""
        healed = []
        was_healed = False

        for item in structure:
            if item.get("type") in ["paragraph", "subheading", "chapter", "title"]:
                original_text = item.get("text", "")
                if not isinstance(original_text, str):
                    healed.append(item)
                    continue

                # 1. Remove hanging single brackets [ or ] from the ends of lines
                cleaned = re.sub(r"^\s*\]\s*$", "", original_text, flags=re.MULTILINE)
                cleaned = re.sub(r"^\s*\[\s*$", "", cleaned, flags=re.MULTILINE)

                # 2. Eradicate fake citations e.g., (Smith, 2020) or [1] if generated arbitrarily outside references
                # We aggressively strip [X] patterns heavily used as LLM placeholders
                if (
                    item.get("type") == "paragraph"
                    and "list of figures" not in original_text.lower()
                ):
                    cleaned = re.sub(r"\[\s*\d+\s*\]", "", cleaned)

                if cleaned != original_text:
                    was_healed = True
                    item["text"] = cleaned

            healed.append(item)

        return healed, was_healed
