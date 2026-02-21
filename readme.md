## CSFloat Discord Notifications Bot

### Overview
Python script that retrieves CS item listings from the CSFloat API, processes the data, and posts relevant listings to a Discord channel using embeds.


## Usage

1. **Clone Git repo**
    ```bash
    git clone https://github.com/annadeva/pycsfloat_bot.git
    ```

2. **Create venv**
    ```bash
    python -m venv venv
    source venv/Scripts/activate
    pip install -r requirements.txt 
    ```

4. **Populate env with API keys**

    Using env.example template create .env file with your own csfloat and discord keys.

3. **Running the script**
    ```bash
    python main/csfloat_bot.py
    ```