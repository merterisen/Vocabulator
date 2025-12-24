# Central place for constants. s

WINDOW_TITLE = "Vocabulator"
WINDOW_SIZE = "650x700"

# NLP Configuration
LANGUAGES = {
    "German": {
        "model": "de_core_news_sm",
        "articles": {"Masc": "der", "Fem": "die", "Neut": "das"},
        "abb": "de",
    },
    "English": {
        "model": "en_core_web_sm",
        "articles": {},
        "abb": "en",
    },
    "French": {
        "model": "fr_core_news_sm",
        "articles": {"Masc": "le", "Fem": "la"},
        "abb": "fr",
    },
    "Spanish": {
        "model": "es_core_news_sm",
        "articles": {"Masc": "el", "Fem": "la"},
        "abb": "es",
    },
}

VALID_POS_TAGS = {"NOUN", "VERB", "ADJ", "ADV"}


# LLM Configuration
LLM_BATCH_SIZE = 20

LLM_MODELS = {
    "gpt-5.2": {"model": "gpt-5.2", "type": "openai", "input_price": 1.75, "output_price": 14.00},
    "gpt-5.1": {"model": "gpt-5.2", "type": "openai", "input_price": 1.25, "output_price": 10.00},
    "gpt-5": {"model": "gpt-5", "type": "openai", "input_price": 1.25, "output_price": 10.00},
    "gpt-5-mini": {"model": "gpt-5-mini", "type": "openai", "input_price": 0.25, "output_price": 2.00},
    "gpt-4.1": {"model": "gpt-4.1", "type": "openai", "input_price": 2.00, "output_price": 8.00},
    "gpt-4.1-mini": {"model": "gpt-4.1-mini", "type": "openai", "input_price": 0.40, "output_price": 1.60},
    "gpt-4o": {"model": "gpt-4o", "type": "openai", "input_price": 2.50, "output_price": 10.00},
    "gpt-4o-mini": {"model": "gpt-4o-mini", "type": "openai", "input_price": 0.15, "output_price": 0.60},
}

