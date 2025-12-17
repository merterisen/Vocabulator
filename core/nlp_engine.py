import spacy
import pandas as pd
import config 

# Keep this as a class because it needs to remember things.

class NLPEngine:
    """
    Responsible for natural language processing and data aggregation.
    """

    def __init__(self, language_name):
        self.language_name = language_name
        lang_config = config.LANGUAGES.get(language_name)
        
        if not lang_config:
            raise ValueError(f"No configuration found for language: {language_name}")
            
        self.model_name = lang_config["model"]

    def load_model(self):
        """Loads the spacy models like de_core_news_sm."""
        # KEEP THIS TRY/EXCEPT
        try:
            self.nlp = spacy.load(self.model_name, disable=["ner", "parser"])
        except OSError:
            raise OSError(f"Model '{self.model_name}' not found. Please run: python -m spacy download {self.model_name}")


    def load_known_words(self, filepath):
        """
        Loads a CSV/Excel file and returns a set of known words.
        """
        if not filepath:
            return set()
            
        if filepath.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(filepath)
        else:
            df = pd.read_csv(filepath)
        
        # Smart column detection: reads first column only.
        target_col = df.columns[0]
        return set(df[target_col].astype(str).str.lower().str.strip())

    def process_text_pages(self, pages_text, known_words_set=None, include_articles=False):
        """
        Main logic loop. 
        Args:
            include_articles (bool): If True, adds articles to nouns.
        """
        
        if known_words_set is None:
            known_words_set = set()

        word_freq = {}
        word_gender = {} 
        
        article_map = config.LANGUAGES.get(self.language_name, {}).get("articles", {})

        for doc in self.nlp.pipe(pages_text, batch_size=20):
            for token in doc:
                if (token.is_alpha and 
                    not token.is_stop and 
                    len(token.lemma_) > 2 and
                    token.pos_ in config.VALID_POS_TAGS):
                    
                    lemma = token.lemma_.lower()
                    
                    if lemma not in known_words_set:
                        # 1. Count the word (lemma based)
                        word_freq[lemma] = word_freq.get(lemma, 0) + 1
                        
                        # 2. Detect Gender if it is a Noun (only if user wants articles)
                        if include_articles and token.pos_ == "NOUN" and lemma not in word_gender:
                            genders = token.morph.get("Gender")
                            if genders:
                                word_gender[lemma] = genders[0]

        # 3. Format Output
        data = []
        for lemma, count in word_freq.items():
            display_word = lemma
            
            # Articles Conditions
            if include_articles and lemma in word_gender:
                gender = word_gender[lemma]
                article = article_map.get(gender)
                if article:
                    display_word = f"{article} {lemma}"
            
            data.append((display_word, count))

        df = pd.DataFrame(data, columns=['word', 'count'])
        
        if not df.empty:
            df = df.sort_values(by='count', ascending=False)
            
        return df