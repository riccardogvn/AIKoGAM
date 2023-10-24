# -*- coding: utf-8 -*-
#event_extraction.py
import os
import json
import re
import spacy
from src.utils import utils
from src.utils.transl import text_to_target_lang
from spacy.cli.download import download
from transformers import pipeline  # Add this import statement
from memory_profiler import profile
from fuzzywuzzy import fuzz
from setup.config import SPACY_MODELS, similarity_threshold



import re
import gc  # Import the garbage collection module
from collections import Counter
from tqdm.notebook import tqdm

# Define a similarity threshold for language caching
similarity_threshold = 90


def duplicatesCheck(datafile):
    # Read the content of the file
    with open(datafile, "r", encoding="utf-8") as file:
        data = file.readlines()

    # Create a dictionary to store unique entries based on lotHash
    unique_entries = {}

    # Process each line in the file
    for line in data:
        entry = json.loads(line)
        lot_hash = entry.get(list(entry.keys())[0], {}).get("lotHash")

        # Check if the lotHash is not already present
        if lot_hash not in unique_entries:
            unique_entries[lot_hash] = entry

    # Write the unique entries back to the file with new index keys (0, 1, 2, 3, 4, ...)
    with open(datafile, "w", encoding="utf-8") as file:
        for index, entry in enumerate(unique_entries.values()):
            # Write the extracted dictionary with the new index as the key
            file.write(json.dumps({str(index): entry[next(iter(entry))]}, ensure_ascii=False) + "\n")

    # Print the length of data and unique_entries
    print("Length of data:", len(data))
    print("Length of unique_entries:", len(unique_entries))
    print("Duplicates removed:", len(data) - len(unique_entries))

    with open(datafile, newline='', encoding="utf8") as jsonfile:
        lines = jsonfile.readlines()

    return jsonfile

def extract_events_dot(text):
    """
    Extract events from a paragraph based on full stops.

    Parameters
    ----------
    text : str
        A paragraph.

    Returns
    -------
    events : list
        List of events found.
    """
    events = re.findall('[a-zA-Z\u00C0-\u017F\d,;\s\(\)\'\"\’\&\\-:\/]+.', text)
    events = [s.strip() for s in events]
    events = [s.strip(".") for s in events]
    return events

def extract_events_html(text):
    """
    Extract events from a paragraph based on HTML tags.

    Parameters
    ----------
    text : str
        A paragraph.

    Returns
    -------
    events : list
        List of events found.
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
    Preprocess provenance text.

    Parameters
    ----------
    prov : str
        Provenance text.

    Returns
    -------
    prov : str
        Preprocessed provenance text.
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

# @profile
def batch_extract_store_events(
        artworks,
        batch_size=100,
        event_output_file='events/events.txt',
        no_event_output_file='events/noevents.txt',
        artwork_index=0,
        
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
    artwork_index : int
        Updated artwork index.
    """
    final_output = []
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
                    # Preprocessing
                    for k, v in prov.items():
                        if v is None or k == 'provenance_0':
                            continue
                        elif isinstance(v, dict):
                            prov_text = clean_provenance(v['text'])
                            spacy_model = v['spacy_model']

                            # Remove dots from names, etc.
                            entities, old_model, nlp = utils.extract_named_entities(prov_text, spacy_model, old_model,
                                                                                    nlp)
                            if not entities:
                                if 'anonymous' in prov_text.lower():
                                    tag = 'PERSON'
                                elif 'private' in prov_text.lower():
                                    tag = 'PERSON'
                                else:
                                    tag = 'OTHER'
                                entities = {"OTHER": [prov_text]}
                            for i, entity_ls in enumerate(entities.values()):
                                if (list(entities.keys())[i] != 'DATE'):
                                    for e in entity_ls:
                                        prov_text = prov_text.replace(e, utils.remove_dots(e))

                            events = extract_events_dot(prov_text)

                            # Extract named entities from the events
                            artwork_events = []

                            for event in events:
                                event = event.replace('|', '').strip()
                                ev_data = {'label': event}

                                ev_entities, old_model, nlp = utils.extract_named_entities(event, spacy_model,
                                                                                           old_model, nlp)
                                if not ev_entities:
                                    if 'anonymous' in str(event).lower():
                                        tag = 'PERSON'
                                    elif 'private' in str(event).lower():
                                        tag = 'PERSON'
                                    else:
                                        tag = 'OTHER'
                                    ev_entities = {tag: [event]}
                                for entity_type in ev_entities.keys():
                                    ev_data[entity_type] = ev_entities[entity_type]

                                artwork_events.append(ev_data)

                                new_artwork_events = []

                                for event in artwork_events:  # Create a copy to avoid dictionary modification during iteration
                                    new_elems = []
                                    label_value = None  # Initialize a variable to store the 'label' value
                                    for k, v in event.items():
                                        if k == 'label':  # Check if the key is 'label'
                                            label_value = v
                                            new_elems.append((k, v))
                                        if isinstance(v, str):
                                            if 'collection' in v.lower():
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
                                                if 'collection' in element.lower():
                                                    if key == 'label':
                                                        if len(event) == 1:
                                                            new_elems.append(('ORG', element))
                                                            new_elems.append(('label', element))
                                                    else:
                                                        new_elems.append(('ORG', element))
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

                                    output_dict['label'] = label_value  # Restore the 'label' key-value pair
                                    event.clear()
                                    event.update(output_dict)

                        events_of_artworks.append(artwork_events)

                else:  # This is the correct placement for the else block
                    events_of_artworks = ''

            except Exception as e:
                # Handle specific exceptions and log them for better debugging
                print(f"Error in {str(e)}")

            gc.collect()  # Perform garbage collection to release memory inside the loop

            # Move these lines outside the inner loop
            json_object["events"] = events_of_artworks
            json_object_with_index = {str(artwork_index): json_object}
            final_output.append(json_object_with_index)
            artwork_index += 1
            with open(event_output_file, 'a', encoding='utf-8') as output_f:
                output_f.write(json.dumps(json_object_with_index, ensure_ascii=False) + '\n')

                # Increment the iteration counter
            iteration_counter += 1

            # Check if the counter is a multiple of 100
            if iteration_counter % 100 == 0:
                print(f"Last events added for iteration {iteration_counter}: {json_object_with_index}")

    with open(event_output_file, 'a', encoding='utf-8') as output_f:
        for json_object in final_output:
            output_f.write(json.dumps(json_object, ensure_ascii=False) + '\n')

    return artwork_index




import re

def detect_language(provenance_text, language_cache):
    """
    Detect the language of provenance text.

    Parameters
    ----------
    provenance_text : str
        Provenance text.
    language_cache : dict
        A cache for storing detected languages.

    Returns
    -------
    detected_lang : str
        Detected language code (e.g., 'en' for English).
    spacy_model : str
        Spacy model name corresponding to the detected language.
    language_cache : dict
        Updated language cache.
    """
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




def add_lang(file, language_cache):
    """
    Add language information to the provenance text in a JSON file.

    Parameters
    ----------
    file : str
        Path to the input JSON file.
    language_cache : dict
        A cache for storing detected languages.

    Returns
    -------
    data : dict
        Updated JSON data with language information.
    """
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

#@profile


if __name__ == "__main__":  
    with open('datasets/final_db.json','r',encoding='utf-8') as f:
        file = json.load(f)

    artworks = list(file['lots'].values())
     
    artwork_index = batch_extract_store_events(artworks,batch_size=50)
            
    print("Job done")
     
    

  
    

  
    
