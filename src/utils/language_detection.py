import langid
from langid.langid import LanguageIdentifier, model
from tqdm import tqdm
from setup.config import SPACY_MODELS
identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

def detect_language_batch(texts):
    """
    Detect the language of a batch of texts and return the detected languages and scores.

    Args:
        texts (list of str): A list of input texts to detect the language for.

    Returns:
        tuple: A tuple containing:
            - input_texts (list of str): The input texts.
            - detected_languages (list of str): The detected languages for each input text.
            - detection_scores (list of float): Confidence scores for each detected language.
    """
    detected_languages = []
    spacy_models_list = []  # Store the Spacy models for each text
    input_texts = []  # Store the input texts

    for text in tqdm(texts, desc="Detecting Languages"):
        # Detect the language using langid.py

        detected_lang, score = identifier.classify(text)
        # Determine the Spacy model to use based on language detection score

        if detected_lang in SPACY_MODELS:
            detected_lang = detected_lang
        else:
            detected_lang = 'en'

        spacy_model = SPACY_MODELS[detected_lang]


        detected_languages.append(detected_lang)
        spacy_models_list.append(spacy_model)
        input_texts.append(text)  # Store the input text


    return input_texts, detected_languages, spacy_models_list

