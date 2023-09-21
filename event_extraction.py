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




def extract_store_events(ner_model, file, artwork_index = 0):
    """
    Extract events from artwork provenances. Store the events in JSON format.

    Parameters
    ----------
    ner_model : LANGUAGE
        NAMED ENTITY REGOGNITION MODEL.
    directory : STR
        DATASET OF PROVENANCES.
    json_object_level : INT, optional
        JSON OBJECT LEVEL TO CONSIDER FOR EXTRACTING ARTWORK DATA. The default is 0.
    event_separator : STR, optional
        THE MECHANISM OF EXTRACTING EVENTS. The default is "html".
    artwork_index : INT, optional
        ARTWORK INDEX. The default is 0.

    Returns
    -------
    artwork_index : INT
        ARTWORK INDEX.

    """
    with open('datasets/db.json','r') as j:
        annos = json.load(j)
    annosk = list(annos.keys())
    annosv = list(annos.values())
    
    with open(file, 'r') as input_f:

    # Returns json object as a dictionary
        data = json.load(input_f)
          
        # Iterating through the json list
        # Iterating through the json list
        for k,v in tqdm(data['lots'].items()):
           
            json_object = v
            prov = v['lotProvenance'] 
            events_of_artworks = []
        
            # Consider only artworks with provenance  
            if (prov):                  
                try:    
                    # Preprocessing
                    for k,v in prov.items():
                        if v is None:                    
                            pass
                        else:
                            prov = clean_provenance(v)
            
                    # Remove dots from names, etc.
                            entities = utils.extract_named_entities(ner_model, prov)
                            for i, entity_ls in enumerate(entities.values()):
                                if (list(entities.keys())[i] != 'DATE'): 
                                    for e in entity_ls:
                                        prov = prov.replace(e, utils.remove_dots(e))
            
                            
                            
                            events = extract_events_dot(prov)
            
                            # Extract named entities from the events
                            artwork_events = []
                            
                            for event in events:
                                ev_data = {}
                                ev_data['label'] = event
                                
                                ev_entites = utils.extract_named_entities(ner_model, event)
                                
                                for entity_type in ev_entites.keys():
                                    ev_data[entity_type] = ev_entites[entity_type]
                                    
                                
                                artwork_events.append(ev_data)
                                print('oLDone\n',artwork_events)
                                from collections import Counter
                                new_artwork_events = []
                                from collections import Counter

                                for event in artwork_events:
                                    new_elems = []
                                    label_value = None  # Initialize a variable to store the 'label' value
                                    for k, v in event.items():
                                        if k == 'label':  # Check if the key is 'label'
                                            label_value = v
                                            new_elems.append((k, v))
                                        if type(v) is str:
                                            if v in annosk:
                                                idx = annosk.index(v)
                                                new_elems.append((annosv[idx], v))
                                                print('is str in annosk', new_elems)
                                            elif 'collection' in v.lower():
                                                if k == 'label':
                                                    if len(event) == 1:
                                                        new_elems.append(('ORG', v))
                                                        print('collection in v lower with label k', new_elems)
                                                        new_elems.append(('label', v))
                                                        print('readding label', new_elems)
                                                else:
                                                    new_elems.append(('ORG', v))
                                                    print('not label k', new_elems)
                                            else:
                                                new_elems.append((k, v))
                                                print('else', new_elems)
                                        elif type(v) is list:
                                            key = k
                                            for element in v:
                                                if element in annosk:
                                                    idx = annosk.index(element)
                                                    new_elems.append((annosv[idx], element))
                                                    print('list', new_elems)
                                                elif 'collection' in element.lower():
                                                    if key == 'label':
                                                        if len(event) == 1:
                                                            new_elems.append(('ORG', element))
                                                            print('listwithcollectionlabel', new_elems)
                                                            new_elems.append(('label', element))
                                                            print('readdinglabel', new_elems)
                                                    else:
                                                        new_elems.append(('ORG', element))
                                                        print('notlist', new_elems)
                                                else:
                                                    new_elems.append((k, element))
                                                    print(new_elems)
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
                                        
                                    output_dict['label'] = label_value  # Restore the 'label' key-value pair
                                    event.clear()
                                    event.update(output_dict)
                                
                                print('newone\n', artwork_events)
                                
                                    
                                
                        events_of_artworks.append(artwork_events)
                        
                
                    with open('events/events.txt', 'a', encoding="utf-8") as output_f:
                                json_object["events"] = events_of_artworks
                                json_str = json.dumps({str(artwork_index):json_object}, ensure_ascii = False)
                                output_f.write(json_str + "\n")
                                artwork_index += 1
                except:
                    with open('events/events.txt', 'a', encoding="utf-8") as output_f:
                        json_object["events"] = ""
                        json_str = json.dumps({str(artwork_index):json_object}, ensure_ascii = False)
                        output_f.write(json_str + "\n")
                        artwork_index += 1
                    with open('events/noevents.txt', 'a', encoding="utf-8") as output_f:
                        json_object["eventy"] = ""
                        json_str = json.dumps({str(artwork_index):json_object}, ensure_ascii = False)
                        output_f.write(json_str + "\n")
                        artwork_index += 1
            else:
                    with open('events/events.txt', 'a', encoding="utf-8") as output_f:
                        json_object["events"] = ""
                        json_str = json.dumps({str(artwork_index):json_object}, ensure_ascii = False)
                        output_f.write(json_str + "\n")
                        artwork_index += 1
                    with open('events/noevents.txt', 'a', encoding="utf-8") as output_f:
                        json_object["events"] = ""
                        json_str = json.dumps({str(artwork_index):json_object}, ensure_ascii = False)
                        output_f.write(json_str + "\n")
                        artwork_index += 1  
            
                                          
                

         
    return artwork_index



if __name__ == "__main__":
    
    # Named Entity Recognition (NER) model
    ner_model = spacy.load("en_core_web_md")
    
    file = 'datasets/db.json'

    artwork_index = 0
    artwork_index = extract_store_events(ner_model, file, artwork_index)
    
        
    print("Job done")        
    

  
    

  
    
