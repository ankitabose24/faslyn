"""
Static configuration for Faslyn.
Holds BRICS hub coordinates and supported advisory languages —
no logic, no side effects, safe to import anywhere.
"""

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
