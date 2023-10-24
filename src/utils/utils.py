# -*- coding: utf-8 -*-
import os  # Add this line for the 'os' module
import re
import logging
import spacy
from spacy.cli.download import download
import pickle
# Set up logging
logging.basicConfig(filename='error_log.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')
import json
import hashlib
from typing import Dict, Any
from setup.config import SPACY_MAPPINGS, ENTITIES_MAPPING

def split_text(text):
    """Split the given text into sentences and phrases."""
    # Split the text using regex patterns
    sentences = re.split(r'(<br>|\r\n|\r|\n|<p>|</p>|<br>|<[^>]+>)', text)

    # Remove any leading or trailing whitespaces from each sentence
    sentences = [sentence.strip() if sentence else '' for sentence in sentences]

    # Remove empty sentences
    sentences = [sentence for sentence in sentences if sentence]

    # Split sentences into phrases using semicolons as stop phrases
    phrases = []
    for sentence in sentences:
        phrases.extend([phrase.strip() for phrase in re.split(r';', sentence) if phrase.strip()])

    return phrases

def openJson(path):
    if os.path.isfile(path):
        with open(path,'r',encoding='utf-8') as f:
            file = json.load(f)
    else:
        file = []

    return file

def saveJson(file,path):
    with open(path,'w') as f:
        json.dump(file,f)

def pR():
    excl = ['Degree Centrality (DC)','Eigenvector Centrality (EC)','Betweennes Centrality (BC)','Closeness Centrality (CC)']
    for k,v in resulting_values.items():
        if k not in excl:
            prk = k
            prv = v
        else:
            prk = k
            prv = '...'
    print(prk,' : ',prv)

def format_time(fractional_seconds):
    # Convert fractional seconds to hours, minutes, and seconds
    hours, remainder = divmod(int(fractional_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    # Build the formatted string
    time_components = []

    if hours > 0:
        time_components.append(f"{int(hours)}:{int(minutes):02}:{int(seconds):02} hours")
    elif minutes > 0:
        time_components.append(f"{int(minutes):02}:{int(seconds):02} minutes")
    elif seconds > 0:
        time_components.append(f"{int(seconds):02} seconds")
    else:
        time_components.append("0 seconds")

    formatted_time = ' '.join(time_components)
    return formatted_time

def dict_hash(dictionary: Dict[str, Any]) -> str:
    """sha512 hash of a dictionary."""
    dhash = hashlib.sha512()
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()

def extract_duration(text):
    '''
    EXTRACT DURATION FROM TEXT USING YYYY-YYYY FORMAT.

    Parameters
    ----------
    text : STR
        TEXT.

    Returns
    -------
    found_duration : STR
        EXTRACTED DURATION in YYYY-YYYY FORMAT.

    '''
    found_duration = re.findall('\d\d\d\ds?\s?-?\s?\d\d\d\ds?', text)
    found_duration = [s.strip() for s in found_duration]
    return found_duration

def extract_year(text):
    '''
    EXTRACT YEAR FROM TEXT USING YYYY FORMAT.

    Parameters
    ----------
    text : STR
        TEXT.

    Returns
    -------
    found_year : STR
        EXTRACTED YEAR in YYYY FORMAT.

    '''
    found_year = re.findall('\d\d\d\d', text)
    found_year = [s.strip() for s in found_year]
    return found_year

def extract_century(text):
    '''
    EXTRACT CENTURY FROM TEXT.

    Parameters
    ----------
    text : STR
        TEXT.

    Returns
    -------
    found_century : STR
        EXTRACTED CENTURY.

    '''
    found_century = re.findall('\d\dth', text)
    found_century = [s.strip() for s in found_century]
    return found_century

def year_from_century(text):
    '''
    CALCULATE YEAR RANGE FROM CENTURY.

    Parameters
    ----------
    text : STR
        TEXT.

    Returns
    -------
    year_range : LIST
        EXTRACTED YEAR RANGE.

    '''
    century = int(re.findall('\d\d', text)[0])
    year_range = [((century - 1) * 100) + 1, century * 100]
    return year_range

def extract_named_entities(text, spacy_model, old_model, nlp):
    """
    Extract named entities from text.

    Parameters
    ----------
    ner_model : LANGUAGE
        NAMED ENTITY REGOGNITION MODEL.
    text : STR
        TEXT TO EXTRACT NAMED ENTITIES FROM.

    Returns
    -------
    entities : LIST
        LIST OF NAMED ENTITIES.

    """
    if spacy_model != old_model:
        try:
            nlp = spacy.load(spacy_model)

        except OSError:

            try:
                download(spacy_model)  # Download the Spacy model
                nlp = spacy.load(spacy_model)
            except:
                nlp = spacy.load('en_core_news_md')
    else:
        spacy_model = spacy_model

    entities = {}
    for ent in nlp(text).ents:

        # First, check SPACY_MAPPINGS for entity label mapping
        for k, v in SPACY_MAPPINGS.items():
            if ent.label_ in v:
                ent.label_ = k
                break

        # Then, check ENTITIES_MAPPING for custom entity tag
        for tag, entity_list in ENTITIES_MAPPING.items():
            if ent.text.lower() in [item.lower() for item in entity_list]:
                ent.label_ = tag
                break

        label = ent.label_
        if label not in entities:
            entities[label] = [ent.text]
        else:
            entities[label].append(ent.text)
    old_model = spacy_model

    return entities, old_model, nlp

def remove_dots(text):
    '''
    Remove dots from text.

    Parameters
    ----------
    text : STR
        TEXT.

    Returns
    -------
    STR
        TEXT AFTER REMOVING THE DOTS.

    '''
    return text.replace('.','')

class Pic:
    def __init__(self, file_path):
        self.file_path = file_path

    def save(self, data):
        with open(f'{self.file_path}.pickle', 'wb') as file:
            pickle.dump(data, file)

    def load(self):
        if os.path.isfile(f'{self.file_path}.pickle'):
            with open(f'{self.file_path}.pickle', 'rb') as file:
                data = pickle.load(file)
            return data
        else:
            return None

if __name__ == "__main__":
    print(extract_year("between 1945 and 1972")[0])
    print(extract_century("the first half of the 19th century")[0])
    print(year_from_century("19th"))
    print(extract_duration("the Estate of Nicolas Landau 1960s - 1970s, Paris"))
