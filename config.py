import os

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# CoinGecko
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Paper trading
INITIAL_BALANCE = 10000  # 10 000$ fictifs
MAX_TRADE_PERCENT = 0.05  # max 5% du portefeuille par trade
STOP_LOSS_PERCENT = 0.08  # stop loss à -8%
TAKE_PROFIT_PERCENT = 0.20  # take profit à +20%
MAX_DAILY_LOSS_PERCENT = 0.10  # coupe tout si -10% dans la journée

# Scanner
SCAN_INTERVAL_SECONDS = 30  # scan toutes les 30 secondes
VOLUME_SPIKE_THRESHOLD = 3.0  # volume x3 = signal fort
PRICE_CHANGE_THRESHOLD = 10.0  # +10% en 1h = signal fort

# Marchés surveillés
TRACKED_COINS = [
    "bitcoin", "ethereum", "solana",
    "pepe", "dogecoin", "shiba-inu",
    "bonk", "floki", "wojak"
]

# Or et matières premières (via API alternative)
GOLD_SYMBOL = "XAU"
