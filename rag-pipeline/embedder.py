import os
import json
import math
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

CHUNKED_DIR = "../data/chunked"
EMBED_OUTPUT_DIR = "../data/embedded"
FAISS_INDEX_PATH = os.path.join(EMBED_OUTPUT_DIR, "index.faiss")
METADATA_PATH = os.path.join(EMBED_OUTPUT_DIR, "metadata.json")

MODEL_NAME = "nomic-ai/nomic-embed-text-v1"
DEVICE = "cpu"
TASK_PREFIX = "search_document: "   # nomic's required convention for indexing documents
BATCH_SIZE = 32                  

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, trust_remote_code=True, device=DEVICE)
    return _model

# ---------- TESTING TWO INPUT OPTIONS ----------
# ---------- input: option A - read from disk ----------

def load_chunks_from_disk():
    """Reads every data/chunked/*.json file and returns a flat list of chunk dicts."""
    all_chunks = []
    if not os.path.isdir(CHUNKED_DIR):
        print(f"No chunked directory found at {CHUNKED_DIR}. Run chunker.py first.")
        return all_chunks

    for fname in os.listdir(CHUNKED_DIR):
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(CHUNKED_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        all_chunks.extend(chunks)

    return all_chunks


# ---------- input: option B - direct callback from chunker ----------

# def embed_chunk_callback(filename, chunks):
#     """
#     Pass this directly as chunker.py's output handler if you want embedding
#     to happen immediately after chunking, without writing/reading data/chunked.
#     Usage: chunker.chunk_pdf(filename, lines_out) -> then call this manually,
#     or wire it into your own pipeline runner.
#     """
#     embed_and_store(chunks)

# ---------- embedding ----------

def embed_texts(texts):
    model = get_model()
    prefixed = [TASK_PREFIX + t for t in texts]
    vectors = model.encode(
        prefixed,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    return vectors.astype("float32")


# ---------- FAISS index ----------

def build_faiss_index(vectors):
    """
    IVF index (IndexIVFFlat) over an L2 flat quantizer.
    nlist is derived from dataset size (sqrt heuristic), with a safety floor/cap
    since IVF needs at least ~nlist training points to behave well.
    Tune nlist/nprobe later based on actual corpus size.
    """
    num_vectors, dim = vectors.shape
    nlist = max(1, int(math.sqrt(num_vectors)))
    nlist = min(nlist, max(1, num_vectors // 10)) if num_vectors >= 10 else 1

    quantizer = faiss.IndexFlatL2(dim)
    index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_L2)

    index.train(vectors)
    index.add(vectors)
    index.nprobe = max(1, nlist // 8)   # tune later

    return index


# ---------- save ----------

def save_outputs(chunks, vectors, index):
    os.makedirs(EMBED_OUTPUT_DIR, exist_ok=True)

    # JSON: human-readable record of text + metadata + embedding (per design decision)
    records = []
    for chunk, vector in zip(chunks, vectors):
        record = dict(chunk)  # copy text/header/level/page/source_file
        record["embedding"] = vector.tolist()
        records.append(record)

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # FAISS index file (vector id position == index in `chunks` list)
    faiss.write_index(index, FAISS_INDEX_PATH)

    print(f"Saved {len(records)} embeddings -> {METADATA_PATH}")
    print(f"Saved FAISS IVF index -> {FAISS_INDEX_PATH}")


# ---------- main pipeline ----------

def embed_and_store(chunks):
    if not chunks:
        print("No chunks to embed.")
        return None, None

    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)
    index = build_faiss_index(vectors)
    save_outputs(chunks, vectors, index)
    return vectors, index


if __name__ == "__main__":
    # --- Option A: read chunks from disk (default) ---
    chunks = load_chunks_from_disk()
    embed_and_store(chunks)

    # --- Option B: comment out Option A above and uncomment below if you want
    #     to wire embedding directly from chunker's output instead of disk ---
    # import chunker
    # chunks = chunker.chunk_all_pdfs()  # returns {filename: chunk_list}
    # flat_chunks = [c for chunk_list in chunks.values() for c in chunk_list]
    # embed_and_store(flat_chunks)