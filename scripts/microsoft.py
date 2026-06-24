import json
import os
from datetime import datetime, timezone

import requests

API_KEY = os.getenv("ITAD_API_KEY", "")
COUNTRY = "IN"
OUTPUT_FILE = "data/microsoft-store.json"

# We will auto-detect the Microsoft Store shop id first.
SHOPS_MAP_URL = "https://api.isthereanydeal.com/service/shops/map/v1"
DEALS_URL = "https://api.isthereanydeal.com/deals/v2"


def get_microsoft_shop_id():
    res = requests.get(
        SHOPS_MAP_URL,
        params={"key": API_KEY},
        timeout=30,
    )
    res.raise_for_status()

    shops = res.json()

    for shop in shops:
        name = str(shop.get("name", "")).lower()
        title = str(shop.get("title", "")).lower()

        if "microsoft" in name or "microsoft" in title:
            return shop.get("id")

    raise RuntimeError("Microsoft Store shop id not found in ITAD shops map")


def get_image(game):
    assets = game.get("assets") or {}
    return (
        assets.get("banner600")
        or assets.get("banner300")
        or assets.get("banner145")
        or assets.get("boxart")
        or ""
    )


def main():
    if not API_KEY:
        raise RuntimeError("Missing ITAD_API_KEY GitHub secret")

    microsoft_shop_id = get_microsoft_shop_id()
    print(f"Microsoft Store shop id: {microsoft_shop_id}")

    payload = {
        "country": COUNTRY,
        "sort": "price",
        "limit": 200,
        "shops": [microsoft_shop_id],
        "filter": {
            "price": {
                "max": 0
            }
        },
    }

    res = requests.post(
        DEALS_URL,
        params={"key": API_KEY},
        json=payload,
        timeout=30,
    )
    res.raise_for_status()

    data = res.json()

    items = []
    seen = set()

    # ITAD can return either a list or an object depending on endpoint version.
    deals = data if isinstance(data, list) else data.get("list", data.get("deals", []))

    for deal in deals:
        game = deal.get("game") or deal

        title = (
            game.get("title")
            or game.get("name")
            or deal.get("title")
            or deal.get("name")
            or ""
        ).strip()

        if not title:
            continue

        price_data = deal.get("price") or deal.get("current") or {}
        price_amount = price_data.get("amount", None)
        price_int = price_data.get("amountInt", None)

        cut = deal.get("cut", 0)

        is_free = (
            price_amount == 0
            or price_int == 0
            or cut == 100
        )

        if not is_free:
            continue

        key = title.lower()
        if key in seen:
            continue

        seen.add(key)

        items.append(
            {
                "title": title,
                "platform": "Microsoft Store",
                "status": "free",
                "url": deal.get("url") or "",
                "image": get_image(game),
                "price": "Free",
                "discount": "-100%",
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
