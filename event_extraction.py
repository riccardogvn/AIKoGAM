# -*- coding: utf-8 -*-
import os
import json
import re
import spacy
from src.utils import utils
from tqdm.notebook import tqdm
from src.utils.transl import text_to_target_lang
import spacy
from spacy.cli.download import download
from transformers import pipeline  # Add this import statement
def extract_events_dot(text):
    """
     Extract events from a paragraph based on full stops.
    
     Parameters
     ----------
     text : STR
         A PARAGRAPH.
    
     Returns
     -------
     events : LIST
         LIST OF EVENTS FOUND.
    
     """
    events = re.findall('[a-zA-Z\u00C0-\u017F\d,;\s\(\)\'\"\’\&\\-:\/]+.', text)
    events = [s.strip() for s in events]
    events = [s.strip(".") for s in events]
    return events

def extract_events_html(text):
    """
    Extract events from a paragraph based on html tags.

    Parameters
    ----------
    text : STR
        A PARAGRAPH.

    Returns
    -------
    events : LIST
        LIST OF EVENTS FOUND.

    """
    events = []
    lines = text.split("<br />")
    
    for line in lines:
        if ('<p>' in line):
            paragraphs = re.findall('.*?</p>', line)
            paragraphs = [p.strip('</p>') for p in paragraphs]
            events.extend(paragraphs)
        else:
            events.append(line)
            
    events = [s.strip() for s in events]    
    return events
             
def clean_provenance(prov):
    """
    Proprocess provenance text.

    Parameters
    ----------
    prov : STR
        PROPVENANCE TEXT.

    Returns
    -------
    prov : STR
        PREPROCESSED PROPVENANCE TEXT.

    """ 
    # Remove the parts of the provenance that are inside brackets (to facilitate extracting events)
    prov = re.sub("\s[\[\(].*?[\)\]]", "", prov)
    
    # This is to avoid the splitting of provenance with such kind of dots 
    prov = re.sub("Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.|St\.|Rev\.|acc\.|vol\.|no\.|pl\.|inv\.", "", prov, flags=re.IGNORECASE)
    
    # The ":" and ";" act as event separator such as the "."
    prov = prov.replace(':', '.')
    prov = prov.replace(';', '.')
    
    # Cleaning
    prov = prov.replace('. ,', ',')
    prov = prov.replace('. ;', ',')    
    prov = prov.replace('.,', ',')
    
    prov = prov.replace('_', '')
    
    prov = prov.replace('<em>', '')
    

    
    return prov





spacy_models = {
    'ca': 'ca_core_news_sm',  # Catalan
    'da': 'da_core_news_sm',  # Danish
    'de': 'de_core_news_sm',  # German
    'el': 'el_core_news_sm',  # Greek
    'en': 'en_core_web_md',  # English
    'es': 'es_core_news_sm',  # Spanish
    'fi': 'fi_core_news_sm',  # Finnish
    'fr': 'fr_core_news_sm',  # French
    'hr': 'hr_core_news_sm',  # Croatian
    'it': 'it_core_news_sm',  # Italian
    'ja': 'ja_core_news_sm',  # Japanese
    'ko': 'ko_core_news_sm',  # Korean
    'lt': 'lt_core_news_sm',  # Lithuanian
    'mk': 'mk_core_news_sm',  # Macedonian
    'nb': 'nb_core_news_sm',  # Norwegian Bokmål
    'nl': 'nl_core_news_sm',  # Dutch
    'pl': 'pl_core_news_sm',  # Polish
    'pt': 'pt_core_news_sm',  # Portuguese
    'ro': 'ro_core_news_sm',  # Romanian
    'sl': 'sl_core_news_sm',  # Slovenian
    'sv': 'sv_core_news_sm',  # Swedish
    'ru': 'ru_core_news_sm',  # Russian
    'uk': 'uk_core_news_sm',  # Ukrainian
    'xx_ent_wiki': 'xx_ent_wiki_sm',  # Multi-language Entity Recognition
    'xx_sent_ud': 'xx_sent_ud_sm',  # Multi-language Sentence Segmentation
    'zh': 'zh_core_web_sm',  # Chinese
}

