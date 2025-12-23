import spacy
import pandas as pd
import config 

class NLPManager:
    """
    Responsible for natural language processing and data aggregation.
    """

    def __init__(self, language_name):
        self.language_name = language_name
        lang_config = config.LANGUAGES.get(language_name)
        
        if not lang_config:
            raise ValueError(f"No configuration found for language: {language_name}")
            
        self.model_name = lang_config["model"]
        self.nlp = None


    # =================================================================
    # GLOBAL FUNCTIONS
    # =================================================================

    def load_model(self):
        """Loads the spacy models."""
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
            
        try:
            if filepath.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)
            
            # Smart column detection: reads first column only.
            target_col = df.columns[0]
            known_words = set(df[target_col].astype(str).str.lower().str.strip())
        
            lemmatized_known_words = set()

            for doc in self.nlp.pipe(list(known_words), batch_size=100):
                for token in doc:
                    if token.is_alpha:
                        lemmatized_known_words.add(token.lemma_.lower())
            
            return lemmatized_known_words
        
        except Exception as e:
            raise Exception(f"Failed to read known words file: {str(e)}")



    def extract_words(self, texts, known_words=None, include_articles=False):
        """
        Extracts words from text, handles nlp tasks and returns dataframe.
        """

        if self.nlp is None:
            self.load_model()
            
        if known_words is None:
            known_words = set()
        
        lemmatized_words_data = {}

        language_config = config.LANGUAGES.get(self.language_name, {})
        article_map = language_config.get("articles") or {} 

        for doc in self.nlp.pipe(texts, batch_size=20):
            for token in doc:
                if (token.is_alpha and not token.is_stop and len(token.lemma_) > 2 and token.pos_ in config.VALID_POS_TAGS):
                    lemma = token.lemma_.lower()
                    
                    # If word is known, skip loop.
                    if lemma in known_words:
                        continue

                    # words_data configuration
                    if lemma not in lemmatized_words_data:
                        lemmatized_words_data[lemma] = {
                            "count": 0,
                            "gender": None,
                            "pos": token.pos_
                        }

                    lemmatized_words_data[lemma]["count"] += 1
                    
                    # Article info
                    if article_map and token.pos_ == "NOUN" and lemmatized_words_data[lemma]["gender"] is None:
                            genders = token.morph.get("Gender")
                            if genders:
                                lemmatized_words_data[lemma]["gender"] = genders[0]
                    

        # Output Data
        output_data = []
        for key, values in lemmatized_words_data.items():
            # Adding Articles
            if include_articles and values["gender"]:
                article = article_map.get(values["gender"])
                if article:
                    key = f"{article} {key}"
            

            row = {
                "word": key,
                "count": values["count"],
                "pos": values["pos"]
            }

            output_data.append(row)

        output_df = pd.DataFrame(output_data)
        
        if not output_df.empty:
            output_df = output_df.sort_values(by='count', ascending=False)
            
        return output_df


    # =================================================================
    # LOCAL FUNCTIONS
    # =================================================================