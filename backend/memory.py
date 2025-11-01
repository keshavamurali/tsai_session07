# memory.py
from mcp_server import search_documents, process_documents

def index_new_page(file_path: str):
    """
    Trigger MCP to index new page after saving.
    """
    process_documents()


def search_memory(query: str):
    """
    Search MCP memory for query.
    """
    results = search_documents(query=query)
    return results


# Example usage
if __name__ == "__main__":
    # Index all existing documents
    #process_documents()

    # Test search
    query = "dog"
    results = search_memory(query)
    print(f"Memory search results for '{query}':")
    for r in results:
        print("-", r)
