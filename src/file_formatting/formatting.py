from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement, ns
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE





def create_element(name):
    return OxmlElement(name)

def create_attribute(element, name, value):
    element.set(qn(name), value)

def add_field_code(paragraph, field_code):
    """Insert a Word field code using separate runs per OOXML spec."""
    # Run 1: Field Begin
    run1 = paragraph.add_run()
    fldChar1 = create_element('w:fldChar')
    create_attribute(fldChar1, 'w:fldCharType', 'begin')
    run1._r.append(fldChar1)

    # Run 2: Field Instruction
    run2 = paragraph.add_run()
    instrText = create_element('w:instrText')
    create_attribute(instrText, 'xml:space', 'preserve')
    instrText.text = field_code
    run2._r.append(instrText)

    # Run 3: Separate marker
    run3 = paragraph.add_run()
    fldChar2 = create_element('w:fldChar')
    create_attribute(fldChar2, 'w:fldCharType', 'separate')
    run3._r.append(fldChar2)

    # Run 4: Placeholder display text (replaced by Word on update)
    run4 = paragraph.add_run('Right-click to update field.')
    run4.font.name = 'Times New Roman'
    run4.font.size = Pt(12)

    # Run 5: Field End
    run5 = paragraph.add_run()
    fldChar3 = create_element('w:fldChar')
    create_attribute(fldChar3, 'w:fldCharType', 'end')
    run5._r.append(fldChar3)


def add_table_of_contents(doc, heading_paragraph, structure=None):
    """
    Builds a native MS Word Table of Contents using Field Codes.
    Word will dynamically generate this TOC when the user opens the document.
    """
    if not structure:
        return

    p = doc.add_paragraph()
    # Field code for TOC: Levels 1-3, Hyperlinks, Outline levels
    add_field_code(p, r' TOC \o "1-3" \h \z \u ')


def add_list_of_figures(doc, heading_paragraph, structure=None):
    """
    Builds a native MS Word List of Figures using Field Codes.
    Word will dynamically generate this LOF when the user opens the document.
    """
    if not structure:
        return

    p = doc.add_paragraph()
    # Field code for LOF: Target Captions named "Figure"
    add_field_code(p, r' TOC \h \z \c "Figure" ')


