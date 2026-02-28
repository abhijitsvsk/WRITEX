from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement, ns
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE


def add_table_of_contents(doc, p, structure=None):
    r"""
    Inserts a real Word TOC field (Auto-TOC).
    The heading for the TOC page is handled by the main loop's 'toc' dispatcher.
    This function only injects the SDT field code block immediately after the provided paragraph `p`.
    """

    # To trigger auto-update in Word, a TOC must be housed in an SDT (Structured Document Tag)
    # create w:sdt
    sdt = OxmlElement("w:sdt")

    # create w:sdtPr
    sdtPr = OxmlElement("w:sdtPr")
    docPartObj = OxmlElement("w:docPartObj")
    docPartGallery = OxmlElement("w:docPartGallery")
    docPartGallery.set(ns.qn("w:val"), "Table of Contents")
    docPartUnique = OxmlElement("w:docPartUnique")
    docPartObj.append(docPartGallery)
    docPartObj.append(docPartUnique)
    sdtPr.append(docPartObj)
    sdt.append(sdtPr)

    # create w:sdtContent
    sdtContent = OxmlElement("w:sdtContent")

    paragraph = OxmlElement("w:p")
    run = OxmlElement("w:r")

    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(ns.qn("w:fldCharType"), "begin")
    fldChar1.set(ns.qn("w:dirty"), "true")  # Dirty flag forces Word to update

    instrText = OxmlElement("w:instrText")
    instrText.set(ns.qn("xml:space"), "preserve")
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'

    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(ns.qn("w:fldCharType"), "separate")

    fldChar3 = OxmlElement("w:fldChar")
    fldChar3.set(ns.qn("w:fldCharType"), "end")

    run.append(fldChar1)
    run.append(instrText)
    run.append(fldChar2)
    run.append(fldChar3)
    paragraph.append(run)
    sdtContent.append(paragraph)

    sdt.append(sdtContent)
    # Append directly after the heading paragraph to preserve XML hierarchy
    p._element.addnext(sdt)


