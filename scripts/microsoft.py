import json
import re
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

URL = "https://isthereanydeal.com/deals/#/filter:stores/48"


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


items = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 2400})

    page.goto(URL, wait_until="networkidle", timeout=90000)
    page.wait_for_timeout(8000)

    for _ in range(10):
        page.mouse.wheel(0, 1600)
        page.wait_for_timeout(800)

    page.screenshot(path="microsoft-debug.png", full_page=True)

    deals = page.evaluate("""
    () => {
      const results = [];
      const rows = [...document.querySelectorAll("tr, article, [class*='game'], [class*='deal'], [class*='item'], [class*='row']")];

      for (const row of rows) {
        const text = row.innerText || "";
        const img = row.querySelector("img");

        if (!img) continue;

        const lower = text.toLowerCase();

        const looksFree =
          lower.includes("free") ||
          lower.includes("100%") ||
          lower.includes("-100%") ||
          lower.includes("₹0") ||
          lower.includes("$0") ||
          lower.includes("0.00");

        if (!looksFree) continue;

        const lines = text
          .split("\\n")
          .map(x => x.trim())
          .filter(Boolean);

        const title = lines.find(line =>
          line.length > 2 &&
          line.length < 120 &&
          !line.toLowerCase().includes("free") &&
          !line.toLowerCase().includes("microsoft") &&
          !line.toLowerCase().includes("store") &&
          !line.match(/^[₹$€£]?\\d/)
        );

        if (!title) continue;

        results.push({
          title,
          image: img.src || "",
          rawText: text
        });
      }

      return results;
    }
    """)

    seen = set()

    for deal in deals:
        title = clean(deal.get("title", ""))
        image = deal.get("image", "")
        raw = clean(deal.get("rawText", ""))

        if not title:
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
            "image": image.replace("banner145.jpg", "banner300.jpg"),
            "price": "Free",
            "source": "IsThereAnyDeal",
            "rawText": raw[:300],
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
