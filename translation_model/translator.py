"""This is a translation helper class that handles preprocessing, translation, and postprocessing"""
import os
import warnings
import re
import logging
import torch
import ctranslate2
import transformers
from translation_model.mapping_dictionary import nepali_to_english_dict, english_to_nepali_dict
from translation_model.romanized_to_nepali import nepali_to_romanized_dict
from symspellpy.symspellpy import SymSpell, Verbosity
from dotenv import load_dotenv

load_dotenv()

translation_model_path = os.getenv("TRANSLATION_MODEL")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")

class TranslatorModel:
    """
    A translation helper class that handles preprocessing, translation, and postprocessing
    of text between English and Nepali using a pre-trained NLLB model with CTranslate2.

    Main responsibilities:
    - Load tokenizer and translation model
    - Replace and restore URLs/email placeholders
    - Handle punctuation and newline preservation
    - Perform dictionary-based replacements for Romanized and Nepali words
    - Translate text using beam search
    - Restore symbols and apply language-specific formatting (e.g., Nepali danda '।')

    This class is designed to support modular and clean translation workflows for
    applications involving code-mixed or Romanized Nepali-English text.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Using device: %s", self.device)

        self.translation_model_path = translation_model_path
        self.translation_tokenizer=transformers.AutoTokenizer.from_pretrained(
            self.translation_model_path
        )
        self.translation_model = ctranslate2.Translator(self.translation_model_path, device="cuda")
        self.sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        self._build_symspell_dictionary()

    def mask_urls_with_placeholders(self, text: str ) -> tuple[str, dict[str]]:
        """This function replaces URLs and email addresses in the text with placeholders.
        like u1, u2, u3 and so on."""
        url_email_pattern = re.compile(r'\b(?:https?:\/\/|www\.)\S+|\S+@\S+\.\S+')
        matches = url_email_pattern.findall(text)
        placeholder_map = {}
        for i, match in enumerate(matches, start=1):
            placeholder = f'u{i}'
            placeholder_map[placeholder] = match
            text = text.replace(match, placeholder, 1)
        return text, placeholder_map

    def unmask_urls_from_placeholders(self, text: str, placeholder_map: dict[str, str]) -> str:
        """this function restores the original URLs and
        email addresses in the text using the placeholders."""
        for placeholder, original in placeholder_map.items():
            text = text.lower()
            text = text.replace(placeholder, original)
        return text

    def split_preserving_newlines(self, text: str) -> list[str]:
        """This function splits the text while preserving newlines."""
        return re.split(r'(\n)', text)

    def split_on_punctuation(self, text_parts: list[str]) -> list[str]:
        """This function splits the text on punctuation marks while preserving the punctuation.
        like - . , : ; ? ! / \n"""
        final_result = []
        for part in text_parts:
            split_parts = re.split(
                r'(?<!\d)([!?:/]|(?<![A-Za-z])\.(?![A-Za-z]))(?=(?:[^*]*\*\*[^*]*\*\*)*[^*]*$)|([–!?:/]|(?<![A-Za-z])\.(?![A-Za-z]))(?!\d)(?=(?:[^*]*\*\*[^*]*\*\*)*[^*]*$)',
                part)
            final_result.extend(split_parts)
        return [item for item in final_result if item]


    def remove_punctuation_tokens(self, text_parts: list[str]) -> list[str]:
        """This function removes unwanted symbols from the text.
        strip removes leading and trailing whitespace and
        filter removes empty strings and unwanted symbols"""
        return [item.strip()
                for item in text_parts
                if item.strip() and item not in {'–', '.', ':', '?', '/', '!', '\n'}
        ]


    def reinsert_punctuation_tokens(self, original: list[str], translated: list[str]) -> list[str]:
        """
        This function restores the original punctuation and symbols to the translated text.
        It iterates through the original text and checks each item.
        If the item is a symbol, it is either attached to the last word in the translated list (if the last item is a word),
        or added as a separate symbol (if the last item is also a symbol).
        If the item is a word, it takes the next translated word and adds it to the output list.
        """

        translated_with_symbols = []
        index = 0
        for item in original:
            if item in {'–', '.', ':', '?', '/', '!', '\n'}:
                # Attach punctuation directly to the last word if needed
                if translated_with_symbols and translated_with_symbols[-1] not in {'–', '.', ':', '?', '/', '!', '\n'}:
                    translated_with_symbols[-1] += item
                else:
                    translated_with_symbols.append(item)
            else:
                translated_with_symbols.append(translated[index])
                index += 1
        return translated_with_symbols


    def assemble_final_text(self, translated_with_symbols: list[str]) -> str:
        """This function ensures that the translated text is properly formatted.
        Turn the list back into a proper sentence."""
        # Ensuring punctuation is attached properly
        text = ''.join(
            f' {item}' if item not in {'–', '.', ':', '?', '/', '!', '\n'} else item
            for item in translated_with_symbols
        ).strip()
        return text

    def add_space_before_ma(self, text: str ) -> str:
        """This function adds a space before 'मा' and 'को' if they are not preceded by a space."""
        return re.sub(r'(?<=\S)(मा|को)(?=\s|[.,!?;])', r' \1', text)

    def build_romanized_mapping(self, romanized_dict : dict[str, list[str]]) -> dict[str, str]:
        """ This function builds a mapping from romanized words
        to their corresponding Nepali words."""
        return {roman: nepali
                for nepali, romans in romanized_dict.items()
                #Iterate through each romanized variant in the list eg. "निस्किन्छ": ["niskinxa", "niskincha"]
                for roman in romans}
    def _build_symspell_dictionary(self):
        """This function builds the SymSpell dictionary using the provided mapping."""
        for variants in nepali_to_romanized_dict.values():
            for word in variants:
                self.sym_spell.create_dictionary_entry(word, 2)

    def replace_with_symspell(self, text: str) -> str:
        """This function replaces Romanized Nepali words with
        their corresponding Nepali words using SymSpell."""
        replaced_words = []
        for word in text.lower().split():
            suggestions = self.sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=1)
            if suggestions:
                matched_variant = suggestions[0].term
                for nepali_word, variants in nepali_to_romanized_dict.items():
                    if matched_variant in variants:
                        replaced_words.append(nepali_word)
                        break
            else:
                replaced_words.append(word)
        return ' '.join(replaced_words)

    def apply_dictionary_replacements(
        self, text: str, src_lang: str, tgt_lang: str
    ) -> tuple[str, str, str]:
        """
        Preprocesses text by applying dictionary-based replacements
        and determines translation languages.

        - If source language is 'npi_Deva', replaces using Nepali-to-English dictionary.
        - If source language is 'eng_Latn', replaces using English-to-Nepali dictionary.
        - Prioritizes multi-word phrase replacements before single-word replacements.

        Args:
            text (str): Input text to preprocess.
            src_lang (str): Source language code.
            tgt_lang (str): Target language code.

        Returns:
            tuple[str, str, str]: Preprocessed text,
            updated source language, updated target language.
        """

        lower_text = text.lower()
        preprocessed_text = lower_text
        updated_src_lang, updated_tgt_lang = src_lang, tgt_lang

        if src_lang == "npi_Deva":
            preprocessed_text = self.add_space_before_ma(lower_text)
            for phrase in sorted(nepali_to_english_dict.keys(), key=lambda x: -len(x)):
                preprocessed_text = re.sub(
                    rf'\b{re.escape(phrase)}\b',
                    nepali_to_english_dict[phrase],
                    preprocessed_text
                )
            updated_src_lang, updated_tgt_lang = 'npi_Deva', 'eng_Latn'

        elif src_lang == "eng_Latn":
            for phrase in sorted(english_to_nepali_dict.keys(), key=lambda x: -len(x)):
                preprocessed_text = re.sub(
                    rf'\b{re.escape(phrase)}\b',
                    english_to_nepali_dict[phrase],
                    preprocessed_text
                )
            updated_src_lang, updated_tgt_lang = 'eng_Latn', 'npi_Deva'

        logger.info("Preprocessed text after replacements: %s", preprocessed_text)
        return preprocessed_text, updated_src_lang, updated_tgt_lang


    def apply_dictionary_replacements_romanized(
        self, text: str, src_lang: str, tgt_lang: str ) -> tuple[str, str, str]:
        """
        Preprocesses text by applying dictionary-based replacements
        and determines translation languages.

        - If Romanized Nepali words are detected, replaces them with Nepali equivalents,
        applies English-to-Nepali dictionary, and sets languages to 'npi_Deva' → 'eng_Latn'.
        - If source language is 'npi_Deva', replaces using Nepali-to-English dictionary.
        - If source language is 'eng_Latn', replaces using English-to-Nepali dictionary.
        - Prioritizes multi-word phrase replacements before single-word replacements.

        Args:
            text (str): Input text to preprocess.
            src_lang (str): Source language code.

        Returns:
            tuple[str, str, str]: Preprocessed text,
            updated source language, updated target language.
        """

        lower_text = text.lower()
        romanized_mapping = self.build_romanized_mapping(nepali_to_romanized_dict)
        contains_romanized = any(word in romanized_mapping for word in lower_text.split())

        # Initialize replacement settings
        preprocessed_text = lower_text
        updated_src_lang, updated_tgt_lang = src_lang, tgt_lang

        if contains_romanized:

            # Step 1: Replace phrases from Romanized Mapping
            # Match multi-word phrases in the dictionary first
            # Sort the keys by length in descending order to match longer phrases first
            for phrase in sorted(romanized_mapping.keys(), key=lambda x: -len(x)):
                preprocessed_text = re.sub(r'\b' + re.escape(phrase) + r'\b', romanized_mapping[phrase], preprocessed_text)

            preprocessed_text = self.replace_with_symspell(preprocessed_text)

            # Step 2: Replace phrases from English-Nepali Dictionary
            # Match multi-word phrases in the dictionary first
            # Sort the keys by length in descending order to match longer phrases first
            for phrase in sorted(english_to_nepali_dict.keys(), key=lambda x: -len(x)):
                preprocessed_text = re.sub(r'\b' + re.escape(phrase) + r'\b', english_to_nepali_dict[phrase], preprocessed_text)

            updated_src_lang, updated_tgt_lang = 'npi_Deva', 'eng_Latn'

        elif src_lang == "npi_Deva":
            preprocessed_text = self.add_space_before_ma(lower_text)
            # Match multi-word phrases in the dictionary first
            # Sort the keys by length in descending order to match longer phrases first
            for phrase in sorted(nepali_to_english_dict.keys(), key=lambda x: -len(x)):
                preprocessed_text = re.sub(r'\b' + re.escape(phrase) + r'\b', nepali_to_english_dict[phrase], preprocessed_text)

            updated_src_lang, updated_tgt_lang = 'npi_Deva', 'eng_Latn'

        elif src_lang == "eng_Latn":
            # Match multi-word phrases in the dictionary first
            # Sort the keys by length in descending order to match longer phrases first
            for phrase in sorted(english_to_nepali_dict.keys(), key=lambda x: -len(x)):
                preprocessed_text = re.sub(r'\b' + re.escape(phrase) + r'\b', english_to_nepali_dict[phrase], preprocessed_text)

            updated_src_lang, updated_tgt_lang = 'eng_Latn', 'npi_Deva'

        logger.info("Preprocessed text after replacements: %s", preprocessed_text)
        return preprocessed_text, updated_src_lang, updated_tgt_lang


    # Function to translate text using the translation model
    def translate_text_with_model(self, text: str,
                    src_lang: str ='npi_Deva',
                    tgt_lang: str ='eng_Latn'
                    ) -> str:
        """
        Translates text using the translation model.
        """
        self.translation_tokenizer.src_lang = src_lang
        self.translation_tokenizer.tgt_lang = tgt_lang
        inputs = self.translation_tokenizer(
            text.lower(),
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=1024).to(self.device)
        source_tokens = self.translation_tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        target_prefix = [tgt_lang]
        results = self.translation_model.translate_batch([source_tokens],
                                                        target_prefix=[target_prefix],
                                                        beam_size=4)
        translated_tokens = results[0].hypotheses[0][1:]
        translated_text = self.translation_tokenizer.decode(
            self.translation_tokenizer.convert_tokens_to_ids(translated_tokens),
            skip_special_tokens=True)
        return translated_text

    def translate_single_sentence(self,
                                  text: str,
                                  src_lang: str,
                                  tgt_lang: str,
                                  context: str = "answer") -> str:
        """
        Translates text while preserving special words using dictionary mapping.
        """

        if not isinstance(text, str):
            text = str(text)
        if context == "question":
            preprocessed_text, updated_src_lang, updated_tgt_lang = self.apply_dictionary_replacements_romanized(text, src_lang, tgt_lang)
            logger.info("This is text with replacement from the dictionary for romanized as the context is question: %s", preprocessed_text)
        else:
            preprocessed_text, updated_src_lang, updated_tgt_lang = self.apply_dictionary_replacements(text, src_lang, tgt_lang)
            logger.info("This is text with replacement from the dictionary for romanized as the context is answer: %s", preprocessed_text)
        logger.info("This is text with replacement from the dictionary: %s", preprocessed_text)
        translated_text = self.translate_text_with_model(
            preprocessed_text, updated_src_lang, updated_tgt_lang
        )
        return translated_text


    def replace_dot(self, input_str: str) -> str:
        """
        This function replaces the dot (.) with a full stop (।) in the text.
        It also handles specific cases where certain words should not be replaced.
        """
        words_to_replace = ['श्री', 'श्रीमती','प्रा', 'डा', 'ई' ]
        pattern = r'(' + '|'.join(words_to_replace) + r')\.'
        text = re.sub(pattern, r'\1', input_str) # ignores words present in word to replace
        text = re.sub(r'(?<!\d)\.', '।', text) #replace . with ।
        text = re.sub(r'।।+', '।', text) # removes extra ।
        text = re.sub(r'\?{2,}', '?', text) #removes extra ?
        return text