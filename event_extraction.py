# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 10:40:15 2022

@author: hemohamed, Riccardo Giovanelli
"""
import os
import json
import re
import spacy
from src.utils import utils


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
 
   
def extract_store_events(ner_model, directory, json_object_level = 0, event_separator = "html", artwork_index = 0):
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
    for filename in os.listdir(directory):

        # Open file
        with open(os.path.join(directory, filename), 'r') as input_f:
        
            # Returns json object as a dictionary
            data = json.load(input_f)
              
            # Iterating through the json list
            for k,v in data['lots'].items():
                json_object = v
                prov = v['lotProvenance']
                                
                              
                # Consider only artworks with provenance  
                if (prov): 
                    try:
                        events_of_artworks = []
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
                                    ev_data[entity_type] = ev_entites[entity_type][0]
                                    
                                artwork_events.append(ev_data)
                            events_of_artworks.append(artwork_events)
                            
                            # Store artwork data in JSON format
                        with open('AIKoGAM/events/events.txt', 'a', encoding="utf-8") as output_f:
                            json_object["events"] = events_of_artworks
                            json_str = json.dumps({str(artwork_index):json_object}, ensure_ascii = False)
                            output_f.write(json_str + "\n")
                            artwork_index += 1
                    except Exception:
                        with open('AIKoGAM/events/events.txt', 'a', encoding="utf-8") as output_f:
                            json_object["events"] = ""
                            json_str = json.dumps({str(artwork_index):json_object}, ensure_ascii = False)
                            output_f.write(json_str + "\n")
                            artwork_index += 1

         
    return artwork_index

def extract_store_events_from_events(ner_model, directory, json_object_level = 0, event_separator = "html", artwork_index = 0):
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
    for filename in os.listdir(directory):

        # Open file
        with open(os.path.join(directory, filename), 'r') as input_f:
        
            # Returns json object as a dictionary
            data = json.load(input_f)
            
            # Iterating through the json list
            for k,v in data['events'].items():
                json_object = v
                
                                
                            
                # Consider only artworks with provenance  
                if 'saleRef' in json_object: 
                    try:
                        events_of_artworks = []
                        # Preprocessing
                        prov = clean_provenance(json_object['saleRef'])
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
                                ev_data[entity_type] = ev_entites[entity_type][0]
                                
                            artwork_events.append(ev_data)
                        
                            
                            # Store artwork data in JSON format
                        with open('events/events_.txt', 'a', encoding="utf-8") as output_f:
                            json_object["events"] = artwork_events
                            json_str = json.dumps({str(artwork_index):json_object}, ensure_ascii = False)
                            output_f.write(json_str + "\n")
                            artwork_index += 1
                    except Exception:
                        pass

         
    return artwork_index




if __name__ == "__main__":
    
    # Named Entity Recognition (NER) model
    ner_model = spacy.load("en_core_web_md")
    
    # Handle different datasets
    ds_config = []
    ds_config.append({'ds':'AIKoGAM/datasets/'})

    artwork_index = 0
    for conf in ds_config:
        artwork_index = extract_store_events(ner_model, conf['ds'], artwork_index)
    for conf in ds_config:
        artwork_index = extract_store_events_from_events(ner_model, conf['ds'], artwork_index)
        
    print("Total number of provenance artwork", artwork_index)       
    

  
    
