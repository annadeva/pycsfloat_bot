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

def create_suggested_price(listing: dict)-> str:
    min_bargain = listing['min_bargain_price']
    est_price = listing['estimated_price']
    base_str = f"Buy at (-5%): ${est_price - (est_price*0.05):.2f}\nBuy at (-6%): ${est_price - (est_price*0.06):.2f}"
    
    if min_bargain > (est_price - (est_price*0.07)): # when suggested price %7 is lower than min bargain
        return base_str
    elif min_bargain > (est_price - (est_price*0.08)): # when suggested price %8 is lower than min bargain
        return base_str + f"\nBuy at (-7%): ${est_price - (est_price*0.07):.2f}"
    else: # all are higher than min bargain price
        return base_str + f"\nBuy at (-7%): ${est_price - (est_price*0.07):.2f}\nBuy at (-8%): ${est_price - (est_price*0.08):.2f}"

def create_discord_embed(listing: dict) -> dict:
    """Create a Discord embed dictionary based on the listing details."""
    """In the title, add the percentage discount from the estimated price to the listing price, and in the fields, add the profit margin if bought at listed price and sold at estimated price, and if bought at min bargain price and sold at estimated price."""
    discount = ((listing['estimated_price'] - listing['listing_price']) / listing['estimated_price'] * 100) if listing['estimated_price'] > 0 else 0
    embed = {
        "title": f"{listing['item_name']} - ${listing['listing_price']:.2f} ({discount:.2f}% off)",
        "url": listing['listing_url'],
        "thumbnail": {"url": listing['screenshot_url']},
        "color": get_embed_color(listing['rarity_name']),
        "fields": [
            {"name": "Float Value", "value": f"{listing['float_value']:.6f}", "inline": True},
            {"name": "Paint Seed", "value": str(listing['paint_seed']), "inline": True},
            {"name": "Estimated Price", "value": f"${listing['estimated_price']:.2f}", "inline": True},
            {"name": "Min Bargain Price", "value": f"${listing['min_bargain_price']:.2f}", "inline": True},
            {"name": "Max Bargain Discount", "value": f"{listing['max_bargain_discount']:.2f}%", "inline": True},
            {"name": "Global Listings", "value": str(listing['global_listings']), "inline": True},
            # Calculated profit margins and suggested buy price
            {
                "name": "Profit Margins", 
                "value": f"""${listing['listing_price']:.2f} (listed price) + 5% = ${listing['listing_price'] * 1.05:.2f}\n${listing['min_bargain_price']:.2f} (min bargain price) + 5% = ${listing['min_bargain_price'] * 1.05:.2f}""", 
                "inline": False
            },
            {"name": "Suggested Buy Prices (estimated price - X%)", "value": create_suggested_price(listing),"inline": True}
        ],
        #"footer": {"text": f"Listed at {listing['created_at']}"},
    }
    return embed

# def create_discord_embed(listing: dict) -> dict:
#     """Create a Discord embed dictionary based on the listing details."""
#     embed = {
#         "title": f"{listing['item_name']} - ${listing['listing_price']:.2f}",
#         "url": listing['listing_url'],
#         "thumbnail": {"url": listing['screenshot_url']},
#         "color": get_embed_color(listing['rarity_name']),
#         "fields": [
#             {"name": "Float Value", "value": f"{listing['float_value']:.6f}", "inline": True},
#             {"name": "Paint Seed", "value": str(listing['paint_seed']), "inline": True},
#             {"name": "Estimated Price", "value": f"${listing['estimated_price']:.2f}", "inline": True},
#             {"name": "Min Bargain Price", "value": f"${listing['min_bargain_price']:.2f}", "inline": True},
#             {"name": "Max Bargain Discount", "value": f"{listing['max_bargain_discount']:.2f}%", "inline": True},
#             {"name": "Global Listings", "value": str(listing['global_listings']), "inline": True},
#             # Calculated profit margins and suggested buy price
#             {
#                 "name": "Profit Margins", 
#                 "value": f"""${listing['listing_price']:.2f} (listed price) + 5% = ${listing['listing_price'] * 1.05:.2f}\n${listing['min_bargain_price']:.2f} (min bargain price) + 5% = ${listing['min_bargain_price'] * 1.05:.2f}""", 
#                 "inline": False
#             },
#             {"name": "Suggested Buy Prices (estimated price - X%)", "value": create_suggested_price(listing),"inline": True}
#         ],
#         #"footer": {"text": f"Listed at {listing['created_at']}"},
#     }
#     return embed

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
