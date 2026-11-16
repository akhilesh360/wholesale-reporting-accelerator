// Injected into Snowflake / Strategy pages before recording. Blurs any element
// whose own text contains account or personal identifiers, and keeps doing so
// as the page changes.
(() => {
  const PAT = /(lk72347|bwnqupl|mb87799|saiakhilesh|sai akhilesh|akhilesh|veldi|sxv9415|USER\$)/i;
  const blurEl = (el) => {
    if (!el || el.dataset.pvBlur) return;
    el.dataset.pvBlur = "1";
    el.style.setProperty("filter", "blur(6px)", "important");
  };
  const scan = (root) => {
    const w = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) if (PAT.test(n.nodeValue)) blurEl(n.parentElement);
    document.querySelectorAll("[title],[aria-label],img[alt]").forEach((e) => {
      const t = (e.getAttribute("title") || "") + (e.getAttribute("aria-label") || "") + (e.getAttribute("alt") || "");
      if (PAT.test(t)) blurEl(e);
    });
  };
  scan();
  if (!window.__pvObs) {
    window.__pvObs = new MutationObserver(() => scan());
    window.__pvObs.observe(document.body, { subtree: true, childList: true, characterData: true });
  }
  return document.querySelectorAll("[data-pv-blur]").length;
})();
