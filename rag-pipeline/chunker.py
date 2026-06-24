import os
import re
import json
from collections import Counter

CHUNK_OUTPUT_DIR = "../data/chunked"
MAX_CHARS = 1500       # tune later
OVERLAP_CHARS = 150    # tune later


# ---------- helpers ----------

def is_bold(font_name):
    return "bold" in font_name.lower()


def get_body_size(lines):
    weighted = Counter()
    for l in lines:
        weighted[round(l["size"], 1)] += len(l["text"])
    return weighted.most_common(1)[0][0]


def detect_headers(lines, body_size):
    for l in lines:
        size = round(l["size"], 1)
        bold = is_bold(l["font"])
        l["is_header"] = (size > body_size) or (size == body_size and bold)
    return lines


def assign_levels(lines):
    header_keys = {(round(l["size"], 1), is_bold(l["font"])) for l in lines if l["is_header"]}
    ranked = sorted(header_keys, key=lambda k: (-k[0], not k[1]))  # size desc, bold first
    level_map = {key: i + 1 for i, key in enumerate(ranked)}

    for l in lines:
        if l["is_header"]:
            key = (round(l["size"], 1), is_bold(l["font"]))
            l["level"] = level_map[key]
        else:
            l["level"] = None
    return lines


# ---------- tree building ----------

class Node:
    def __init__(self, header_text, level, page, source_file):
        self.header_text = header_text
        self.level = level
        self.page = page
        self.source_file = source_file
        self.content_lines = []   # direct content (not in children)
        self.children = []

    def own_text(self):
        parts = []
        if self.header_text:
            parts.append(self.header_text)
        parts.extend(self.content_lines)
        return "\n".join(parts)

    def full_text(self):
        parts = [self.own_text()]
        for child in self.children:
            child_text = child.full_text()
            if child_text.strip():
                parts.append(child_text)
        return "\n".join(p for p in parts if p.strip())


def build_tree(lines, source_file):
    root_nodes = []
    preamble = Node("Preamble", 0, lines[0]["page"] if lines else 1, source_file)
    stack = [(0, preamble)]
    root_nodes.append(preamble)

    for line in lines:
        if line["is_header"]:
            node = Node(line["text"], line["level"], line["page"], source_file)
            while stack and stack[-1][0] >= node.level:
                stack.pop()
            parent = stack[-1][1] if stack else None
            if parent:
                parent.children.append(node)
            else:
                root_nodes.append(node)
            stack.append((node.level, node))
        else:
            stack[-1][1].content_lines.append(line["text"])

    return root_nodes


# ---------- splitting (paragraph -> sentence -> hard char) ----------

def split_paragraphs(text):
    paras = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paras if p.strip()]


def split_sentences(text):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def greedy_pack(units, max_chars, sub_split_fn=None):
    """
    Greedily combine units (paragraphs or sentences) into pieces <= max_chars.
    If a single unit exceeds max_chars, recursively split it with sub_split_fn,
    or hard-slice by characters if no sub_split_fn given.
    """
    pieces = []
    current = ""

    for unit in units:
        if len(unit) > max_chars:
            if current:
                pieces.append(current)
                current = ""
            if sub_split_fn:
                pieces.extend(greedy_pack(sub_split_fn(unit), max_chars, None))
            else:
                # hard slice
                for i in range(0, len(unit), max_chars):
                    pieces.append(unit[i:i + max_chars])
            continue

        candidate = (current + "\n" + unit).strip() if current else unit
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                pieces.append(current)
            current = unit

    if current:
        pieces.append(current)

    return pieces


def apply_overlap(pieces, overlap_chars):
    if overlap_chars <= 0 or len(pieces) < 2:
        return pieces
    overlapped = [pieces[0]]
    for i in range(1, len(pieces)):
        prev_tail = pieces[i - 1][-overlap_chars:]
        overlapped.append(prev_tail + "\n" + pieces[i])
    return overlapped


def split_oversized_text(text):
    paragraphs = split_paragraphs(text)
    pieces = greedy_pack(paragraphs, MAX_CHARS, sub_split_fn=split_sentences)
    return apply_overlap(pieces, OVERLAP_CHARS)


# ---------- chunk assembly ----------

def make_chunk(node, text):
    return {
        "text": text,
        "header": node.header_text,
        "level": node.level,
        "page": node.page,
        "source_file": node.source_file
    }


def chunk_node(node):
    full_text = node.full_text()
    if not full_text.strip():
        return []

    if len(full_text) <= MAX_CHARS:
        return [make_chunk(node, full_text)]

    # Too large: split along sub-headings if present
    if node.children:
        chunks = []
        own = node.own_text()
        if own.strip():
            if len(own) <= MAX_CHARS:
                chunks.append(make_chunk(node, own))
            else:
                chunks.extend(make_chunk(node, piece) for piece in split_oversized_text(own))
        for child in node.children:
            chunks.extend(chunk_node(child))
        return chunks

    # No sub-headings: paragraph -> sentence -> char split
    return [make_chunk(node, piece) for piece in split_oversized_text(full_text)]


# ---------- public entry points ----------

def chunk_pdf(filename, lines_out):
    if not lines_out:
        return []

    body_size = get_body_size(lines_out)
    lines_out = detect_headers(lines_out, body_size)
    lines_out = assign_levels(lines_out)

    header_count = sum(1 for l in lines_out if l["is_header"])
    print(f"[{filename}] body_size={body_size} | headers detected={header_count}")

    root_nodes = build_tree(lines_out, filename)

    all_chunks = []
    for node in root_nodes:
        all_chunks.extend(chunk_node(node))

    save_chunks(filename, all_chunks)
    return all_chunks


def save_chunks(filename, chunks):
    os.makedirs(CHUNK_OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(CHUNK_OUTPUT_DIR, f"{os.path.splitext(filename)[0]}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    return out_path


# ---------- standalone execution (reads from data/parsed) ----------

PARSED_DIR = "../data/parsed"


def load_parsed_pdfs():
    pdfs = {}
    if not os.path.isdir(PARSED_DIR):
        print(f"No parsed directory found at {PARSED_DIR}. Run parser.py first.")
        return pdfs

    for fname in os.listdir(PARSED_DIR):
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(PARSED_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            lines_out = json.load(f)
        original_pdf_name = os.path.splitext(fname)[0] + ".pdf"
        pdfs[original_pdf_name] = lines_out
    return pdfs


def chunk_all_pdfs():
    pdfs = load_parsed_pdfs()
    results = {}
    for filename, lines_out in pdfs.items():
        results[filename] = chunk_pdf(filename, lines_out)
    return results


if __name__ == "__main__":
    chunk_all_pdfs()