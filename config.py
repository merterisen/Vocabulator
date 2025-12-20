# Central place for constants. s

WINDOW_TITLE = "Vocabulator"
WINDOW_SIZE = "650x700"

# Language Configuration
LANGUAGES = {
    "German": {
        "model": "de_core_news_sm",
        "articles": {"Masc": "der", "Fem": "die", "Neut": "das"}
    },
    "French": {
        "model": "fr_core_news_sm",
        "articles": {"Masc": "le", "Fem": "la"}
    },
    "Spanish": {
        "model": "es_core_news_sm",
        "articles": {"Masc": "el", "Fem": "la"}
    }
}

VALID_POS_TAGS = {"NOUN", "VERB", "ADJ", "ADV"}