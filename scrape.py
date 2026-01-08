import requests
import json
import csv

API_URL = "https://www.bcci.tv/api/videos/players?page={}"

def scrape_all_players():
    all_players = []
    page = 1

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    while True:
        url = API_URL.format(page)
        print(f"Fetching page {page}...")

        r = requests.get(url, headers=headers, timeout=20)

        if r.status_code != 200:
            break

        data = r.json()
        players = data.get("players", [])

        if not players:
            break

        for p in players:
            all_players.append({
                "name": p.get("title"),
                "player_id": p.get("nid"),
                "link": "https://www.bcci.tv" + p.get("path", ""),
                "image_url": p.get("image", "")
            })

        if not data.get("has_more"):
            break

        page += 1

    # SAVE JSON (GUARANTEED)
    with open("bcci_players.json", "w", encoding="utf-8") as f:
        json.dump(all_players, f, indent=2, ensure_ascii=False)

    # SAVE CSV
    with open("bcci_players.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_players[0].keys())
        writer.writeheader()
        writer.writerows(all_players)

    print(f"\n✅ TOTAL PLAYERS SCRAPED: {len(all_players)}")
    return all_players


if __name__ == "__main__":
    scrape_all_players()