def detect_language(provenance_text, language_cache):
    # Check if the input is a valid string
    if not isinstance(provenance_text, (str, bytes)):
        raise ValueError("provenance_text must be a string or bytes-like object")

    # Check if the language is cached based on similarity
    matched_key = None
    for key in language_cache.keys():
        if fuzz.ratio(provenance_text, key) >= similarity_threshold:
            matched_key = key
            print('matched')
            break

    if matched_key is not None:
        detected_lang, spacy_model = language_cache[matched_key]
    else:
        # Language detection using the specified model
        lang_detector = pipeline("text-classification", model="ERCDiDip/langdetect")
        detected_lang = lang_detector(provenance_text)
        print(detected_lang)

        # Check if multiple languages were detected
        detected_lang = lang_detector(provenance_text)[0]['label']
        primary_lang_score = lang_detector(provenance_text)[0]['score']  # Get the score of the primary language

        if len(detected_lang) > 1:
            other_lang = detected_lang[1:]  # Get other detected languages
        else:
            other_lang = None

        # Determine the Spacy model to use based on language detection score
        if primary_lang_score < 0.7:
            detected_lang = 'en'

        elif detected_lang in spacy_models:
            detected_lang = detected_lang

        else:
            detected_lang = 'en'

        spacy_model = spacy_models[detected_lang]

        # Cache the detected language and Spacy model based on similarity
        language_cache[provenance_text] = (detected_lang, spacy_model)

    return detected_lang, spacy_model, language_cache
from tqdm import tqdm
def add_lang(file, language_cache):
    with open(file, 'r', encoding='utf-8') as j:
        annos = json.load(j)
        annosk = list(annos.keys())
        annosv = list(annos.values())
        data = annos
        for key, value in tqdm(data['lots'].items()):
            json_object = value
            prov = value['lotProvenance']
            events_of_artworks = []
            if prov:
                try:
                    new_p = dict()
                    for k, v in prov.items():
                        if v is None:
                            pass
                        else:
                            cleaned_prov = clean_provenance(v)
                            print(cleaned_prov)
                            detected_lang, _, language_cache = detect_language(cleaned_prov, language_cache)
                            prov_with_lang = (cleaned_prov, detected_lang)
                            new_p[k] = prov_with_lang
                    json_object['lotProvenance'] = new_p
                    print(new_p)
                except Exception as e:
                    json_object['lotProvenance'] = prov
                    print(f"Error processing provenance: {str(e)}")
                    pass
            with open('datasets/db_lang.json', 'w', encoding='utf-8') as db:
                json.dump(data, db)

    return data




import json
import spacy
from tqdm.notebook import tqdm

from src.utils import utils

