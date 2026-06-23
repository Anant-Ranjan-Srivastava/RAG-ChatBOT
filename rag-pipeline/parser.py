from pathlib import Path
import fitz 


def parse_pdf_folder(folder_path: str):
    parsed_content = []

    pdf_files = Path(folder_path).glob("*.pdf")

    for pdf_file in pdf_files:
        doc = fitz.open(pdf_file)

        for page_number, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")

            for block in page_dict["blocks"]:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        parsed_content.append(
                            {
                                "pdf_name": pdf_file.name,
                                "page": page_number,
                                "text": span["text"].strip(),
                                "font_size": span["size"],
                                "font_name": span["font"],
                            }
                        )

        doc.close()

    return parsed_content

# ====================== TEMPORARY TEST ======================
results = parse_pdf_folder("../data")
print(len(results)) # For checking if all pages parsed or not.

for item in results[:10]: # Printing the first 10.
    print(item)  