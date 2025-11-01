from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import re
import json
from mcp_server import process_documents, search_documents  # direct import

app = FastAPI(title="AI Memory Agent Backend")

# Enable CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure documents folder exists
DOC_PATH = Path("documents")
DOC_PATH.mkdir(exist_ok=True)

@app.post("/index_page")
async def index_page(req: Request):
    data = await req.json()
    url = data.get("url")
    title = data.get("title", "untitled")
    text = data.get("text")

    if not text or not url:
        return {"status": "error", "message": "Missing url or text"}

    # Sanitize filename and save as JSON
    safe_name = re.sub(r"[^A-Za-z0-9]", "_", title)[:100] + ".json"
    doc_file = DOC_PATH / safe_name

    # Save page content as JSON
    doc_file.write_text(json.dumps({"title": title, "text": text, "url": url}), encoding="utf-8")

    # Optionally, trigger indexing asynchronously
    # process_documents()

    return {"status": "queued", "file": safe_name}


@app.get("/agent")
async def agent(query: str):
    try:
        memory_results = search_documents(query=query)
        print("memory results is ", memory_results)
        # Open first URL if exists
        page_url = memory_results[0]["url"] if memory_results and memory_results[0].get("url") else None
        action = "show_memory" if page_url else "search_web"

        return {"action": {"action": action}, "memory_results": memory_results, "page_url": page_url}
    except Exception as e:
        return {"action": {"action": "search_web"}, "memory_results": [], "page_url": None, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
