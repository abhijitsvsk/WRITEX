from docx import Document
from utils.para_type_detector import detect
from file_formatting.formatting import apply_paragraph_format


def main():
    doc = Document("D:/writex/test.docx")
    for paragraph in doc.paragraphs:
        paragraph.paragraph_format.line_spacing = 5
        para_type = detect(paragraph.text)
        apply_paragraph_format(para_type, paragraph)
    doc.save("formatted.docx")


if __name__ == "__main__":
    main()
