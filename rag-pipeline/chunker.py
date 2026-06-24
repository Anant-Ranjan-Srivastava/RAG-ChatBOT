from collections import defaultdict


def is_heading(record):
    return (
        record["font_size"] == 15
        and "Bold" in record["font_name"]
    )


def is_subheading(record):
    return (
        record["font_size"] == 15
        and "Bold" not in record["font_name"]
    )


def is_body(record):
    return record["font_size"] == 9.96


def chunk_documents(records, max_words=1500):
    chunks = []
    current_chunk = None

    def word_count(text):
        return len(text.split())

    for r in records:

        if is_heading(r):
            # close previous chunk
            if current_chunk:
                chunks.append(current_chunk)

            current_chunk = {
                "heading": r["text"],
                "content": "",
                "subsections": []
            }

        elif is_subheading(r):
            if not current_chunk:
                continue

            current_chunk["subsections"].append({
                "title": r["text"],
                "content": ""
            })

        elif is_body(r):
            if not current_chunk:
                continue

            # attach to latest subheading if exists
            if current_chunk["subsections"]:
                current_chunk["subsections"][-1]["content"] += " " + r["text"]
            else:
                current_chunk["content"] += " " + r["text"]

    # append last chunk
    if current_chunk:
        chunks.append(current_chunk)

    # ---- SIZE CHECK + FALLBACK ----
    final_chunks = []

    for c in chunks:

        total_text = c["heading"] + " " + c["content"]
        for s in c["subsections"]:
            total_text += " " + s["title"] + " " + s["content"]

        if word_count(total_text) <= max_words:
            final_chunks.append({
                "text": total_text.strip()
            })
        else:
            # recursive fallback → split by subsections first
            if c["subsections"]:
                for s in c["subsections"]:
                    sub_text = f"{c['heading']} {s['title']} {s['content']}"
                    final_chunks.append({"text": sub_text.strip()})
            else:
                # final fallback: hard split
                words = total_text.split()
                for i in range(0, len(words), max_words):
                    final_chunks.append({
                        "text": " ".join(words[i:i+max_words])
                    })

    return final_chunks


if __name__ == "__main__":
    from parser import parse_pdf_folder

    records = parse_pdf_folder("../data")
    chunks = chunk_documents(records)

    print(f"\nTotal chunks: {len(chunks)}\n")

    for i, c in enumerate(chunks[:10], start=1):
        print("=" * 100)
        print(f"Chunk #{i}")
        print(c["text"][:500])