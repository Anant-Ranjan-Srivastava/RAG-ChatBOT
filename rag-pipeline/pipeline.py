import parser
import chunker

if __name__ == "__main__":
    results = parser.parse_all_pdfs(chunk_callback=chunker.chunk_pdf)

    print(f"Processed {len(results)} PDF(s).")
    print("Parsed JSON  -> data/parsed/")
    print("Chunked JSON -> data/chunked/")