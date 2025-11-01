document.getElementById("searchBtn").addEventListener("click", () => {
  const query = document.getElementById("query").value.trim();
  if (!query) return;

  document.getElementById("status").textContent = "Searching...";
  chrome.runtime.sendMessage({ action: "search_query", query }, (response) => {
    if (response.status === "ok") {
      document.getElementById("status").textContent = "Done!";
    } else {
      document.getElementById("status").textContent = "Error: " + response.error;
    }
  });
});
