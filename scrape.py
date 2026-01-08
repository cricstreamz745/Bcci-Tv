import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import json
import time

def scrape_bcci_players():
    base_url = "https://www.bcci.tv"
    target_url = "https://www.bcci.tv/international/men/videos/player"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print(f"Fetching data from: {target_url}")
        response = requests.get(target_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        players_data = []
        
        # Find all player anchor tags with onclick="click_player(this)"
        player_links = soup.find_all('a', onclick="click_player(this)")
        
        print(f"Found {len(player_links)} player links with onclick attribute")
        
        for link in player_links:
            try:
                player_info = {}
                
                # Extract player name from data-player_name attribute
                player_name = link.get('data-player_name', '').strip()
                if player_name:
                    player_info['name'] = player_name
                else:
                    # Fallback: get name from alt text of image
                    img_tag = link.find('img')
                    if img_tag and img_tag.get('alt'):
                        player_info['name'] = img_tag['alt'].strip()
                
                # Extract player link from href attribute
                player_href = link.get('href', '')
                if player_href:
                    # Make URL absolute if relative
                    if not player_href.startswith('http'):
                        player_href = urljoin(base_url, player_href)
                    player_info['link'] = player_href
                
                # Extract player ID from the link (last part of URL after slash)
                if player_href:
                    parts = player_href.rstrip('/').split('/')
                    if parts:
                        player_info['player_id'] = parts[-1]
                
                # Extract image URL
                img_tag = link.find('img')
                if img_tag and img_tag.get('src'):
                    img_src = img_tag['src'].strip()
                    # Make image URL absolute if relative
                    if img_src and not img_src.startswith('http'):
                        img_src = urljoin(base_url, img_src)
                    player_info['image_url'] = img_src
                    
                    # Also get alt text if available
                    if img_tag.get('alt'):
                        player_info['alt_text'] = img_tag['alt'].strip()
                
                # Extract any other data attributes
                for attr, value in link.attrs.items():
                    if attr.startswith('data-'):
                        player_info[attr] = value
                
                # Only add if we have a name
                if 'name' in player_info:
                    players_data.append(player_info)
                    print(f"✓ Found: {player_info['name']}")
                
            except Exception as e:
                print(f"Error processing player link: {e}")
                continue
        
        # Alternative approach if the above doesn't work
        if not players_data:
            print("Trying alternative search methods...")
            
            # Look for all anchor tags containing player links
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if '/players/' in href or '/player/' in href:
                    try:
                        player_info = {}
                        
                        # Get name from img alt or link text
                        img_tag = link.find('img')
                        if img_tag and img_tag.get('alt'):
                            player_info['name'] = img_tag['alt'].strip()
                        else:
                            # Try to extract name from href
                            name_from_href = href.split('/')[-2].replace('-', ' ').title()
                            player_info['name'] = name_from_href
                        
                        # Make URL absolute
                        player_info['link'] = urljoin(base_url, href)
                        
                        # Get image
                        if img_tag and img_tag.get('src'):
                            img_src = img_tag['src'].strip()
                            if not img_src.startswith('http'):
                                img_src = urljoin(base_url, img_src)
                            player_info['image_url'] = img_src
                        
                        players_data.append(player_info)
                        print(f"✓ Found via alternative: {player_info['name']}")
                        
                    except Exception as e:
                        continue
        
        # Remove duplicates based on player name
        unique_players = []
        seen_names = set()
        for player in players_data:
            name = player.get('name')
            if name and name not in seen_names:
                seen_names.add(name)
                unique_players.append(player)
        
        players_data = unique_players
        
        # Display results
        print(f"\n{'='*60}")
        print(f"SCRAPING COMPLETE")
        print(f"{'='*60}")
        print(f"Total unique players found: {len(players_data)}")
        print(f"{'='*60}")
        
        for i, player in enumerate(players_data, 1):
            print(f"\n{i}. {player.get('name', 'Unknown')}")
            print(f"   ID: {player.get('player_id', 'N/A')}")
            print(f"   Link: {player.get('link', 'N/A')}")
            print(f"   Image: {player.get('image_url', 'No image')}")
            if player.get('alt_text'):
                print(f"   Alt Text: {player.get('alt_text')}")
        
        # Save to CSV
        if players_data:
            with open('bcci_players.csv', 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'player_id', 'link', 'image_url', 'alt_text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(players_data)
            print(f"\n✅ Data saved to 'bcci_players.csv'")
        
        # Save to JSON for structured data
        with open('bcci_players.json', 'w', encoding='utf-8') as jsonfile:
            json.dump(players_data, jsonfile, indent=2, ensure_ascii=False)
        print(f"✅ Data also saved to 'bcci_players.json'")
        
        return players_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching the page: {e}")
        return []
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return []

def get_individual_player_details(player_url):
    """Fetch additional details for a specific player"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"\nFetching details from: {player_url}")
        response = requests.get(player_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract page title
        title = soup.find('title')
        if title:
            print(f"Page Title: {title.get_text(strip=True)}")
        
        # You can add more specific extraction logic here
        # For example, find video count, recent videos, etc.
        
        return True
        
    except Exception as e:
        print(f"Error fetching player details: {e}")
        return False

if __name__ == "__main__":
    print("BCCI.tv Player Scraper")
    print("=" * 50)
    
    # Scrape all players
    players = scrape_bcci_players()
    
    # Optionally fetch details for first few players
    if players:
        print(f"\n{'='*60}")
        print("FETCHING DETAILS FOR FIRST 3 PLAYERS")
        print(f"{'='*60}")
        
        for i, player in enumerate(players[:3]):
            print(f"\n{i+1}. Getting details for: {player['name']}")
            get_individual_player_details(player['link'])
            time.sleep(1)  # Be polite to the server
        
        print(f"\n{'='*60}")
        print("SCRIPT COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}")
        
        # Show summary
        print(f"\n📊 SUMMARY:")
        print(f"   Total Players: {len(players)}")
        print(f"   CSV File: bcci_players.csv")
        print(f"   JSON File: bcci_players.json")
        
        # Show sample players
        print(f"\n👤 SAMPLE PLAYERS:")
        for i, player in enumerate(players[:5]):
            print(f"   {i+1}. {player['name']} → {player['link']}")
    else:
        print("\n❌ No players were found. Possible reasons:")
        print("   1. The website structure may have changed")
        print("   2. The page requires JavaScript rendering")
        print("   3. The URL might be different")
        print("\n💡 TROUBLESHOOTING:")
        print("   - Check if the URL is correct")
        print("   - Try using Selenium for JavaScript-rendered content")
        print("   - Inspect the page HTML to find correct selectors")
