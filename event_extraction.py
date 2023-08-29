# -*- coding: utf-8 -*-
import os
import json
import re
import spacy
from src.utils import utils
from tqdm.notebook import tqdm

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
    

  
    

  
    
