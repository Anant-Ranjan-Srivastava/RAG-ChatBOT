from pathlib import Path
import fitz


def parse_pdf_folder(folder_path):
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

                    spans = line.get("spans", [])

                    if not spans:
                        continue

                    merged_text = "".join(
                        span["text"] for span in spans
                    ).strip()

                    if not merged_text:
                        continue

                    parsed_content.append(
                        {
                            "page": page_number,
                            "text": merged_text,
                            "font_size": spans[0]["size"],
                            "font_name": spans[0]["font"],
                        }
                    )

        doc.close()

    return parsed_content


if __name__ == "__main__":

    results = parse_pdf_folder("../data")

    print(f"\nTotal Records: {len(results)}\n")

    for i, item in enumerate(results[:50], start=1):
        print("=" * 100)
        print(f"Record #{i}")
        print(f"Page      : {item['page']}")
        print(f"Font Size : {item['font_size']}")
        print(f"Font Name : {item['font_name']}")
        print(f"Text      : {item['text']}")