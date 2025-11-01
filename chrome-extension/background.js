// Listen for popup search queries
chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
    if (message.action === "search_query") {
      const query = message.query;
      try {
        const res = await fetch(`http://localhost:8000/agent?query=${encodeURIComponent(query)}`);
        const data = await res.json();
  
        if (data.action.action === "show_memory" && data.memory_results.length > 0) {
          // Open first memory result
          const url = data.memory_results[0].url;
          chrome.tabs.create({ url });
        } else {
          // Open Google search
          const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
          chrome.tabs.create({ url: searchUrl });
        }
        sendResponse({ status: "ok" });
      } catch (err) {
        console.error(err);
        sendResponse({ status: "error", error: err.toString() });
      }
    }
    return true; // Keep message channel open for async response
  });
  
  // Optional: capture tab updates (automatic page indexing)
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.url.startsWith("http")) {
      chrome.scripting.executeScript({
        target: { tabId },
        func: () => document.body.innerText
      }, (results) => {
        if (results && results[0] && results[0].result) {
          const pageText = results[0].result;
          const payload = {
            url: tab.url,
            title: tab.title,
            text: pageText
          };
          fetch("http://localhost:8000/index_page", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          }).then(res => res.json())
            .then(resp => console.log("Indexed:", resp))
            .catch(err => console.error("Indexing error:", err));
        }
      });
    }
  });
  