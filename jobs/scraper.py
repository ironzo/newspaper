import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import time
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_24h_posts(channel_username):
    base_url = f"https://t.me/s/{channel_username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    all_posts = []
    
    current_url = base_url
    
    while True:
        response = requests.get(current_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Grab all message wraps
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        
        if not messages:
            print("No more messages found.")
            break

        batch_posts = []
        oldest_id = None

        first_div = messages[0].find('div', class_='tgme_widget_message')
        if first_div and first_div.has_attr('data-post'):
            oldest_id = first_div['data-post'].split('/')[-1]

        for msg in messages:
            
            time_element = msg.find('time', class_='time')
            text_element = msg.find('div', class_='tgme_widget_message_text')
            
            if time_element:
                post_date = datetime.fromisoformat(time_element['datetime']).astimezone(timezone.utc)
                
                if post_date >= cutoff_time:
                    text = text_element.get_text(separator="\n").strip() if text_element else "[media]"
                    batch_posts.append({
                        "date": post_date,
                        "text": text
                    })
        
        all_posts.extend(batch_posts)
        

        newest_msg_in_batch = messages[-1].find('time', class_='time')
        if newest_msg_in_batch:
            newest_date_in_batch = datetime.fromisoformat(newest_msg_in_batch['datetime']).astimezone(timezone.utc)
            
            if newest_date_in_batch >= cutoff_time and oldest_id:
                # Construct URL for the PREVIOUS batch
                current_url = f"{base_url}?before={oldest_id}"
                print(f"Moving to previous batch (before ID {oldest_id})...")
                time.sleep(1) # Be nice to Telegram's servers
                continue
        
        break

    all_posts = sorted(all_posts, key=lambda x: x['date'], reverse=True)
    return all_posts

def scrape_news():
    all_posts = []
    with open(os.path.join(BASE_DIR, "telegram_channels.md"), "r", encoding="utf-8") as f:
        channels = f.readlines()
    for channel in channels:
        channel_posts = f"## Channel Name: {channel}\n"
        channel = channel.strip()
        if channel:
            posts = get_24h_posts(channel)
            print(f"Found {len(posts)} posts for {channel}")
            for p in posts:
                channel_posts += f"### [{p['date']}] {p['text']}\n"
                print(f"[{p['date']}] {p['text'][:100]}...")
        all_posts.append(channel_posts)
    with open(os.path.join(BASE_DIR, "temp_storage", "raw_news.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(all_posts)) 