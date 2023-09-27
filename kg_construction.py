# -*- coding: utf-8 -*-
import os
import json
from src.db import db_connection as db
from src.utils import utils
from tqdm.notebook import tqdm

def prepare_artwork_data(artwork):
    """
    Prepare the list of properties and values to be stored in a KG node of type 'artwork'.

    Parameters
    ----------
    artwork : dict
        Artwork dictionary.

    Returns
    -------
    processed_data : list
        List of properties and values.

    """    
    properties = list(artwork.keys())
    values = [str(value) for value in artwork.values()]
    processed_data = [properties, values]
    return processed_data


def prepare_event_data(event):
    """
    Propare the list of properties and values to be stored in a KG node of type 'event'.

    Parameters
    ----------
    event : DICT
        EVENT DICTIONARY.

    Returns
    -------
    proccessed_data : LIST
        LIST OF PROPERTIES AND VALUES.

    """
    properties = []
    values = []
    event_id = utils.dict_hash(event)
    event['event_id'] = event_id

    # Extract event dates (using RegEx)
    label_duration = utils.extract_duration(event['label'])
    label_years = utils.extract_year(event['label'])
    label_century = utils.extract_century(event['label'])
    
    if label_duration:
        year_range = utils.extract_year(label_duration[0])
        properties.append('START_DATE')
        values.append(int(year_range[0]))
        properties.append('END_DATE')
        values.append(int(year_range[1]))
        
    elif label_years:
        if len(label_years) == 2:
            properties.append('START_DATE')
            values.append(int(label_years[0]))
            properties.append('END_DATE')
            values.append(int(label_years[1]))  
        else:
            properties.append('DATE')
            values.append(int(label_years[0]))
            
    elif label_century:
        year_range = utils.year_from_century(label_century[0])
        properties.append('START_DATE')
        values.append(year_range[0])
        properties.append('END_DATE')
        values.append(year_range[1])
            
    # Handle other properties
    for property_name in event.keys():
        if property_name != 'DATE':
            properties.append(property_name)
            values.append(event[property_name])
     
    proccessed_data = [properties, values]
    
    
    return  proccessed_data


def main():
    """
    Main.

    Returns
    -------
    None.

    """
    db_connection = db.DB_Connection()
    #db_connection.clear()
    
    directory = "events"
    filename = "events.txt" #REMEMBER TO CHANGE BACK!!!
    file = os.path.join(directory, filename)
    
    
     
     
    with open(file, newline='', encoding="utf8") as jsonfile:
        lines = jsonfile.readlines()
        count = db_connection.check_db()
        if count == 0:
            hash_ids = ['no_data']
        else:
            hashes = db_connection.take_hashes()
            hash_ids = []
            for hash in hashes:
                hash_ids.append(hash['a.artwork_id'])
        for line in tqdm(lines):
            json_line = json.loads(line)
            for json_key in json_line.keys():
                
                json_object = json_line[str(json_key)]
                
                if json_object['lotHash'] in hash_ids:
                    pass
                else:                
                    json_object['_events'] = json_object['events']
                    json_object.pop('events')
                    json_object['events'] = []
                    for event in json_object['_events']:
                        for e in event:
                            json_object['events'].append(e)
                    json_object.pop('_events')
                    
            
                    artwork_data = prepare_artwork_data(json_object)
                    
                    # Create a new 'artwork' node
                    artwork_id = json_object['lotHash']
                    db_connection.add_node("artwork", artwork_id, artwork_data)
                    for event in json_object['events']:
                        ev_data = prepare_event_data(event)
                        event_id = ev_data[1][-1]
                        
                        
                        # Match similar 'event' nodes if exist, otherwise create a new one
                        
                        event_ids = db_connection.get_similar_event(ev_data)
                        if (event_ids):
                            for existing_event in event_ids:
                                db_connection.link_two_nodes("event", existing_event, "artwork", artwork_id)  
                        else:
                            if (not set(ev_data[0]).isdisjoint(set(db_connection.event_subject + db_connection.event_location + db_connection.event_date + db_connection.event_id))):                        
                                
                                db_connection.add_node("event", event_id, ev_data)
                                db_connection.link_two_nodes("event", event_id, "artwork", artwork_id)
        print('starting extraction of new entities from events')
        db_connection.actorsFromEvent()
    
        print('merging double rels')
        query = '''
                MATCH (p:event)<-[r:PARTECIPATED_TO]-(a:artwork)
                with [a,p] as ap, collect(r) as rels
                CALL apoc.refactor.mergeRelationships(rels)
                yield rel
                return count(rel) as result
                '''
        db_connection.additionalQuery(query)

    
   
    

if __name__ == "__main__":
    main()
    
    
    