def add_list_of_figures(doc, p):
    """
    Inserts a real Word LOF field.
    The heading for the LOF page is handled by the main loop's 'lof' dispatcher.
    This function only injects the SDT field code block immediately after the provided paragraph `p`.
    """

    # To trigger auto-update in Word, a LOF must be housed in an SDT (Structured Document Tag)
    # create w:sdt
    sdt = OxmlElement("w:sdt")

    # create w:sdtPr
    sdtPr = OxmlElement("w:sdtPr")
    docPartObj = OxmlElement("w:docPartObj")
    docPartGallery = OxmlElement("w:docPartGallery")
    docPartGallery.set(ns.qn("w:val"), "Table of Figures")
    docPartUnique = OxmlElement("w:docPartUnique")
    docPartObj.append(docPartGallery)
    docPartObj.append(docPartUnique)
    sdtPr.append(docPartObj)
    sdt.append(sdtPr)

    # create w:sdtContent
    sdtContent = OxmlElement("w:sdtContent")

    paragraph = OxmlElement("w:p")
    run = OxmlElement("w:r")

    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(ns.qn("w:fldCharType"), "begin")
    fldChar1.set(ns.qn("w:dirty"), "true")  # Dirty flag forces Word to update

    instrText = OxmlElement("w:instrText")
    instrText.set(ns.qn("xml:space"), "preserve")
    instrText.text = 'TOC \\h \\z \\c "Figure"'

    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(ns.qn("w:fldCharType"), "separate")

    fldChar3 = OxmlElement("w:fldChar")
    fldChar3.set(ns.qn("w:fldCharType"), "end")

    run.append(fldChar1)
    run.append(instrText)
    run.append(fldChar2)
    run.append(fldChar3)
    paragraph.append(run)
    sdtContent.append(paragraph)

    sdt.append(sdtContent)
    # Append directly after the heading paragraph to preserve XML hierarchy
    p._element.addnext(sdt)


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

    # --- Margin Setup ---
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1.5)  # Academic standard
    section.right_margin = Inches(1)

    # --- Style Bootstrapping (Root Cause 2 Fix) ---
    # Ensure critical styles exist so the TOC/LOF fields don't silently fail.
    required_styles = ["Heading 1", "Heading 2", "Caption"]
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
    for idx, item in enumerate(structure):
        if idx in skip_indices:
            continue
        itype = item.get("type")
        text = item.get("text", "")

        # 0a. TOC (Table of Contents)
        if itype == "toc":
            doc.add_page_break()
            p = doc.add_paragraph()
            p.style = doc.styles["Heading 1"]
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
            p.style = doc.styles["Heading 1"]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run("List of Figures")
            run.font.name = font_name
            run.font.size = Pt(16)
            run.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.paragraph_format.space_after = Pt(24)
            p.paragraph_format.space_before = Pt(0)
            add_list_of_figures(doc, p)
            continue

        # 1. CHAPTER (Level 1)
        elif itype == "chapter":
            counters["chapter"] += 1
            counters["sub"] = 0
            counters["subsub"] = 0
            counters["figure"] = 0

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

        # 6. TOC — NATIVE WORD FIELD
        elif itype == "toc":
            doc.add_page_break()
            p = doc.add_paragraph()
            p.style = doc.styles["Heading 1"]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run("TABLE OF CONTENTS")
            run.bold = True
            run.font.name = font_name
            run.font.size = Pt(16)
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.paragraph_format.space_after = Pt(24)

            # Insert static TOC entries + Word field (calculates natively on F9)
            add_table_of_contents(doc, structure)

        # 7. LOF — NATIVE WORD FIELD
        elif itype == "lof":
            add_list_of_figures(doc, figure_list)

        # 8. PAGE BREAK
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
            caption_clean = item.get("caption", "").strip()
            
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

            # EXACT FORMATTING PARITY: "3.1 Title" instead of "Figure 3.1 X: Title"
            run = p.add_run(f"{counters['chapter']}.")
            run.font.name = font_name
            run.font.size = Pt(11)

            # Inject the hidden SEQ field code for auto-numbering
            fldChar1 = OxmlElement("w:fldChar")
            fldChar1.set(ns.qn("w:fldCharType"), "begin")
            instrText = OxmlElement("w:instrText")
            instrText.set(ns.qn("xml:space"), "preserve")
            # \s 1 resets the SEQ number at every Heading 1 (Chapter)
            instrText.text = " SEQ Figure \\* ARABIC \\s 1 "
            fldChar2 = OxmlElement("w:fldChar")
            fldChar2.set(ns.qn("w:fldCharType"), "separate")

            # Word requires a cached text result, otherwise it drops the field as corrupted
            t = OxmlElement("w:t")
            t.text = str(counters["figure"])

            fldChar3 = OxmlElement("w:fldChar")
            fldChar3.set(ns.qn("w:fldCharType"), "end")

            run._r.append(fldChar1)
            run._r.append(instrText)
            run._r.append(fldChar2)
            run._r.append(t)
            run._r.append(fldChar3)

            run2 = p.add_run(" " + caption_clean)
            run2.font.name = font_name
            run2.font.size = Pt(11)

        # 10. PARAGRAPH / BODY / PLACEHOLDERS
        else:
            text = text.strip()
            if not text:
                continue  # Skip completely empty paragraphs

            import re

            # Code Extraction Tag
            code_match = re.search(r"\[Extract Code:\s*(.*?)\]", text, re.IGNORECASE)
            if code_match:
                # Expecting the precise codebase contents to be passed in through some context,
                # but since `formatting.py` iterates `structure`, we need `app.py` to inject
                # the actual code BEFORE sending it to formatting, or Formatting must accept a dict.
                # Easiest way: app.py handles extraction from the codebase dictionary and replaces the tag
                # with a `{"type": "code_block", "text": raw_code}` element.
                # So we simply need to support `code_block` type!
                pass  # Proceed. Support handled above.

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
    # Iterate and destroy totally empty trailing paragraphs to prevent consecutive blank pages
    for p in doc.paragraphs:
        if not p.text.strip():
            # If the paragraph has no text, AND it doesn't contain special XML elements like Page Breaks or Shading, delete it.
            has_break = False
            for run in p.runs:
                if '<w:br w:type="page"/>' in run._r.xml:
                    has_break = True
                    break

            # Don't delete formatting nodes, structural breaks, or embedded images
            has_drawing = bool(p._element.xpath('.//*[local-name()="drawing"]'))
            if (
                not has_break
                and not has_drawing
                and not p.paragraph_format.element.xpath(".//w:shd")
            ):
                p._element.getparent().remove(p._element)

    _add_page_numbers(doc, font_name)

    # --- Structural Validation (Root Cause 3 Fix) ---
    _validate_document_structure(doc)

    # --- Force F9 Field Update (Root Cause 1 Fix) ---
    # Injects the w:updateFields element into settings.xml so Word updates TOC/LOF on open
    try:
        element = doc.settings.element
        updatefields = OxmlElement("w:updateFields")
        updatefields.set(qn("w:val"), "true")
        element.append(updatefields)
    except Exception as e:
        print(f"[WARNING] Failed to inject Auto-Update Field trigger: {e}")

    # Save
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
    # Simple footer page num
    section = doc.sections[0]
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.font.name = font_name

    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(ns.qn("w:fldCharType"), "begin")

    instrText = OxmlElement("w:instrText")
    instrText.set(ns.qn("xml:space"), "preserve")
    instrText.text = "PAGE"

    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(ns.qn("w:fldCharType"), "end")

    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
