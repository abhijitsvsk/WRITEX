def detect(text):
    cleaned_text = text.strip()

    if not cleaned_text:
        return "Empty"

    words = cleaned_text.split()

    if len(words) <= 3 and cleaned_text.isupper():
        return "Heading"

    if words[0][0].isdigit():
        return "Heading"

    if words[0][0].isdigit() and len(words) <= 4 and cleaned_text.isupper():
        return "sub-heading"

    return "Body"
