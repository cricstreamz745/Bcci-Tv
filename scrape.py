import requests
import json
import csv
import sys

API_URL = "https://www.bcci.tv/api/videos/players?page={}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bcci.tv/",
    "Origin": "https://www.bcci.tv",
}

def scrape_all_players():
    all_players = []
    page = 1

    while True:
        url = API_URL.format(page)
        print(f"\nFetching page {page}: {url}")

        r = requests.get(url, headers=HEADERS, timeout=20)

        print("Status:", r.status_code)
        print("Content-Type:", r.headers.get("content-type"))

        # ❌ BLOCKED / INVALID RESPONSE
        if r.status_code != 200:
            print("Stopping: non-200 response")
            break

        # ❌ NOT JSON
        if "application/json" not in r.headers.get("content-type", ""):
            print("Stopping: response is not JSON")
            print("Response preview:")
            print(r.text[:300])
            break

        try:
            data = r.json()
        except Exception as e:
            print("JSON parse failed:", e)
            print("Raw response:")
            print(r.text[:300])
            break

        players = data.get("players", [])
        print("Players on page:", len(players))

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
            print("No more pages")
            break

        page += 1

    # 🔥 FORCE SAVE EVEN IF PARTIAL
    with open("bcci_players.json", "w", encoding="utf-8") as f:
        json.dump(all_players, f, indent=2, ensure_ascii=False)

    if all_players:
        with open("bcci_players.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_players[0].keys())
            writer.writeheader()
            writer.writerows(all_players)

    print("\n✅ TOTAL PLAYERS SAVED:", len(all_players))
    return all_players


if __name__ == "__main__":
    scrape_all_players()