def batch_extract_store_events(
    artworks,
    batch_size=100,  # Define your desired batch size
    annosk=None,  # Pass annosk as an argument
    annosv=None, # Pass annosv as an argument
    event_output_file='events/events.txt',
    no_event_output_file='events/noevents.txt',
    artwork_index=0 
):
    """
    Extract events from a list of artwork provenances and store the events in JSON format.

    Parameters
    ----------
    artworks : list of dict
        List of artwork JSON objects.
    batch_size : int, optional
        Batch size for processing. The default is 100.
    event_output_file : str, optional
        Path to the event output file. The default is 'events/events.txt'.
    no_event_output_file : str, optional
        Path to the file for artworks with no events. The default is 'events/noevents.txt'.
    annosk : list, optional
        List of keys for mapping. Pass this argument if required.
    annosv : list, optional
        List of values for mapping. Pass this argument if required.

    Returns
    -------
    None
    """
    import json
    import spacy
    from tqdm.notebook import tqdm
    from src.utils import utils
    f

    old_model = 'en_core_web_md'
    spacy_model = old_model
    nlp = spacy.load('en_core_web_md')
    iteration_counter = 0  # Initialize a counter to keep track of iterations

    # Process artworks in batches
    for batch_start in tqdm(range(0, len(artworks), batch_size)):
        batch_end = min(batch_start + batch_size, len(artworks))
        batch_artworks = artworks[batch_start:batch_end]

        for json_object in tqdm(batch_artworks):
            prov = json_object.get('lotProvenance')
            events_of_artworks = []

            try:
                if prov:
                    for k, v in prov.items():
                        if v is None:
                            print('v none')
                            pass
                        elif k == 'provenance_0':
                            pass
                        elif isinstance(v, dict):
                            prov_text = clean_provenance(v['text'])
                            spacy_model = v['spacy_model']
                            entities, old_model, nlp = utils.extract_named_entities(prov_text, spacy_model, old_model, nlp)
                            for i, entity_ls in enumerate(entities.values()):
                                if (list(entities.keys())[i] != 'DATE'):
                                    for e in entity_ls:
                                        prov_text = prov_text.replace(e, utils.remove_dots(e))
                            events = extract_events_dot(prov_text)
                            artwork_events = []

                            for event in events:
                                ev_data = {}
                                ev_data['label'] = event.replace('|', '').strip()

                                ev_entites, old_model, nlp = utils.extract_named_entities(event, spacy_model, old_model, nlp)

                                for entity_type in ev_entites.keys():
                                    ev_data[entity_type] = ev_entites[entity_type]

                                artwork_events.append(ev_data)

                            for event in artwork_events:
                                new_elems = []
                                label_value = None

                                for k, v in event.items():
                                    if k == 'label':
                                        label_value = v
                                        new_elems.append((k, v))
                                    elif isinstance(v, str):
                                        if v in annosk:
                                            idx = annosk.index(v)
                                            new_elems.append((annosv[idx], v))
                                        elif 'collection' in v.lower():
                                            if k == 'label':
                                                if len(event) == 1:
                                                    new_elems.append(('ORG', v))
                                                    new_elems.append(('label', v))
                                            else:
                                                new_elems.append(('ORG', v))
                                        else:
                                            new_elems.append((k, v))
                                    elif isinstance(v, list):
                                        key = k
                                        for element in v:
                                            if element in annosk:
                                                idx = annosk.index(element)
                                                new_elem = (annosv[idx], element)
                                                if new_elem not in new_elems:
                                                    new_elems.append(new_elem)
                                            elif any('collection' in str(e).lower() for e in element):
                                                if key == 'label':
                                                    if len(event) == 1:
                                                        new_elem = ('ORG', element)
                                                        if new_elem not in new_elems:
                                                            new_elems.append(new_elem)
                                                            new_elems.append(('label', element))
                                                else:
                                                    new_elem = ('ORG', element)
                                                    if new_elem not in new_elems:
                                                        new_elems.append(new_elem)
                                            else:
                                                new_elems.append((k, element))

                            event['new_elem'] = new_elems
                            output_dict = {}
                            for elem in event['new_elem']:
                                key, value = elem
                                if key in output_dict:
                                    if isinstance(output_dict[key], list):
                                        output_dict[key].append(value)
                                    else:
                                        output_dict[key] = [output_dict[key], value]
                                else:
                                    output_dict[key] = value

                            output_dict['label'] = label_value
                            event.clear()
                            event.update(output_dict)

                            events_of_artworks.append(artwork_events)
                            with open(event_output_file, 'a', encoding="utf-8") as output_f:
                                json_object["events"] = events_of_artworks
                                json_object_with_index = {str(artwork_index): json_object}                                
                                output_f.write(json.dumps(json_object_with_index, ensure_ascii=False) + "\n")
                                artwork_index += 1

                            # Increment the iteration counter
                            iteration_counter += 1

                            # Check if the counter is a multiple of 100
                            if iteration_counter % 100 == 0:
                                print(f"Last events added for iteration {iteration_counter}: {artwork_events}")
                else:
                    with open(event_output_file, 'a', encoding="utf-8") as output_f:
                        json_object["events"] = ""
                        json_object_with_index = {str(artwork_index): json_object}                             
                        output_f.write(json.dumps(json_object_with_index, ensure_ascii=False) + "\n")
                        artwork_index +=1
                    with open(no_event_output_file,'a',encoding='utf-8') as output_f:
                        json_object['eventy'] = ""
                        json_object_with_index = {str(artwork_index): json_object}           
                        output_f.write(json.dumps(json_object_with_index, ensure_Ascii=False) + '\n')
                        artwork_index += 1

            except Exception as e:
                # Handle specific exceptions and log them for better debugging
                print(f"Error processing artwork: {str(e)}")

    return artwork_index



if __name__ == "__main__":
    
    # Named Entity Recognition (NER) model
    ner_model = spacy.load("en_core_web_md")
    
    file = 'datasets/db.json'

    artwork_index = 0
    artwork_index = extract_store_events(ner_model, file, artwork_index)
    
        
    print("Job done")        
    

  
    

  
    
