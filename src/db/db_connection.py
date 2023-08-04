# -*- coding: utf-8 -*-

import sys
sys.path.append("..")
from neo4j import GraphDatabase
from setup import config as cfg


class DB_Connection(object):
    
    def __init__(self):
        """
        Initialize the connection.

        Returns
        -------
        None.

        """
        uri = cfg.neo4j["uri"]
        username = cfg.neo4j["username"]
        password = cfg.neo4j["password"]
        encrypted = cfg.neo4j["encrypted"]
        
        self._driver = GraphDatabase.driver(uri, auth=(username, password), encrypted=encrypted) 
        self._success_status = 0
        self._error_status = -1
            
        self.event_subject = ["ORG", "PERSON", "WORK_OF_ART", "FAC", "EVENT", "NORP", "LANGUAGE", "PRODUCT", "LAW"]
        self.event_location = ["LOC", "GPE"]
        self.event_date = ["DATE", "START_DATE", "END_DATE"]
   
    


    def close(self):
        """
        Close connection.

        Returns
        -------
        None.

        """
        self._driver.close()
        

    def clear(self):
        """
        Removes all the data.

        Returns
        -------
        None.

        """
        with self._driver.session() as session:
            tx = session.begin_transaction()
            tx.run("MATCH (n) DETACH DELETE n;")
            tx.commit() 
   
        print("Deleted all.")
        
    def take_hashes(self):
        with self._driver.session() as session:
            query = f"MATCH (a:artwork) RETURN a.artwork_id"
                    
            tx = session.begin_transaction()
            c = tx.run(query)
            c = c.data()
            tx.commit() 
                     
            
        return c

    def check_db(self):
        with self._driver.session() as session:
            tx = session.begin_transaction()
            query = "USE prova MATCH (n) RETURN count(n)"
            result = tx.run(query)
            results = result.data()
            datum = results[0]['count(n)']
                
        return datum

    def additionalQuery(self, query):
        with self._driver.session() as session:
            tx = session.begin_transaction()
            tx.run(query)
            tx.commit()

        return ('Rels merged')
    
            
    def add_node(self, node_type, node_id, data):
        """
        Add node to the KG.
        
        Parameters
        ----------
        node_type : STR
            NODE TYPE.
        node_id : STR
            NODE ID.              
        node_label : STR
            NODE LABEL.
        data : LIST
            PROPERTIES AND VALUES.

        Returns
        -------
        INT
            STATUS.

        """

        
                



        with self._driver.session() as session:
            props = data[0]
            vals = data[1]
            
            
            tx = session.begin_transaction()
            query = f"CREATE (a:{node_type} "
            query += "{"
            query += f"{node_type}_id: '{node_id}'"
            
            for idx, property_name in enumerate(props):
                if property_name == "DATE":
                    if type(vals[idx]) is list:
                        query += ", " + property_name + ": " + str(vals[idx]) + ""  
                    elif type(vals[idx]) is int:
                        query += ", " + property_name + ": " + str(vals[idx]) + "" 
                    else:
                        query += ", " + property_name + ": \"" + str(vals[idx]).replace('\"', '\'') + "\""     
                else:    
                    query += ", " + property_name + ": \"" + str(vals[idx]).replace('\"', '\'') + "\""
                    
            query += "})"
            
            try:
                tx.run(query)
                tx.commit()
                
            except Exception as e:
                print("Exception: {0}".format(e))
                return self._error_status
        
    
        return self._success_status                   

    
    def get_node(self, node_type, node_label, data):
        """
        Get node.

        Parameters
        ----------
        node_type : STR
            NODE TYPE.
        node_label : STR
            NODE LABEL.
        data : LIST
            PROPERTIES AND VALUES.

        Returns
        -------
        INT
            STATUS.

        """
        with self._driver.session() as session:
            tx = session.begin_transaction()
            
            query = f"MATCH (a:{node_type}) WHERE a.label= \"{node_label}\" "
            query += f"RETURN a.{node_type}_id as id"
            
            try:
                result = tx.run(query)
                for record in result:
                    return record["id"] 
                
            except Exception as e:
                print("Exception: {0}".format(e))
                return self._error_status()
            
        return self._success_status
    
    
    def get_similar_event(self, data):
        """
        Get similar event.

        Parameters
        ----------
        data : LIST
            PROPERTIES AND VALUES.

        Returns
        -------
        INT
            STATUS.

        """
        with self._driver.session() as session:
            output = []
            
            props = data[0]
            vals = data[1]
            
            ev_label = ""  
            ev_date = []
            
            for idx, property_name in enumerate(props):
                if property_name == "DATE":
                    ev_date = vals[idx] 
                if property_name == "label":
                    ev_label = ''.join(c for c in vals[idx] if c not in '"')
                    
            tx = session.begin_transaction()
            
            query = "MATCH (a:event) "
            query += f"WHERE a.label = \"{ev_label}\" "
            #OR ("
            
            # Match event subject
            #query += "(a." + self.event_subject[0] + " in " + str(vals)
            #for attr in self.event_subject[1:]:
            #    query += " OR a." + str(attr) + " in " + str(vals)
            
            # Match event location    
            #query += ") AND (a." + self.event_location[0] + " in " + str(vals)   
            #for attr in self.event_location[1:]:
            #    query += " OR a." + str(attr) + " in " + str(vals) 
            
            # Match event date
            #query += ") AND "
            #if type (ev_date) is list and len(ev_date) > 1:
            #    query += "((a.DATE >= " + str(ev_date[0]) + " AND a.DATE =< " + str(ev_date[1]) + ") OR (a.START_DATE = " + str(ev_date[0]) + " AND a.END_DATE = " + str(ev_date[1]) + ")) "
            #elif type (ev_date) is int:
            #    query += "((a.START_DATE <= " + str(ev_date) + " AND a.END_DATE >= " + str(ev_date) + ") OR a.DATE = " + str(ev_date) + ") "
            #elif type (ev_date) is str:
            #    query += "a.DATE in " + str(vals)
            #else:
            #    query += "a.DATE is null "
                
            #query += ") RETURN a.event_id as id"
            query +=  "RETURN a.event_id as id"
            try:
                result = tx.run(query)
                for record in result:
                    output.append(record['id'])
                return output   
            
            except Exception as e:
                print("Exception: {0}".format(e))
                return self._error_status 
            
        return self._success_status
    
    
    def link_two_nodes(self, a_type, a_id, b_type, b_id):
        """
        Link two nodes with a relation RELATED_TO.

        Parameters
        ----------
        a_type : STR
            HEAD NODE TYPE.
        a_id : STR
            HEAD NODE ID.
        b_type : STR
            TAIL NODE TYPE.
        b_id : STR
            TAIL NODE ID.

        Returns
        -------
        INT
            STATUS.

        """
        with self._driver.session() as session: 
            tx = session.begin_transaction()
            query = f"MATCH (a:{a_type}), (b:{b_type}) WHERE a.{a_type}_id='{a_id}' and b.{b_type}_id='{b_id}' CREATE (a)<-[:PARTECIPATED_TO]-(b) "
    
            try:
                tx.run(query)
                tx.commit()
                
            except Exception as e:
                print("Exception: {0}".format(e))
                return self._error_status
        return self._success_status

    def actorsFromEvent(self):
        propertiesDates = ['DATE','END_DATE','START_DATE']
        propertiesActors = ['ORG','PERSON']
        propertiesLocations = ['GPE','LANGUAGE','LOC','NORP']
        propertiesOther = ['EVENT','FAC','LAW','MONEY','ORDINAL','PRODUCT','WORK_OF_ART']
        for i in propertiesDates:
            query = "MATCH (e:event) WHERE "
            query += f"e.{i} IS NOT NULL WITH e.{i} as {i}, collect(e) AS events MERGE (g:date "
            query += "{name:"
            query += f" {i}"
            query += '''}) FOREACH (event in events |
                MERGE (event)-[:HAS_'''
            query += f"{i}]->(g) )"
                    
            with self._driver.session() as session:
                tx = session. begin_transaction()
                tx.run(query)
                tx.commit()
        for i in propertiesLocations:
            query = "MATCH (e:event) WHERE "
            query += f"e.{i} IS NOT NULL WITH e.{i} as {i}, collect(e) AS events MERGE (g:location "
            query += "{name:"
            query += f" {i}"
            query += '''}) FOREACH (event in events |
                MERGE (event)-[:HAS_LOCATION]->(g) )'''      
            with self._driver.session() as session:
                tx = session. begin_transaction()
                tx.run(query)
                tx.commit()
        for i in propertiesActors:
            query = "MATCH (e:event) WHERE "
            query += f"e.{i} IS NOT NULL WITH e.{i} as {i}, collect(e) AS events MERGE (g:actor "
            query += "{name:"
            query += f" {i}"
            query += '''}) FOREACH (event in events |
                MERGE (event)<-[:PARTECIPATED_TO]-(g) )'''      
            with self._driver.session() as session:
                tx = session. begin_transaction()
                tx.run(query)
                tx.commit()
        for i in propertiesOther:
            query = "MATCH (e:event) WHERE "
            query += f"e.{i} IS NOT NULL WITH e.{i} as {i}, collect(e) AS events MERGE (g:other "
            query += "{name:"
            query += f" {i}"
            query += '''}) FOREACH (event in events |
                MERGE (event)<-[:RELATED_TO]-(g) )'''      
            with self._driver.session() as session:
                tx = session. begin_transaction()
                tx.run(query)
                tx.commit()
            
        
                            
