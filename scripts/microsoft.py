import json
import os
from datetime import datetime, timezone

import requests

API_KEY = os.getenv("ITAD_API_KEY", "")
COUNTRY = "IN"
MICROSOFT_SHOP_ID = 48

OUTPUT_FILE = "data/microsoft-store.json"
DEALS_URL = "https://api.isthereanydeal.com/deals/v2"


def main():
    if not API_KEY:
        raise RuntimeError("Missing ITAD_API_KEY secret")

    params = {
        "key": API_KEY,
        "country": COUNTRY,
        "shops": str(MICROSOFT_SHOP_ID),
    }

    res = requests.get(DEALS_URL, params=params, timeout=30)
    res.raise_for_status()

    data = res.json()

    print("API returned keys:", data.keys())
    print("Has more:", data.get("hasMore"))
    print("Next offset:", data.get("nextOffset"))

    deals = data.get("list", [])

    items = []
    seen = set()

    for item in deals:
        deal = item.get("deal", {})
        shop = deal.get("shop", {})
        price = deal.get("price", {})

        shop_id = shop.get("id")
        amount = price.get("amount")
        amount_int = price.get("amountInt")
        cut = deal.get("cut", 0)

        title = item.get("title", "").strip()

        print("DEAL:", title, "| shop:", shop_id, "| price:", amount, "| cut:", cut)

        if shop_id != MICROSOFT_SHOP_ID:
            continue

        is_free = amount == 0 or amount_int == 0 or cut == 100

        if not is_free:
            continue

        key = title.lower()
        if key in seen:
            continue

        seen.add(key)

        assets = item.get("assets", {})
        image = (
            assets.get("banner600")
            or assets.get("banner400")
            or assets.get("banner300")
            or assets.get("banner145")
            or assets.get("boxart")
            or ""
        )

        items.append(
            {
                "title": title,
                "platform": "Microsoft Store",
                "status": "free",
                "url": item.get("url") or deal.get("url") or "https://www.microsoft.com/store",
                "image": image,
                "price": "Free",
                "discount": "-100%" if cut == 100 else "",
                "source": "IsThereAnyDeal API",
            }
        )

    output = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(items)} Microsoft Store freebies")


if __name__ == "__main__":
    main()
