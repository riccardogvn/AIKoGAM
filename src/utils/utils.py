ding: utf-8 -*-
"""
Created on Wed Dec 14 10:12:37 2022

@authors: hemohamed, Riccardo Giovanelli
"""
import re


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


def extract_named_entities(ner_model, text):
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
    nlp = ner_model(text) 
    
    entities = {}
    for ent in nlp.ents:
        if ent.label_ not in entities:  
            entities[ent.label_] = [ent.text]
        else:
            entities[ent.label_].append(ent.text)
    return entities
   
 
if __name__ == "__main__":
    print(extract_year("between 1945 and 1972")[0])
    print(extract_century("the first half of the 19th century")[0])
    print(year_from_century("19th"))
    print(extract_duration("the Estate of Nicolas Landau 1960s - 1970s, Paris"))
