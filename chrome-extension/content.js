// Only sends page content after 5s delay, skips confidential pages
setTimeout(async () => {
  const url = window.location.href;
  const isConfidential = url.includes("bank") || url.includes("login");
  if (isConfidential) return;

  const title = document.title;
  const text = document.body.innerText;

  try {
    await fetch("http://localhost:8000/index_page", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, title, text }) // always "text" field
    });
  } catch (e) {
    console.warn("Backend not reachable:", e);
  }
}, 5000);
