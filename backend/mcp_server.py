from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
import sys, os, json, faiss, numpy as np, hashlib, time, threading, requests
from pathlib import Path
from markitdown import MarkItDown
from tqdm import tqdm

mcp = FastMCP("WebMemoryAgent")

# =====================
# CONFIGURATION
# =====================
ROOT = Path(__file__).parent.resolve()
DOC_PATH = ROOT / "documents"
INDEX_CACHE = ROOT / "faiss_index"
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 256
CHUNK_OVERLAP = 40

INDEX_CACHE.mkdir(exist_ok=True)

# =====================
# HELPERS
# =====================
def mcp_log(level, msg):
    sys.stderr.write(f"{level}: {msg}\n")
    sys.stderr.flush()

def get_embedding(text: str) -> np.ndarray:
    """Get text embedding from Ollama."""
    response = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split long text into overlapping chunks."""
    words = text.split()
    for i in range(0, len(words), size - overlap):
        yield " ".join(words[i:i+size])

def file_hash(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()

# =====================
# MEMORY INDEXING (FAISS)
# =====================
def process_documents():
    """Process documents and create FAISS index"""
    mcp_log("INFO", "Indexing documents with MarkItDown...")
    DOC_PATH = ROOT / "documents"
    INDEX_CACHE = ROOT / "faiss_index"
    INDEX_CACHE.mkdir(exist_ok=True)
    INDEX_FILE = INDEX_CACHE / "index.bin"
    METADATA_FILE = INDEX_CACHE / "metadata.json"
    CACHE_FILE = INDEX_CACHE / "doc_index_cache.json"

    CACHE_META = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    metadata = json.loads(METADATA_FILE.read_text()) if METADATA_FILE.exists() else []
    index = faiss.read_index(str(INDEX_FILE)) if INDEX_FILE.exists() else None
    converter = MarkItDown()

    for file in DOC_PATH.glob("*.*"):
        # skip non-JSON files
        if file.suffix != ".json":
            mcp_log("SKIP", f"Skipping non-JSON file: {file.name}")
            continue

        fhash = file_hash(file)
        if file.name in CACHE_META and CACHE_META[file.name] == fhash:
            mcp_log("SKIP", f"Skipping unchanged file: {file.name}")
            continue

        mcp_log("PROC", f"Processing: {file.name}")
        try:
            with open(file, "r", encoding="utf-8") as f:
                try:
                    page_data = json.load(f)
                except json.JSONDecodeError:
                    mcp_log("ERROR", f"Invalid JSON: {file.name}")
                    continue

                markdown = page_data.get("text", "")
                page_url = page_data.get("url", "")

            if not markdown.strip():
                mcp_log("SKIP", f"No text content: {file.name}")
                continue

            chunks = list(chunk_text(markdown))
            embeddings_for_file = []
            new_metadata = []

            for i, chunk in enumerate(tqdm(chunks, desc=f"Embedding {file.name}")):
                embedding = get_embedding(chunk)
                embeddings_for_file.append(embedding)
                new_metadata.append({
                    "doc": file.name,
                    "chunk": chunk,
                    "chunk_id": f"{file.stem}_{i}",
                    "url": page_url
                })

            if embeddings_for_file:
                if index is None:
                    dim = len(embeddings_for_file[0])
                    index = faiss.IndexFlatL2(dim)
                index.add(np.stack(embeddings_for_file))
                metadata.extend(new_metadata)

            CACHE_META[file.name] = fhash

        except Exception as e:
            mcp_log("ERROR", f"Failed to process {file.name}: {e}")

    # Save cache and metadata
    CACHE_FILE.write_text(json.dumps(CACHE_META, indent=2))
    METADATA_FILE.write_text(json.dumps(metadata, indent=2))
    if index and index.ntotal > 0:
        faiss.write_index(index, str(INDEX_FILE))
        mcp_log("SUCCESS", "Saved FAISS index and metadata")
    else:
        mcp_log("WARN", "No new documents or updates to process.")

@mcp.tool()
def search_documents(query: str) -> list[dict]:
    """Search for relevant content from uploaded documents."""
    #ensure_faiss_ready()
    mcp_log("SEARCH", f"Query: {query}")
    print("query is ", query)
    try:
        index = faiss.read_index(str(ROOT / "faiss_index" / "index.bin"))
        metadata = json.loads((ROOT / "faiss_index" / "metadata.json").read_text())
        query_vec = get_embedding(query).reshape(1, -1)
        D, I = index.search(query_vec, k=2)
        results = []
        for idx in I[0]:
            data = metadata[idx]
            results.append({
                "chunk": data['chunk'],
                "doc": data['doc'],
                "chunk_id": data['chunk_id'],
                "url": data.get("url", "")
            })
        return results
    except Exception as e:
        return [{"error": f"Failed to search: {str(e)}"}]
# =====================
# START SERVER
# =====================
if __name__ == "__main__":
    print("🚀 Starting MCP WebMemoryAgent...")

    server_thread = threading.Thread(target=lambda: mcp.run(transport="stdio"))
    server_thread.daemon = True
    server_thread.start()

    # Index previously browsed pages before serving requests
    time.sleep(1)
    print("process_documents")
    process_documents()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
