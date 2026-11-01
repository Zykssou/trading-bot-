import os

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# CoinGecko
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Paper trading
INITIAL_BALANCE = 1000  # 1 000€ fictifs
MAX_TRADE_PERCENT = 0.05  # max 5% du portefeuille par trade
STOP_LOSS_PERCENT = 0.05  # stop loss à -5%
TAKE_PROFIT_PERCENT = 0.10  # take profit à +10%
MAX_DAILY_LOSS_PERCENT = 0.10  # coupe tout si -10% dans la journée

# Scanner
SCAN_INTERVAL_SECONDS = 600  # scan toutes les 10 minutes
VOLUME_SPIKE_THRESHOLD = 1.5  # volume x1.5 = signal fort
PRICE_CHANGE_THRESHOLD = 1.0  # +1% en 1h = signal fort

# Marchés surveillés
TRACKED_COINS = [
    "bitcoin", "ethereum", "solana", "bnb", "xrp",
    "cardano", "avalanche-2", "chainlink",
    "pepe", "shiba-inu", "floki", "bonk",
    "wojak", "sui", "injective-protocol", "render-token", "fetch-ai"
]

# Coins autorisés à l'achat (volatile = meilleur win rate)
BUYABLE_COINS = [
    "pepe", "shiba-inu", "floki", "bonk", "wojak",
    "sui", "injective-protocol", "render-token", "fetch-ai", "solana"
]

# Catégories pour anti-corrélation
LARGE_CAPS = ["bitcoin", "ethereum", "bnb", "xrp", "cardano", "solana", "avalanche-2", "chainlink"]
MEME_COINS = ["pepe", "shiba-inu", "floki", "bonk", "wojak"]

# Mapping CoinGecko ID → symbole Binance
BINANCE_SYMBOLS = {
    "bitcoin":            "BTCUSDT",
    "ethereum":           "ETHUSDT",
    "solana":             "SOLUSDT",
    "bnb":                "BNBUSDT",
    "xrp":                "XRPUSDT",
    "cardano":            "ADAUSDT",
    "avalanche-2":        "AVAXUSDT",
    "chainlink":          "LINKUSDT",
    "pepe":               "PEPEUSDT",
    "shiba-inu":          "SHIBUSDT",
    "floki":              "FLOKIUSDT",
    "bonk":               "BONKUSDT",
    "wojak":              "WOJAKUSDT",
    "sui":                "SUIUSDT",
    "injective-protocol": "INJUSDT",
    "render-token":       "RENDERUSDT",
    "fetch-ai":           "FETUSDT",
}

# Stratégie par coin — seuil entrée, stop-loss, take-profit
COIN_PROFILES = {
    "bitcoin":            {"threshold": 3.0, "stop_loss": 0.03, "take_profit": 0.06},
    "ethereum":           {"threshold": 3.0, "stop_loss": 0.03, "take_profit": 0.06},
    "solana":             {"threshold": 2.0, "stop_loss": 0.04, "take_profit": 0.08},
    "bnb":                {"threshold": 2.0, "stop_loss": 0.04, "take_profit": 0.08},
    "xrp":                {"threshold": 2.0, "stop_loss": 0.04, "take_profit": 0.08},
    "cardano":            {"threshold": 2.0, "stop_loss": 0.04, "take_profit": 0.08},
    "avalanche-2":        {"threshold": 2.0, "stop_loss": 0.04, "take_profit": 0.08},
    "chainlink":          {"threshold": 2.0, "stop_loss": 0.04, "take_profit": 0.08},
    "sui":                {"threshold": 1.5, "stop_loss": 0.05, "take_profit": 0.10},
    "injective-protocol": {"threshold": 1.5, "stop_loss": 0.05, "take_profit": 0.10},
    "render-token":       {"threshold": 1.5, "stop_loss": 0.05, "take_profit": 0.10},
    "fetch-ai":           {"threshold": 1.5, "stop_loss": 0.05, "take_profit": 0.10},
    "pepe":               {"threshold": 1.0, "stop_loss": 0.05, "take_profit": 0.10},
    "shiba-inu":          {"threshold": 1.0, "stop_loss": 0.05, "take_profit": 0.10},
    "floki":              {"threshold": 1.0, "stop_loss": 0.05, "take_profit": 0.10},
    "bonk":               {"threshold": 0.8, "stop_loss": 0.05, "take_profit": 0.10},
    "wojak":              {"threshold": 0.8, "stop_loss": 0.05, "take_profit": 0.10},
}
