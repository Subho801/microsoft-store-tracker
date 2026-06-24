import json
import re
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

URL = "https://isthereanydeal.com/deals/#filter:N4IgzgFgg9gDmIC4DaAWAHAXQL5A;sort:price"


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def is_free(text):
    t = text.lower()
    return (
        "₹0.00" in text
        or "$0.00" in text
        or "€0.00" in text
        or "£0.00" in text
        or "-100%" in text
        or "100%" in text
    )


items = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 2400})

    page.goto(URL, wait_until="networkidle", timeout=90000)
    page.wait_for_timeout(10000)

    for _ in range(8):
        page.mouse.wheel(0, 1400)
        page.wait_for_timeout(800)

    page.screenshot(path="microsoft-debug.png", full_page=True)

    deals = page.evaluate("""
    () => {
      const results = [];

      const rows = [...document.querySelectorAll("div, tr, article")]
        .filter(el => {
          const text = el.innerText || "";
          return (
            text.includes("Microsoft Store") &&
            (
              text.includes("₹0.00") ||
              text.includes("$0.00") ||
              text.includes("€0.00") ||
              text.includes("£0.00") ||
              text.includes("-100%")
            )
          );
        });

      for (const row of rows) {
        const text = row.innerText || "";
        const img = row.querySelector("img");

        const lines = text
          .split("\\n")
          .map(x => x.trim())
          .filter(Boolean);

        const title = lines.find(line =>
          line.length > 2 &&
          line.length < 120 &&
          !line.includes("Microsoft Store") &&
          !line.includes("₹") &&
          !line.includes("$") &&
          !line.includes("€") &&
          !line.includes("£") &&
          !line.includes("%") &&
          !line.toLowerCase().includes("shop") &&
          !line.toLowerCase().includes("current deals") &&
          !line.toLowerCase().includes("all games")
        );

        const price =
          lines.find(line =>
            line.includes("₹0.00") ||
            line.includes("$0.00") ||
            line.includes("€0.00") ||
            line.includes("£0.00")
          ) || "Free";

        const discount =
          lines.find(line => line.includes("-100%")) || "-100%";

        if (title) {
          results.push({
            title,
            image: img ? img.src : "",
            price,
            discount,
            rawText: text
          });
        }
      }

      return results;
    }
    """)

    seen = set()

    for deal in deals:
        title = clean(deal.get("title", ""))
        raw_text = clean(deal.get("rawText", ""))

        if not title:
            continue

        if not is_free(raw_text):
            continue

        key = title.lower()
        if key in seen:
            continue

        seen.add(key)

        items.append({
            "title": title,
            "platform": "Microsoft Store",
            "status": "free",
            "url": URL,
            "image": deal.get("image", "").replace("banner145.jpg", "banner300.jpg"),
            "price": clean(deal.get("price", "Free")),
            "discount": clean(deal.get("discount", "-100%")),
            "source": "IsThereAnyDeal",
        })

    browser.close()


output = {
    "updatedAt": datetime.now(timezone.utc).isoformat(),
    "count": len(items),
    "items": items,
}

with open("data/microsoft-store.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Saved {len(items)} Microsoft Store freebies")
