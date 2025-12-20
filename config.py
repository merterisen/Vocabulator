# Central place for constants. s

WINDOW_TITLE = "Vocabulator"
WINDOW_SIZE = "650x700"

# Language Configuration
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

LLM_MODELS = {
    "gpt-5.2": {"model": "gpt-5.2", "type": "openai"},
    "gpt-5": {"model": "gpt-5", "type": "openai"},
    "gpt-5-mini": {"model": "gpt-5-mini", "type": "openai"},
    "gpt-4.1": {"model": "gpt-4.1", "type": "openai"},
    "gpt-4.1-mini": {"model": "gpt-4.1-mini", "type": "openai"},
    "gpt-4o": {"model": "gpt-4o", "type": "openai"},
    "gpt-4o-mini": {"model": "gpt-4o-mini", "type": "openai"},
}


VALID_POS_TAGS = {"NOUN", "VERB", "ADJ", "ADV"}