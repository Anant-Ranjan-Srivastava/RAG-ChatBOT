import fitz  # PyMuPDF
import os
import json

DATA_DIR = "../data"
OUTPUT_DIR = "../data/parsed"


def parse_pdf(pdf_path):
    """Parse a single PDF. Returns list of line dicts."""
    doc = fitz.open(pdf_path)
    lines_out = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                spans = line["spans"]
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans).strip()
                if not text:
                    continue
                # use first span's font/size as representative for the line
                font = spans[0]["font"]
                size = spans[0]["size"]

                lines_out.append({
                    "page": page_num,
                    "font": font,
                    "size": size,
                    "text": text
                })

    doc.close()
    return lines_out


def save_parsed(pdf_filename, lines_out):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(pdf_filename)[0]}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(lines_out, f, ensure_ascii=False, indent=2)
    return out_path


def parse_all_pdfs(chunk_callback=None):
    """
    Iterate all PDFs in DATA_DIR.
    Saves JSON per PDF AND optionally calls chunk_callback(pdf_filename, lines_out)
    to feed results directly into a chunker.
    """
    results = {}

    for filename in os.listdir(DATA_DIR):
        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(DATA_DIR, filename)
        lines_out = parse_pdf(pdf_path)

        save_parsed(filename, lines_out)
        results[filename] = lines_out

        if chunk_callback:
            chunk_callback(filename, lines_out)

    return results


if __name__ == "__main__":
    parse_all_pdfs()