import os
import requests
import pandas as pd
from dotenv import load_dotenv
from utils.logging_config import setup_logging

logger = setup_logging()

load_dotenv()
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")


def send_discord_embed(embed: dict) -> None:
    """Send a Discord embed to the specified webhook URL."""
    data = {"embeds": [embed]}
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code != 204:
            logger.info(f"Failed to send embed to Discord: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logger.error(f"An error occurred while sending embed to Discord: {e}")

def create_discord_embed(listing: dict) -> dict:
    """Create a Discord embed dictionary based on the listing details."""
    embed = {
        "title": f"{listing['item_name']} - ${listing['listing_price']:.2f}",
        "url": listing['listing_url'],
        "thumbnail": {"url": listing['screenshot_url']},
        "color": get_embed_color(listing['rarity_name']),
        "fields": [
            {"name": "Estimated Price", "value": f"${listing['estimated_price']:.2f}", "inline": True},
            {"name": "Float Value", "value": f"{listing['float_value']:.6f}", "inline": True},
            {"name": "Float Factor", "value": f"{listing['float_factor']:.2f}", "inline": True},
            {"name": "Global Listings", "value": str(listing['global_listings']), "inline": True},
            {"name": "Min Bargain Price", "value": f"${listing['min_bargain_price']:.2f}", "inline": True},
            {"name": "Max Bargain Discount", "value": f"{listing['max_bargain_discount']:.2f}%", "inline": True}
        ],
        "footer": {"text": f"Listed at {listing['created_at']}"},
    }
    return embed

def get_embed_color(rarity_name: str) -> int:
    color_dict = {"Consumer": "#847b6e", "Industrial": "#5e98d9", 
              "Mil-Spec": "#4b69ff", "Restricted": "#8847ff", 
              "Classified": "#d32ce6", "Covert": "#eb4b4b", 
              "Contraband": "#e4ae39"}
    
    # update this to return int color if rarity name contains any of the keys in color_dict, otherwise return white
    for key in color_dict:
        if key.lower() in rarity_name.lower():
            return int(color_dict[key].lstrip('#'), 16)
    return int("FFFFFF", 16)

def post_listings_to_discord(df: pd.DataFrame) -> None:
    """Post the filtered listings from passed DataFrame to Discord using embeds."""
    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not set in environment")
    for _, listing in df.iterrows():
        embed = create_discord_embed(listing)
        send_discord_embed(embed)
    logger.info(f"Posted {len(df)} listings to Discord")
