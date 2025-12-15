import spacy
import pandas as pd
import config 

class NLPEngine:
    """
    Responsible for natural language processing and data aggregation.
    """
    def __init__(self, language_name):
        self.model_name = config.SPACY_MODELS.get(language_name)
        if not self.model_name:
            raise ValueError(f"No model found for language: {language_name}")
            
    def load_model(self):
        """Loads the spacy model. Can be slow."""
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
        
        # Smart column detection
        target_col = df.columns[0]
        for col in df.columns:
            if "word" in str(col).lower():
                target_col = col
                break
        
        return set(df[target_col].astype(str).str.lower().str.strip())

    def process_text_pages(self, pages_text, known_words_set=None):
        """
        Main logic loop. 
        """
        if known_words_set is None:
            known_words_set = set()

        word_freq = {}
        
        for doc in self.nlp.pipe(pages_text, batch_size=20):
            for token in doc:
                if (token.is_alpha and 
                    not token.is_stop and 
                    len(token.lemma_) > 2 and
                    token.pos_ in config.VALID_POS_TAGS):
                    
                    lemma = token.lemma_.lower()
                    
                    if lemma not in known_words_set:
                        word_freq[lemma] = word_freq.get(lemma, 0) + 1

        data = list(word_freq.items())
        df = pd.DataFrame(data, columns=['word', 'count'])
        
        if not df.empty:
            df = df.sort_values(by='count', ascending=False)
            
        return df