from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time
import csv
import json
from urllib.parse import urljoin

def scrape_bcci_players_with_selenium():
    base_url = "https://www.bcci.tv"
    target_url = "https://www.bcci.tv/international/men/videos/player"
    
    print("Initializing Selenium WebDriver...")
    
    # Setup Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Uncomment to run in headless mode (no browser window)
    # options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"Loading page: {target_url}")
        driver.get(target_url)
        time.sleep(3)  # Initial wait for page load
        
        players_data = []
        player_set = set()  # To track unique players
        load_more_attempts = 0
        max_load_more_attempts = 10  # Safety limit
        
        print("Looking for players and 'Load More' button...")
        
        while load_more_attempts < max_load_more_attempts:
            # Get current page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all player links
            player_links = soup.find_all('a', onclick="click_player(this)")
            
            current_batch_count = 0
            for link in player_links:
                try:
                    player_info = extract_player_info(link, base_url)
                    
                    if player_info and player_info.get('name') and player_info['name'] not in player_set:
                        player_set.add(player_info['name'])
                        players_data.append(player_info)
                        current_batch_count += 1
                        print(f"  Found: {player_info['name']}")
                        
                except Exception as e:
                    continue
            
            print(f"Batch {load_more_attempts + 1}: Found {current_batch_count} new players")
            print(f"Total so far: {len(players_data)} players")
            
            # Try to find and click "Load More" button
            try:
                # Look for load more button by various possible selectors
                load_selectors = [
                    "button.load-more",
                    "button:contains('Load More')",
                    ".load-more-btn",
                    "#load-more",
                    "button[onclick*='load']",
                    "a.load-more",
                    "a:contains('Load More')",
                    ".btn-load-more",
                ]
                
                load_more_button = None
                for selector in load_selectors:
                    try:
                        load_more_button = driver.find_element(By.CSS_SELECTOR, selector)
                        if load_more_button and load_more_button.is_displayed():
                            break
                    except:
                        continue
                
                if not load_more_button:
                    # Try by text content
                    try:
                        load_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Load More')]")
                    except:
                        try:
                            load_more_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Load More')]")
                        except:
                            load_more_button = None
                
                if load_more_button and load_more_button.is_displayed():
                    print(f"\nClicking 'Load More' button (Attempt {load_more_attempts + 1})...")
                    
                    # Scroll to the button
                    driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                    time.sleep(1)
                    
                    # Click the button
                    driver.execute_script("arguments[0].click();", load_more_button)
                    
                    # Wait for new content to load
                    time.sleep(3)
                    
                    # Wait for new players to appear
                    try:
                        WebDriverWait(driver, 10).until(
                            lambda d: len(d.find_elements(By.CSS_SELECTOR, "a[onclick='click_player(this)']")) > len(player_links)
                        )
                    except TimeoutException:
                        print("Timeout waiting for new players to load, but continuing...")
                    
                    load_more_attempts += 1
                else:
                    print("\nNo more 'Load More' button found. Stopping.")
                    break
                    
            except Exception as e:
                print(f"Error clicking load more button: {e}")
                break
        
        print(f"\nScraping complete! Total players found: {len(players_data)}")
        
        # Display results
        display_results(players_data)
        
        # Save data
        save_data(players_data)
        
        return players_data
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        return []
    finally:
        print("\nClosing browser...")
        driver.quit()

def extract_player_info(link, base_url):
    """Extract player information from a link element"""
    player_info = {}
    
    # Extract player name
    player_name = link.get('data-player_name', '').strip()
    if not player_name:
        img_tag = link.find('img')
        if img_tag and img_tag.get('alt'):
            player_name = img_tag['alt'].strip()
    
    if not player_name:
        return None
    
    player_info['name'] = player_name
    
    # Extract player link
    player_href = link.get('href', '')
    if player_href:
        if not player_href.startswith('http'):
            player_href = urljoin(base_url, player_href)
        player_info['link'] = player_href
        
        # Extract player ID
        parts = player_href.rstrip('/').split('/')
        if parts:
            player_info['player_id'] = parts[-1]
    
    # Extract image URL
    img_tag = link.find('img')
    if img_tag and img_tag.get('src'):
        img_src = img_tag['src'].strip()
        if img_src and not img_src.startswith('http'):
            img_src = urljoin(base_url, img_src)
        player_info['image_url'] = img_src
        
        if img_tag.get('alt'):
            player_info['alt_text'] = img_tag['alt'].strip()
    
    # Extract other data attributes
    for attr, value in link.attrs.items():
        if attr.startswith('data-'):
            player_info[attr] = value
    
    return player_info

def display_results(players_data):
    """Display the scraped results"""
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total players found: {len(players_data)}")
    print(f"{'='*60}")
    
    for i, player in enumerate(players_data[:10], 1):  # Show first 10
        print(f"\n{i}. {player.get('name', 'Unknown')}")
        print(f"   ID: {player.get('player_id', 'N/A')}")
        print(f"   Link: {player.get('link', 'N/A')}")
    
    if len(players_data) > 10:
        print(f"\n... and {len(players_data) - 10} more players")

def save_data(players_data):
    """Save scraped data to files"""
    if not players_data:
        print("No data to save!")
        return
    
    # Save to CSV
    csv_filename = 'bcci_all_players.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'player_id', 'link', 'image_url', 'alt_text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(players_data)
    print(f"\n✅ Data saved to '{csv_filename}'")
    
    # Save to JSON
    json_filename = 'bcci_all_players.json'
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(players_data, jsonfile, indent=2, ensure_ascii=False)
    print(f"✅ Data also saved to '{json_filename}'")
    
    # Save a simple text list
    txt_filename = 'bcci_players_list.txt'
    with open(txt_filename, 'w', encoding='utf-8') as txtfile:
        txtfile.write("BCCI.tv Players List\n")
        txtfile.write("=" * 50 + "\n\n")
        for i, player in enumerate(players_data, 1):
            txtfile.write(f"{i}. {player['name']}\n")
            txtfile.write(f"   Link: {player.get('link', 'N/A')}\n")
            txtfile.write(f"   ID: {player.get('player_id', 'N/A')}\n\n")
    print(f"✅ Player list saved to '{txt_filename}'")

if __name__ == "__main__":
    print("BCCI.tv Player Scraper with Load More Support")
    print("=" * 60)
    print("This script will:")
    print("1. Open the players page")
    print("2. Click 'Load More' button multiple times")
    print("3. Extract all players (not just first 20)")
    print("=" * 60)
    
    players = scrape_bcci_players_with_selenium()
    
    if players:
        print(f"\n🎉 Successfully scraped {len(players)} players!")
        print(f"\n📊 First few players:")
        for i, player in enumerate(players[:5], 1):
            print(f"   {i}. {player['name']}")
        
        if len(players) >= 34:
            print(f"\n✅ Found all {len(players)} players (including those behind 'Load More')")
        else:
            print(f"\n⚠️  Found {len(players)} players, but expected 34+")
            print("   The 'Load More' button might have different selectors")
    else:
        print("\n❌ No players were found.")