def generate_report(
    structure,
    output_path,
    style_name="Standard",
    custom_font=None,
    custom_size=None,
    custom_spacing=None,
):
    doc = Document()

    # --- Standard Style Config ---
    font_name = "Times New Roman"
    font_size = 12
    line_spacing = 1.5

    # --- Margin Setup (Enforcing Strict A4 Geometry) ---
    from docx.shared import Mm
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1.5)  # Academic standard
    section.right_margin = Inches(1)

    # --- Style Bootstrapping (Root Cause 2 Fix) ---
    # Ensure critical styles exist so the TOC/LOF fields don't silently fail.
    required_styles = ["Heading 1", "Heading 2", "Heading 3", "Caption"]
    for s_name in required_styles:
        try:
            _ = doc.styles[s_name]
        except KeyError:
            doc.styles.add_style(s_name, WD_STYLE_TYPE.PARAGRAPH)

    # --- Hierarchy Counters ---
    # These strictly track where we are in the document
    counters = {"chapter": 0, "sub": 0, "subsub": 0, "figure": 0}

    # --- PRE-PROCESS: Extract inline figures from paragraphs ---
    import re as _re

    _clean_structure = []
    for _item in structure:
        if _item.get("type", "") == "paragraph" and _item.get("text", ""):
            _txt = _item.get("text")
            # Pull '[Figure X: Title]' out into its own paragraph block safely
            _parts = _re.split(
                r"(\[(?:Fig|Figure)\s*[\d\.]*[:\-]?\s*.*?\])",
                _txt,
                flags=_re.IGNORECASE,
            )
            for _p in _parts:
                _p = _p.strip()
                if _p:
                    _clean_structure.append({"type": "paragraph", "text": _p})
        else:
            _clean_structure.append(_item)
    structure = _clean_structure

    seen_captions = set()  # Fix 4: Semantic Dedup captions
    skip_indices = set()
    
    # Enable Dual-Section Pagination (Front-Matter Roman Initialization)
    if doc.sections:
        sec1 = doc.sections[0]
        pgNumType = OxmlElement('w:pgNumType')
        pgNumType.set(ns.qn('w:fmt'), 'lowerRoman')
        sec1._sectPr.append(pgNumType)

    for idx, item in enumerate(structure):
        if idx in skip_indices:
            continue
        itype = item.get("type")
        text = item.get("text", "")

        # 0a. TOC (Table of Contents)
        if itype == "toc":
            doc.add_page_break()
            p = doc.add_paragraph()
            # Use Normal style (NOT Heading 1) to prevent TOC heading from indexing itself
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run("Table of Contents")
            run.font.name = font_name
            run.font.size = Pt(16)
            run.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.paragraph_format.space_after = Pt(24)
            p.paragraph_format.space_before = Pt(0)
            add_table_of_contents(doc, p, structure)
            continue

        # 0b. LOF (List of Figures)
        elif itype == "lof":
            doc.add_page_break()
            p = doc.add_paragraph()
            # Use Normal style (NOT Heading 1) to prevent LOF heading from indexing itself
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run("List of Figures")
            run.font.name = font_name
            run.font.size = Pt(16)
            run.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.paragraph_format.space_after = Pt(24)
            p.paragraph_format.space_before = Pt(0)
            add_list_of_figures(doc, p, structure)
            continue

        # 1. CHAPTER (Level 1)
        elif itype == "chapter":
            counters["chapter"] += 1
            counters["sub"] = 0
            counters["subsub"] = 0
            counters["figure"] = 0

            # First Chapter gets a new section with Arabic numbering restart
            if counters["chapter"] == 1:
                # Add section break instead of page break
                new_section = doc.add_section(WD_SECTION.NEW_PAGE)
                
                # Unlink footer from front matter
                new_section.footer.is_linked_to_previous = False
                
                # Restart numbering at 1, Arabic format
                pgNumType = OxmlElement('w:pgNumType')
                pgNumType.set(ns.qn('w:fmt'), 'decimal')
                pgNumType.set(ns.qn('w:start'), '1')
                new_section._sectPr.append(pgNumType)
            else:
                doc.add_page_break()

            p = doc.add_paragraph()
            p.style = doc.styles["Heading 1"]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

            # Use Title Case for Chapter Titles instead of ALL CAPS
            run = p.add_run(f"Chapter {counters['chapter']}\n{text.title()}")
            run.bold = True
            run.font.name = font_name
            run.font.size = Pt(16)
            run.font.color.rgb = RGBColor(0, 0, 0)

            p.paragraph_format.space_after = Pt(24)

        # 2. SUBHEADING (Level 2) - 1.1
        elif itype == "subheading":
            counters["sub"] += 1
            counters["subsub"] = 0

            prefix = f"{counters['chapter']}.{counters['sub']}"
            p = doc.add_paragraph()
            p.style = doc.styles["Heading 2"]

            run = p.add_run(f"{prefix} {text.title()}")
            run.bold = True
            run.font.name = font_name
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(0, 0, 0)

            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(12)

        # 3. SUBSUBHEADING (Level 3) - 1.1.1
        elif itype == "subsubheading":
            counters["subsub"] += 1

            prefix = f"{counters['chapter']}.{counters['sub']}.{counters['subsub']}"
            p = doc.add_paragraph()
            p.style = doc.styles["Heading 3"]

            run = p.add_run(f"{prefix} {text.title()}")
            run.bold = True
            run.font.name = font_name
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0, 0, 0)

            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(8)

        # 4. TITLE / SPLASH
        elif itype == "title":
            p = doc.add_paragraph("Course Project Report On")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(48)
            p.runs[0].font.name = font_name
            p.runs[0].font.size = Pt(14)
            p.paragraph_format.space_after = Pt(24)

            p2 = doc.add_paragraph(text)
            p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p2.runs[0]
            run.font.size = Pt(22)
            run.bold = True
            run.font.name = font_name
            p2.paragraph_format.space_after = Pt(24)
            p2.paragraph_format.line_spacing = 1.0

        # 4a. TITLE PAGE BODY (Centered, Single Spaced)
        elif itype == "title_page_body":
            p = doc.add_paragraph(text)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing = 1.15
            for run in p.runs:
                run.font.name = font_name
                run.font.size = Pt(14)
                if "Bachelor of Technology" in run.text or "Submitted by" in run.text:
                    run.bold = True
            p.paragraph_format.space_after = Pt(24)

        # 4b. SECTION HEADER (Unnumbered, New Page) - Abstract, References
        elif itype == "section_header":
            # Skip building headers for LOF/TOC here as they are explicitly built in the functions above.
            if text.upper() in ["LIST OF FIGURES", "TABLE OF CONTENTS", "CONTENTS"]:
                continue

            doc.add_page_break()
            p = doc.add_paragraph()
            p.style = doc.styles["Heading 1"]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(text.title())  # Changed from UPPER to title case
            run.bold = True
            run.font.name = font_name
            run.font.size = Pt(16)
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.paragraph_format.space_after = Pt(24)
            p.paragraph_format.space_before = Pt(0)

        # 4c. INSTITUTIONAL HEADER (Unnumbered, New Page, Left Aligned, Title Case)
        elif itype == "institutional_header":
            doc.add_page_break()
            p = doc.add_paragraph()
            p.style = doc.styles["Heading 1"]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(text.title())
            run.bold = True
            run.font.name = font_name
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.paragraph_format.space_after = Pt(24)

        # 5. SIGNATURE BLOCK
        elif itype == "signature_block":
            guide = item.get("guide", "Guide")
            guide_desig = item.get("guide_designation", "Assistant Professor")
            hod = item.get("hod", "HOD")
            hod_desig = item.get("hod_designation", "Professor & HoD")
            department = item.get("department", "")

            table = doc.add_table(rows=1, cols=2)
            table.autofit = True
            # Add spacing before signature block
            for cell in table.columns[0].cells:
                for cp in cell.paragraphs:
                    cp.paragraph_format.space_before = Pt(36)

            # Left Cell: Guide
            cell_l = table.cell(0, 0)
            p = cell_l.paragraphs[0]
            guide_text = f"\n\n___________________\n{guide}\n{guide_desig}"
            if department:
                guide_text += f"\nDepartment of {department}"
            run = p.add_run(guide_text)
            run.bold = True
            run.font.name = font_name
            run.font.size = Pt(11)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

            # Right Cell: HOD
            cell_r = table.cell(0, 1)
            p = cell_r.paragraphs[0]
            hod_text = f"\n\n___________________\n{hod}\n{hod_desig}"
            if department:
                hod_text += f"\nDepartment of {department}"
            run = p.add_run(hod_text)
            run.bold = True
            run.font.name = font_name
            run.font.size = Pt(11)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # 6. PAGE BREAK
        elif itype == "page_break":
            doc.add_page_break()

        # 8. CODE SNIPPET (NATIVE)
        elif itype == "code_block":
            # Add "Code:" label first
            label_p = doc.add_paragraph()
            label_run = label_p.add_run("Code:")
            label_run.bold = True
            label_run.font.name = font_name
            label_run.font.size = Pt(font_size)
            label_p.paragraph_format.space_before = Pt(12)
            label_p.paragraph_format.space_after = Pt(4)

            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

            # Simple gray "code block" background via shading xml element
            shading_elm = OxmlElement("w:shd")
            shading_elm.set(ns.qn("w:val"), "clear")
            shading_elm.set(ns.qn("w:color"), "auto")
            shading_elm.set(ns.qn("w:fill"), "F0F0F0")  # Light gray
            p.paragraph_format.element.get_or_add_pPr().append(shading_elm)

            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(12)
            p.paragraph_format.line_spacing = 1.0  # Code is single-spaced
            p.paragraph_format.left_indent = Inches(0.25)

            run = p.add_run(text)
            run.font.name = "Courier New"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0, 0, 0)

            # Note: "Explanation:" label is intentionally omitted to prevent
            # empty heading artifacts when no further explanation follows the code.
            pass

        # 8b. ALONE IMAGE
        elif itype == "image":
            import io

            try:
                image_stream = io.BytesIO(item["content"])
                doc.add_picture(image_stream, width=Inches(6.0))
                last_paragraph = doc.paragraphs[-1]
                last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            except Exception as e:
                print(f"Error embedding standalone diagram: {e}")

        # 9. FIGURE (NATIVE AST OBJECT)
        elif itype == "figure":
            counters["figure"] += 1
            caption_clean = (item.get("caption", "") or item.get("text", "")).strip()
            
            # --- IMAGE PLACEHOLDER OR ACTUAL IMAGE ---
            next_item = structure[idx + 1] if idx + 1 < len(structure) else None
            # If the architecture ever feeds in an image buffer, inject it natively
            if next_item and next_item.get("type") == "image":
                import io
                try:
                    image_stream = io.BytesIO(next_item["content"])
                    doc.add_picture(image_stream, width=Inches(6.0))
                    last_paragraph = doc.paragraphs[-1]
                    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                except Exception as e:
                    print(f"Error embedding diagram: {e}")
                skip_indices.add(idx + 1)
            else:
                placeholder_p = doc.add_paragraph()
                placeholder_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                placeholder_p.paragraph_format.space_before = Pt(12)
                placeholder_p.paragraph_format.space_after = Pt(6)

                box_run = placeholder_p.add_run("\n[ Image Placeholder ]\n")
                box_run.font.name = "Consolas"
                box_run.font.size = Pt(10)

                shading_elm = OxmlElement("w:shd")
                shading_elm.set(ns.qn("w:val"), "clear")
                shading_elm.set(ns.qn("w:color"), "auto")
                shading_elm.set(ns.qn("w:fill"), "EAEAEA")
                placeholder_p.paragraph_format.element.get_or_add_pPr().append(
                    shading_elm
                )

            # --- CAPTION ---
            p = doc.add_paragraph()
            p.style = doc.styles["Caption"]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(12)
            p.paragraph_format.line_spacing = 1.0  # Single spaced for figures

            run = p.add_run("Figure " + str(counters['chapter']) + ".")
            run.font.name = font_name
            run.font.size = Pt(11)

            # Insert SEQ field code for the figure number
            add_field_code(p, r' SEQ Figure \* ARABIC ')

            run = p.add_run(f" {caption_clean}")
            run.font.name = font_name
            run.font.size = Pt(11)

        # 10. PARAGRAPH / BODY / PLACEHOLDERS
        else:
            text = text.strip()
            if not text:
                continue  # Skip completely empty paragraphs

            import re

            # Code Extraction Tag — skip rendering these, they should have been
            # processed by the compiler. If any leak through, silently drop them.
            code_match = re.search(r"\[Extract Code:\s*(.*?)\]", text, re.IGNORECASE)
            if code_match:
                continue  # Do NOT render extraction tags as visible text

            # The architecture now structurally guarantees that all figures are emitted natively as `{"type": "figure"}`.
            # Hallucinated `[Figure]` text inside generic paragraphs is stripped by the Compiler's parser layer.
            # Therefore, we simply print text natively without string-based masking.
            p = doc.add_paragraph(text)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(12)
            p.paragraph_format.line_spacing = line_spacing

            for run in p.runs:
                run.font.name = font_name
                run.font.size = Pt(font_size)

    # --- POST-PROCESSING ---

    # ZERO-TOLERANCE WHITESPACE PURGE
    # Snapshot the list FIRST to avoid modifying during iteration (critical safety fix)
    paragraphs_snapshot = list(doc.paragraphs)
    for p in paragraphs_snapshot:
        if not p.text.strip():
            # Preserve paragraphs containing Word field codes (TOC, LOF, SEQ, PAGE)
            has_field = bool(p._element.xpath('.//*[local-name()="fldChar"]'))
            if has_field:
                continue

            # Preserve page breaks
            has_break = bool(p._element.xpath('.//*[local-name()="br"]'))
            if has_break:
                continue

            # Preserve embedded images/drawings
            has_drawing = bool(p._element.xpath('.//*[local-name()="drawing"]'))
            if has_drawing:
                continue

            # Preserve paragraphs with shading (code blocks, placeholders)
            has_shading = bool(p._element.xpath('.//*[local-name()="shd"]'))
            if has_shading:
                continue

            # Preserve section break paragraphs
            has_sectPr = bool(p._element.xpath('.//*[local-name()="sectPr"]'))
            if has_sectPr:
                continue

            # Preserve SDT-adjacent paragraphs
            has_sdt_sibling = (
                (p._element.getnext() is not None and p._element.getnext().tag.endswith('}sdt'))
                or (p._element.getprevious() is not None and p._element.getprevious().tag.endswith('}sdt'))
            )
            if has_sdt_sibling:
                continue

            # Safe to delete — truly empty paragraph with no structural role
            parent = p._element.getparent()
            if parent is not None:
                parent.remove(p._element)

    _add_page_numbers(doc, font_name)

    # --- Structural Validation (Root Cause 3 Fix) ---
    _validate_document_structure(doc)

    # Force Word to auto-calculate the native field codes upon opening
    try:
        settings = doc.settings.element
        update_fields = OxmlElement('w:updateFields')
        update_fields.set(qn('w:val'), 'true')
        settings.append(update_fields)
    except Exception as e:
        print(f"[WARNING] Could not append w:updateFields element: {e}")

    # Generate final single-pass DOCX
    if hasattr(output_path, "write"):
        doc.save(output_path)
    else:
        doc.save(output_path)


