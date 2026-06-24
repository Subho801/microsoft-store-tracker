import json
import os
from datetime import datetime, timezone

import requests

API_KEY = os.getenv("ITAD_API_KEY", "")
COUNTRY = "IN"
MICROSOFT_SHOP_ID = 48

OUTPUT_FILE = "data/microsoft-store.json"
DEALS_URL = "https://api.isthereanydeal.com/deals/v2"


def get_image(item):
    assets = item.get("assets", {})
    return (
        assets.get("banner600")
        or assets.get("banner400")
        or assets.get("banner300")
        or assets.get("banner145")
        or assets.get("boxart")
        or ""
    )


def main():
    if not API_KEY:
        raise RuntimeError("Missing ITAD_API_KEY secret")

    items = []
    seen = set()
    offset = 0

    while True:
        params = {
            "key": API_KEY,
            "country": COUNTRY,
            "shops": str(MICROSOFT_SHOP_ID),
            "sort": "price",
            "offset": offset,
        }

        res = requests.get(DEALS_URL, params=params, timeout=30)
        res.raise_for_status()

        data = res.json()
        deals = data.get("list", [])

        print(f"Checking offset {offset}, got {len(deals)} deals")

        for item in deals:
            deal = item.get("deal", {})
            shop = deal.get("shop", {})
            price = deal.get("price", {})

            title = item.get("title", "").strip()
            shop_id = shop.get("id")
            amount = price.get("amount")
            amount_int = price.get("amountInt")
            cut = deal.get("cut", 0)

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

            items.append({
                "title": title,
                "platform": "Microsoft Store",
                "status": "free",
                "url": item.get("url") or deal.get("url") or "https://www.microsoft.com/store",
                "image": get_image(item),
                "price": "Free",
                "discount": "-100%" if cut == 100 else "",
                "source": "IsThereAnyDeal",
            })

        if not data.get("hasMore"):
            break

        next_offset = data.get("nextOffset")

        if next_offset is None or next_offset == offset:
            break

        offset = next_offset

        if offset > 1000:
            print("Stopped after offset 1000 to avoid endless scanning")
            break

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
