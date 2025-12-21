import json
import math
from openai import OpenAI
import pandas as pd

class LLMManager:
    """
    Responsible for connecting to LLM providers and adding new columns:
        - sentence
        - translate_word
        - translate_sentence
    """

    def __init__(self, llm_model, api_key):
        self.llm_model = llm_model
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
    

    # =================================================================
    # GLOBAL FUNCTIONS
    # =================================================================

    def create_translates(self, input_df:pd.DataFrame, language:str, translate_language:str, update_callback=None) -> pd.DataFrame:
        if input_df is None or input_df.empty():
            return input_df

        words = input_df['word'].tolist()
        batch_size = 20
        total_batches = math.ceil(len(words) / batch_size)        
        output_data = {}

        for i in range(total_batches):
            words_to_send_llm = words[i*batch_size : (i+1)*batch_size]

            if update_callback:
                update_callback(f"Processing batch {i + 1}/{total_batches}...")
        
            try:
                client_output = self._send_to_llm(words_to_send_llm, language, translate_language)
                for item in client_output:
                    word_key = item.get("word", "").lower().strip()
                    if word_key:
                        output_data[word_key] = item

            except Exception as e:
                print(f"Error in batch {i}: {e}")
        

        # Using apply to safely map, if a word failed -> eave fields empty
        output_df = input_df.copy()
        output_df['sentence'] = output_df['word'].apply(lambda x: output_data.get(x.lower().strip(), {}).get('sentence', ''))
        output_df['translate_word'] = output_df['word'].apply(lambda x: output_data.get(x.lower().strip(), {}).get('translate_word', ''))
        output_df['translate_sentence'] = output_df['word'].apply(lambda x: output_data.get(x.lower().strip(), {}).get('translate_sentence', ''))
        
        return output_df
                


    # =================================================================
    # LOCAL FUNCTIONS
    # =================================================================

    def _send_to_llm(self, words_to_send_llm:list, language:str, translate_language:str) -> list:

        prompt = f"""
        You are a vocabulary assistant.
        Source Language: {language}
        Target Language: {translate_language}
        
        Word List: {", ".join(words_to_send_llm)}

        Task:
        For each word in the list, provide:
        1. An example sentence in the Source Language ({language}) containing the word.
        2. The translation of the word in the Target Language ({translate_language}).
        3. The translation of the example sentence in the Target Language ({translate_language}).

        Return ONLY a raw JSON array of objects. Do not include markdown formatting (```json).
        JSON Format:
        [
            {{
                "word": "original_word",
                "sentence": "Example sentence in source language.",
                "translate_word": "Translated word",
                "translate_sentence": "Translated sentence."
            }}
        ]
        """
        

        response = self.client.chat.completions.create(
            model = self.model,
            messages=[
                {"role": "system", "content": "You are a helpful dictionary assistant that outputs strict JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()

        # Clean potential markdown code blocks if the model ignores instructions
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content)