# -*- coding: utf-8 -*-
"""

Created on Aug 10 2023 14:20:05

@author: Riccardo Giovanelli

"""


def text_to_target_lang(text, original_lang = None, target_lang, lang_detector_model="ERCDiDip/langdetect", translation_model = None):
    '''
    Translates the input text to the target language using machine translation.

    Parameters:
        text (str): The input text to be translated.
        target_lang (str): The target language code to translate the text into.
        lang_detector_model (str, optional): The language detection model to use. Defaults to "ERCDiDip/langdetect".
        translation_model (str, optional): The custom translation model to use. Defaults to None.

    Returns:
        tuple: A tuple containing the translated text and other translations (if available).

    Detects languages in the input text and translates it to the target language using a machine translation model.
    If the detected language is the same as the target language, no translation is performed.
    If a custom translation model is not provided, a default translation model is used based on the detected language.
    
    Detectable Languages:
    Modern: Bulgarian (bg), Croatian (hr), Czech (cs), Danish (da), Dutch (nl), English (en),
    Estonian (et), Finnish (fi), French (fr), German (de), Greek (el), Hungarian (hu), Irish (ga),
    Italian (it), Latvian (lv), Lithuanian (lt), Maltese (mt), Polish (pl), Portuguese (pt),
    Romanian (ro), Slovak (sk), Slovenian (sl), Spanish (es), Swedish (sv), Russian (ru),
    Turkish (tr), Basque (eu), Catalan (ca), Albanian (sq), Serbian (se), Ukrainian (uk),
    Norwegian (no), Arabic (ar), Chinese (zh), Hebrew (he)

    Medieval: Middle High German (mhd), Latin (la), Middle Low German (gml), Old French (fro),
    Old Church Slavonic (chu), Early New High German (fnhd), Ancient and Medieval Greek (grc)
    '''
    
    # Import required modules at the beginning of the function
    from transformers import pipeline, MarianMTModel, MarianTokenizer

    # Language detection using the specified model
    lang_detector = pipeline("text-classification", model=lang_detector_model)
    detected_lang = lang_detector(text)
    
    # Check if multiple languages were detected
    if len(detected_lang) > 1:
        other_lang = detected_lang[1:]  # Get other detected languages
        detected_lang = lang_detector(text)[0]['label']  # Use the primary detected language
    else:
        other_lang = None
        detected_lang = lang_detector(text)[0]['label']        
    
    if detected_lang == target_lang or (original_lang is not None and detected_lang != original_lang):
        # If the detected language is the same as the target language or not the same as the original_lang,
        # no translation needed
        translated_text = text
    else:    
        def translate(detected_lang, translation_model, target_lang):
            if translation_model is None:
                # Default translation model
                translation_model_name = f'Helsinki-NLP/opus-mt-{detected_lang}-{target_lang}'
            else:
                # Custom translation model provided
                translation_model_name = translation_model
            
            # Initialize the translation model and tokenizer
            translation_model = MarianMTModel.from_pretrained(translation_model_name)
            tokenizer = MarianTokenizer.from_pretrained(translation_model_name)

            # Prepare the input for translation
            inputs = tokenizer(text, return_tensors='pt')

            # Generate translation
            translation = translation_model.generate(**inputs)
            translated_text = tokenizer.batch_decode(translation, skip_special_tokens=True)[0]
            return translated_text
        
        other_translations = []  # Initialize the list here
        try:
            # Translate the text using the primary detected language
            translated_text = translate(detected_lang, translation_model, target_lang)
            
            if other_lang:
                for x in other_lang:
                    detected_lang = x['label']
                    try:
                        # Translate the text using the other detected languages
                        translated_text = translate(detected_lang, translation_model, target_lang)
                        other_translations.append(translated_text)  # Append translations
                    except:
                        print('The selected translation model didn\'t support the detected language: ' + detected_lang)
            else:
                other_translations = None  # No other translations available
        except:
            print('The selected translation model didn\'t support the detected language: ' + detected_lang)
            if other_lang:
                for x in other_lang:
                    detected_lang = x['label']
                    try:
                        # Translate the text using the other detected languages
                        translated_text = translate(detected_lang, translation_model, target_lang)
                    except:
                        print('The selected translation model didn\'t support the detected language: ' + detected_lang)
                        translated_text = text
                    
            translated_text = text
    
    # Return the translated text and other translations (if available)
    return translated_text, other_translations
