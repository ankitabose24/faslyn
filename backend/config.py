import os

def load_env_file():
    """Load variables from .env into os.environ (supports python-dotenv with standard-lib fallback)."""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            return True
    except Exception:
        pass

    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
            return True
    except Exception:
        pass
    return False

# Initialize environment variables from .env immediately on import
load_env_file()

BRICS_HUBS = {
    "🇮🇳 India — Odisha (Coastal Rice Belt)": {"lat": 20.2961, "lon": 85.8245, "zoom": 8},
    "🇧🇷 Brazil — Mato Grosso (Soy/Maize Belt)": {"lat": -12.6819, "lon": -56.9211, "zoom": 6},
    "🇿🇦 South Africa — Limpopo (Mixed Farming Belt)": {"lat": -23.4013, "lon": 29.4179, "zoom": 7},
    "🇷🇺 Russia — Krasnodar Krai (Black Earth Belt)": {"lat": 45.0355, "lon": 38.9753, "zoom": 7},
    "🇨🇳 China — Heilongjiang (Grain Belt)": {"lat": 47.3661, "lon": 129.9721, "zoom": 6},
}

LANGUAGES = {
    "Hindi": "hi-IN",
    "Odia": "or-IN",
    "Portuguese": "pt-BR",
    "Russian": "ru-RU",
    "Swahili": "sw-KE",
    "English": "en-US",
    "Mandarin": "zh-CN",
}

FIRST_HUB = list(BRICS_HUBS.values())[0]

REGIONAL_FIELDS = {
    "🇮🇳 India — Odisha (Coastal Rice Belt)": [
        {"name": "Field 01 (North)", "crop_en": "Rice (Paddy)", "crop_key": "rice", "area": "1.2 ha", "icon": "🌾", "stress_bias": 0.90},
        {"name": "Field 02 (East)", "crop_en": "Kharif Maize", "crop_key": "maize", "area": "0.8 ha", "icon": "🌽", "stress_bias": 0.68},
        {"name": "Field 03 (Lowland)", "crop_en": "Basmati Rice", "crop_key": "rice", "area": "1.1 ha", "icon": "🌾", "stress_bias": 0.58},
        {"name": "Field 04 (South)", "crop_en": "Vegetables", "crop_key": "veg", "area": "0.6 ha", "icon": "🥬", "stress_bias": 0.88},
    ],
    "🇧🇷 Brazil — Mato Grosso (Soy/Maize Belt)": [
        {"name": "Talhão 01 (Norte)", "crop_en": "Soja Precoce", "crop_key": "soy", "area": "45 ha", "icon": "🌱", "stress_bias": 0.95},
        {"name": "Talhão 02 (Pivô)", "crop_en": "Milho Safrinha", "crop_key": "maize", "area": "38 ha", "icon": "🌽", "stress_bias": 0.75},
        {"name": "Talhão 03 (Sul)", "crop_en": "Soja Cerrado", "crop_key": "soy", "area": "42 ha", "icon": "🌱", "stress_bias": 0.90},
        {"name": "Talhão 04 (Leste)", "crop_en": "Pastagem Rotacionada", "crop_key": "pasture", "area": "25 ha", "icon": "🌿", "stress_bias": 0.70},
        {"name": "Talhão 05 (Oeste)", "crop_en": "Algodão Safra", "crop_key": "cotton", "area": "20 ha", "icon": "☁️", "stress_bias": 0.80},
    ],
    "🇿🇦 South Africa — Limpopo (Mixed Farming Belt)": [
        {"name": "Sector A (North)", "crop_en": "White Maize", "crop_key": "maize", "area": "6.5 ha", "icon": "🌽", "stress_bias": 0.90},
        {"name": "Sector B (Central)", "crop_en": "Grain Sorghum", "crop_key": "sorghum", "area": "4.2 ha", "icon": "🌾", "stress_bias": 0.72},
        {"name": "Sector C (East)", "crop_en": "Sunflower", "crop_key": "sunflower", "area": "5.0 ha", "icon": "🌻", "stress_bias": 0.88},
        {"name": "Sector D (South)", "crop_en": "Groundnuts", "crop_key": "groundnut", "area": "3.1 ha", "icon": "🥜", "stress_bias": 0.65},
    ],
    "🇷🇺 Russia — Krasnodar Krai (Black Earth Belt)": [
        {"name": "Поле 01 (Север)", "crop_en": "Озимая пшеница", "crop_key": "wheat", "area": "65 ha", "icon": "🌾", "stress_bias": 0.92},
        {"name": "Поле 02 (Центр)", "crop_en": "Подсолнечник", "crop_key": "sunflower", "area": "45 ha", "icon": "🌻", "stress_bias": 0.80},
        {"name": "Поле 03 (Восток)", "crop_en": "Яровой ячмень", "crop_key": "barley", "area": "40 ha", "icon": "🌾", "stress_bias": 0.68},
        {"name": "Поле 04 (Юг)", "crop_en": "Сахарная свёкла", "crop_key": "beet", "area": "30 ha", "icon": "🪴", "stress_bias": 0.85},
        {"name": "Поле 05 (Запад)", "crop_en": "Зерновая кукуруза", "crop_key": "maize", "area": "35 ha", "icon": "🌽", "stress_bias": 0.75},
    ],
    "🇨🇳 China — Heilongjiang (Grain Belt)": [
        {"name": "1号地 (北部高产)", "crop_en": "大豆 (Soybean)", "crop_key": "soy", "area": "28 ha", "icon": "🌱", "stress_bias": 0.90},
        {"name": "2号地 (中部核心)", "crop_en": "玉米 (Field Corn)", "crop_key": "maize", "area": "35 ha", "icon": "🌽", "stress_bias": 0.85},
        {"name": "3号地 (水利灌区)", "crop_en": "优质粳稻 (Rice)", "crop_key": "rice", "area": "22 ha", "icon": "🌾", "stress_bias": 0.62},
        {"name": "4号地 (东部平原)", "crop_en": "春小麦 (Spring Wheat)", "crop_key": "wheat", "area": "18 ha", "icon": "🌾", "stress_bias": 0.78},
        {"name": "5号地 (有机轮作)", "crop_en": "马铃薯 (Potato)", "crop_key": "potato", "area": "15 ha", "icon": "🥔", "stress_bias": 0.92},
    ],
}