def _validate_document_structure(doc):
    """Mathematical AST validation to guarantee headings, captions, and SEQ fields exist before saving."""
    heading_count = 0
    caption_count = 0

    for p in doc.paragraphs:
        if p.style.name.startswith("Heading"):
            heading_count += 1
        elif p.style.name == "Caption":
            caption_count += 1

    seq_count = len(doc.element.xpath('//w:instrText[contains(text(), "SEQ Figure")]'))

    print(
        f"[STRUCTURAL AUDIT] Verified {heading_count} Headings and {caption_count} Captions mapped correctly via AST. Found {seq_count} SEQ Figure instructions."
    )
    if heading_count == 0:
        print(
            "[WARNING] Zero headings detected in the Document Object. The TOC will render empty."
        )
    if caption_count == 0:
        print(
            "[WARNING] Zero Captions detected in the Document Object. The LOF will render empty."
        )
    if caption_count > 0 and seq_count == 0:
        print(
            "[WARNING] Zero SEQ Figure fields detected! The LOF field mathematically cannot populate."
        )


def _add_page_numbers(doc, font_name):
    """Add professional page numbers to all document sections."""
    for i, section in enumerate(doc.sections):
        footer = section.footer
        # First section gets Roman numerals, subsequent sections get Arabic numerals.
        # But both need the PAGE field injected.
        p = footer.paragraphs[0]
        
        # Guard against double-injecting the PAGE field if it already exists
        if p.text.strip():
            p.clear()
            
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Professional format: "— PAGE —"
        # Add left dash
        run_left = p.add_run("\u2014 ")
        run_left.font.name = font_name
        run_left.font.size = Pt(10)
        
        # Add PAGE field
        run = p.add_run()
        run.font.name = font_name
        run.font.size = Pt(10)

        fldChar1 = OxmlElement("w:fldChar")
        fldChar1.set(ns.qn("w:fldCharType"), "begin")

        instrText = OxmlElement("w:instrText")
        instrText.set(ns.qn("xml:space"), "preserve")
        instrText.text = "PAGE"

        fldChar2 = OxmlElement("w:fldChar")
        fldChar2.set(ns.qn("w:fldCharType"), "separate")

        # Cached display text for Word versions that don't auto-calc
        cached_page = OxmlElement("w:t")
        cached_page.text = "1"

        fldChar3 = OxmlElement("w:fldChar")
        fldChar3.set(ns.qn("w:fldCharType"), "end")

        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)
        run._r.append(cached_page)
        run._r.append(fldChar3)
        
        # Add right dash
        run_right = p.add_run(" \u2014")
        run_right.font.name = font_name
        run_right.font.size = Pt(10)

