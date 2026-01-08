import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import json
import time
import os

def scrape_bcci_players():
    base_url = "https://www.bcci.tv"
    target_url = "https://www.bcci.tv/international/men/videos/player"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    print(f"Fetching: {target_url}")

    try:
        response = requests.get(target_url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print("❌ Request failed:", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    players_data = []

    # PRIMARY METHOD
    player_links = soup.find_all("a", onclick="click_player(this)")
    print(f"Found {len(player_links)} player blocks")

    for link in player_links:
        try:
            player = {}

            # Name
            name = link.get("data-player_name", "").strip()
            if not name:
                img = link.find("img")
                if img and img.get("alt"):
                    name = img["alt"].strip()

            if not name:
                continue

            player["name"] = name

            # Link
            href = link.get("href", "")
            if href:
                href = urljoin(base_url, href)
                player["link"] = href
                player["player_id"] = href.rstrip("/").split("/")[-1]

            # Image
            img = link.find("img")
            if img and img.get("src"):
                img_url = img["src"]
                if not img_url.startswith("http"):
                    img_url = urljoin(base_url, img_url)
                player["image_url"] = img_url
                if img.get("alt"):
                    player["alt_text"] = img["alt"].strip()

            players_data.append(player)
            print(f"✓ Found: {name}")

        except Exception:
            continue

    # REMOVE DUPLICATES
    unique = []
    seen = set()
    for p in players_data:
        if p["name"] not in seen:
            seen.add(p["name"])
            unique.append(p)

    players_data = unique

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    print(f"Total unique players: {len(players_data)}")
    print("=" * 60)

    # 🔥 FORCE SAVE FILES (NO CONDITIONS)

    # JSON
    with open("bcci_players.json", "w", encoding="utf-8") as f:
        json.dump(players_data, f, indent=2, ensure_ascii=False)
    print("✅ bcci_players.json SAVED")

    # CSV
    if players_data:
        with open("bcci_players.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=players_data[0].keys())
            writer.writeheader()
            writer.writerows(players_data)
        print("✅ bcci_players.csv SAVED")

    # DEBUG: SHOW FILES
    print("\nFiles in current directory:")
    print(os.listdir("."))

    return players_data


if __name__ == "__main__":
    print("BCCI.tv Player Scraper")
    print("=" * 50)

    players = scrape_bcci_players()

    if players:
        print(f"\n🎉 SUCCESS: {len(players)} players scraped")
        for i, p in enumerate(players[:5], 1):
            print(f"{i}. {p['name']} → {p.get('link')}")
    else:
        print("\n❌ No players found")