DEMO_PROFILES = [
    {
        "name": "Ramesh Kumar",
        "avatar": "RK",
        "role": "Smallholder Farmer",
        "id": "IN-OD-2026-4482",
        "phone": "+91 98765 43210",
        "region": "Odisha, India",
        "hub": "🇮🇳 India — Odisha (Coastal Rice Belt)",
        "crops": "Paddy Rice, Kharif Maize, Vegetables",
        "lang": "English",
        "flag": "🇮🇳",
        "badge": "Coastal Rice Belt",
    },
    {
        "name": "Maria Silva",
        "avatar": "MS",
        "role": "Agroforestry Producer",
        "id": "BR-MT-2026-7819",
        "phone": "+55 65 99123-4567",
        "region": "Mato Grosso, Brazil",
        "hub": "🇧🇷 Brazil — Mato Grosso (Soy/Maize Belt)",
        "crops": "Soja Precoce, Milho Safrinha, Algodão",
        "lang": "Portuguese",
        "flag": "🇧🇷",
        "badge": "Cerrado Biome",
    },
    {
        "name": "Thabo Molefe",
        "avatar": "TM",
        "role": "Cooperative Farmer",
        "id": "ZA-LP-2026-3104",
        "phone": "+27 82 555 0192",
        "region": "Limpopo, South Africa",
        "hub": "🇿🇦 South Africa — Limpopo (Mixed Farming Belt)",
        "crops": "White Maize, Grain Sorghum, Groundnuts",
        "lang": "English",
        "flag": "🇿🇦",
        "badge": "Limpopo Mixed Belt",
    },
    {
        "name": "Dmitry Ivanov",
        "avatar": "DI",
        "role": "Grain Cooperative Member",
        "id": "RU-KD-2026-5520",
        "phone": "+7 918 123-45-67",
        "region": "Krasnodar Krai, Russia",
        "hub": "🇷🇺 Russia — Krasnodar Krai (Black Earth Belt)",
        "crops": "Winter Wheat, Sunflower, Barley",
        "lang": "Russian",
        "flag": "🇷🇺",
        "badge": "Black Earth Belt",
    },
    {
        "name": "Wang Wei (王伟)",
        "avatar": "WW",
        "role": "Smallholder Lead",
        "id": "CN-HL-2026-9041",
        "phone": "+86 138 0013 8000",
        "region": "Heilongjiang, China",
        "hub": "🇨🇳 China — Heilongjiang (Grain Belt)",
        "crops": "Soybean, Corn, Japonica Rice",
        "lang": "Mandarin",
        "flag": "🇨🇳",
        "badge": "Heilongjiang Grain Belt",
    },
]

