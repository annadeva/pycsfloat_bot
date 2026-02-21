"""
CSFloat Bot: A Python script that retrieves CS item listings from the CSFloat API,
processes the data, and posts relevant listings to a Discord channel using embeds.
The bot performs the following steps:
1. Retrieves listing data from the CSFloat API. 
2. Cleans and transforms the raw data by extracting relevant details, converting price formats, and reordering columns.
3. Filters the listings to keep only relevant ones based on type, float factor, and estimated price criteria.
4. Posts the filtered listings to a Discord channel using embeds for better presentation.
"""

import pandas as pd
from csfloat_api import make_listing_request
from discord_webhook import post_listings_to_discord

from utils.save_data import save_df_daily
from utils.logging_config import setup_logging

logger = setup_logging()


def create_screenshot_url(icon_url: str) -> str:
    return f"https://community.akamai.steamstatic.com/economy/image/{icon_url}"

def create_listing_url(listing_id: str) -> str:
    return f"https://csfloat.com/item/{listing_id}"

def convert_price_to_dollars(price_in_cents: int) -> float:
    return price_in_cents / 100.0

def get_item_details(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract item details from the nested "item" column and create new columns for each detail. 
    Also creates a screenshot URL based on the icon URL.
    """
    df["item_name"] = df["item"].apply(lambda x: x['market_hash_name'] if 'market_hash_name' in x else None)
    df["float_value"] = df["item"].apply(lambda x: x['float_value'] if 'float_value' in x else None)
    df["rarity_name"] = df["item"].apply(lambda x: x['rarity_name'] if 'rarity_name' in x else None)
    df['inspect_link'] = df["item"].apply(lambda x: x['inspect_link'] if 'inspect_link' in x else None)
    df['paint_seed'] = df["item"].apply(lambda x: x['paint_seed'] if 'paint_seed' in x else None) 
    df['type'] = df["item"].apply(lambda x: x['type'] if 'type' in x else None) 
    df['icon_url'] = df["item"].apply(lambda x: x['icon_url'] if 'icon_url' in x else None)
    df['screenshot_url'] = df['icon_url'].apply(create_screenshot_url)

    df = df.drop(columns=['item', 'icon_url'], axis=1)
    return df

def get_reference_details(df: pd.DataFrame) -> pd.DataFrame:
    """Extract reference details from the nested "reference" column and create new columns for each detail."""
    # get float factor if exists
    df['float_factor'] = df["reference"].apply(lambda x: x['float_factor'] if 'float_factor' in x else None)
    df['predicted_price'] = df["reference"].apply(lambda x: x['predicted_price'] if 'predicted_price' in x else None)
    df['quantity'] = df["reference"].apply(lambda x: x['quantity'])

    # Drop the original "reference" column
    df = df.drop(columns=['reference'], axis=1)
    return df

def get_seller_details(df: pd.DataFrame) -> pd.DataFrame:
    """Extract seller details from the nested "seller" column and create new columns for each detail."""
    df['median_trade_time'] = df["seller"].apply(lambda x: x['statistics']['median_trade_time'] 
                                                 if 'statistics' in x and 'median_trade_time' in x['statistics'] else None)
    df['total_trades'] = df["seller"].apply(lambda x: x['statistics']['total_trades'] 
                                            if 'statistics' in x and 'total_trades' in x['statistics'] else None)

    # Drop the original "seller" column
    df = df.drop(columns=['seller'], axis=1)
    return df


def clean_listings_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and transform the raw listings DataFrame by extracting relevant details, converting price formats, and reordering columns."""
    keep_columns = ['id', 'created_at', 'seller', 'price', 'reference',
                    'item', 'min_offer_price', 'max_offer_discount']
    df = df[keep_columns].copy()
    df = get_item_details(df)
    df = get_reference_details(df)
    df = get_seller_details(df)
    
    # Column renaming for clarity
    df = df.rename(columns={
        'id': 'listing_id',
        'price': 'listing_price',
        'min_offer_price': 'min_bargain_price',
        'max_offer_discount': 'max_bargain_discount',
        'predicted_price': 'estimated_price',
        'quantity': 'global_listings',
        'median_trade_time': 'seller_median_trade_time',
        'total_trades': 'seller_total_trades'
    })

    df['listing_url'] = df['listing_id'].apply(create_listing_url)

    # Convert price columns from cents to dollars
    df['listing_price'] = df['listing_price'].apply(convert_price_to_dollars)
    df['estimated_price'] = df['estimated_price'].apply(convert_price_to_dollars)
    df['min_bargain_price'] = df['min_bargain_price'].apply(convert_price_to_dollars)

    columns_to_move = ['item_name', 'listing_price', 'estimated_price', 'float_factor', 'float_value', 'listing_url']
    new_order = columns_to_move + [c for c in df.columns if c not in columns_to_move]
    df = df[new_order]
    return df.sort_values(by='created_at', ascending=False, inplace=False)

def handle_missing_estimated_price(row: dict) -> str:
    if row['estimated_price'] is None and row['type'] == 'agent':
        return "Keep"
    elif row['estimated_price'] is None:
        return "Drop"
    elif row['estimated_price'] < row['listing_price']:
        return "Drop"
    elif row['estimated_price'] == row['listing_price'] and row['max_bargain_discount'] < 300.0:
        return "Drop"
    else:
        return "Keep"
     
def filter_listings_df(df: pd.DataFrame) -> pd.DataFrame:
    """Filter the listings DataFrame to keep only relevant listings based on type, float factor, and estimated price criteria."""
    logger.info(f"Number of listings before filtering: {len(df)}")
    df = df[df['type'].isin(['skin', 'agent'])]
    df = df[df['float_factor'] >= 0.95]

    df["keep_listing"] = df.apply(handle_missing_estimated_price, axis=1)
    df = df[df['keep_listing'] != "Drop"]
    df = df.drop(columns=['keep_listing', 'type'], axis=1)

    logger.info(f"Number of listings after filtering: {len(df)}")
    return df


if __name__ == "__main__":
    df = make_listing_request()
    if df is None or df.empty:
        logger.warning("No listings data retrieved from API.")
        raise RuntimeError("No listings data retrieved from API.")
    
    df = clean_listings_df(df)
    df = filter_listings_df(df)
    post_listings_to_discord(df)
    save_df_daily(df)
