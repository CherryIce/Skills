(() => {
  const supported = new Set(["en", "zh"]);
  const queryLanguage = new URLSearchParams(window.location.search).get("lang");
  let storedLanguage = null;
  try {
    storedLanguage = window.localStorage.getItem("release-kit-language");
  } catch (_) {
    // Local storage can be unavailable in hardened browser modes.
  }
  const browserLanguage = navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en";
  const initialLanguage = [queryLanguage, storedLanguage, browserLanguage].find((value) => supported.has(value)) || "en";

  function applyLanguage(language) {
    if (!supported.has(language)) return;
    document.documentElement.lang = language === "zh" ? "zh-Hans" : "en";
    document.querySelectorAll("[data-lang]").forEach((element) => {
      element.hidden = element.dataset.lang !== language;
    });
    document.querySelectorAll("[data-language-option]").forEach((button) => {
      const active = button.dataset.languageOption === language;
      button.setAttribute("aria-pressed", String(active));
    });

    const title = language === "zh" ? document.body.dataset.titleZh : document.body.dataset.titleEn;
    const description = language === "zh" ? document.body.dataset.descriptionZh : document.body.dataset.descriptionEn;
    if (title) document.title = title;
    const meta = document.querySelector('meta[name="description"]');
    if (meta && description) meta.setAttribute("content", description);

    document.querySelectorAll("a[data-local-page]").forEach((link) => {
      const target = new URL(link.getAttribute("href"), window.location.href);
      target.searchParams.set("lang", language);
      link.setAttribute("href", `${target.pathname.split("/").pop()}${target.search}${target.hash}`);
    });
    try {
      window.localStorage.setItem("release-kit-language", language);
    } catch (_) {
      // The page still works when persistence is unavailable.
    }
  }

  document.querySelectorAll("[data-language-option]").forEach((button) => {
    button.addEventListener("click", () => applyLanguage(button.dataset.languageOption));
  });
  applyLanguage(initialLanguage);
})();
