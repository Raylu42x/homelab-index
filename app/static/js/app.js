// Homelab Index — small interactivity layer on top of HTMX.
(() => {
  "use strict";

  function focusSearch() {
    const el = document.querySelector("[data-global-search]");
    if (el) {
      el.focus();
      el.select();
    }
  }

  document.addEventListener("keydown", (e) => {
    const isMeta = e.metaKey || e.ctrlKey;
    const tag = (e.target.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "textarea";

    if (isMeta && e.key.toLowerCase() === "k") {
      e.preventDefault();
      focusSearch();
      return;
    }

    if (!typing && e.key === "/") {
      e.preventDefault();
      focusSearch();
      return;
    }

    if (e.key === "Escape" && typing) {
      e.target.blur();
      const results = document.querySelector("[data-search-results]");
      if (results) results.innerHTML = "";
    }
  });

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-copy]");
    if (!btn) return;
    const value = btn.getAttribute("data-copy");
    navigator.clipboard.writeText(value).then(() => {
      const original = btn.innerHTML;
      btn.innerHTML = "Copied";
      btn.classList.add("btn-accent");
      setTimeout(() => {
        btn.innerHTML = original;
        btn.classList.remove("btn-accent");
      }, 1200);
    });
  });

  // Close the search dropdown when clicking outside of it.
  document.addEventListener("click", (e) => {
    const wrap = document.querySelector(".search-wrap");
    const results = document.querySelector("[data-search-results]");
    if (!wrap || !results) return;
    if (!wrap.contains(e.target)) {
      results.innerHTML = "";
    }
  });
})();
