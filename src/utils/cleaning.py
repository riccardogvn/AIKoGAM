#cleaning.py
from neo4j import GraphDatabase
from setup.config import (
    REPLACEMENTS,
    GRAPH_FOLDER,
    GPE,
    OTHER,
    DATES,
    GENERICS,
    uri,
    password,
    username,
    PROPERTY_PATTERN,
    COLLECTION_PATTERN,
    REGEX_PATTERNS_TO_REMOVE
)
from tqdm.notebook import tqdm
import time
import networkx as nx
from unidecode import unidecode
from collections import defaultdict
import re
import pickle
from src.utils.utils import format_time

uri = uri
password = password
username = username


def removeErrArtwork(graph):
    for node in list(graph.nodes()):
        if graph.nodes[node]['label'] == 'artwork':
            if len(graph.nodes[node]['properties']['lotLastOwner']) > 160:
                graph.remove_node(node)

def mergingNodes(graph, dictionary, count=0):
    """
    Merge nodes in the graph based on the provided dictionary.

    Parameters:
    - graph (NetworkX Graph): The graph containing nodes to be merged.
    - dictionary (dict): Dictionary where keys are new names and values are lists of names to be merged under the key.
    - count (int, optional): Initial count value. Defaults to 0.
    - batch_size (int, optional): Batch size for removing nodes. Defaults to 100.

    Returns:
    - NetworkX Graph: The modified graph after merging nodes.
    - int: The updated count value.
    """
    for k, v in tqdm(dictionary.items()):
        head = None  # Initialize head and tail outside the loop
        tail = None

        v = normalize_name(v)
        k = normalize_name(k)

        for node in graph.nodes():
            if graph.nodes[node]['label'] == 'actor':
                if normalize_name(graph.nodes[node]['properties']['name']) == v:
                    head = node
                if normalize_name(graph.nodes[node]['properties']['name']) == k:
                    tail = node

        if head and tail and tail != head:
            neighbors = list(graph.neighbors(tail))
            for neighbor in neighbors:
                if not graph.has_edge(head, neighbor):
                    graph.add_edge(head, neighbor, label='dealt_with', direction='forward')
            graph.remove_node(tail)

    return graph, count

def mergingDuples(graph):
    duplicate_nodes = defaultdict(list)
    # Identify duplicate nodes
    for node in graph.nodes():
        label = graph.nodes[node]['label']
        if label == 'actor':
            normalized_name = normalize_name(graph.nodes[node]['properties']['name'])
            # Append the node to the list corresponding to its normalized name
            duplicate_nodes[normalized_name].append(node)


    for normalized_name, nodes_list in duplicate_nodes.items():
        if len(nodes_list) > 1:
            head = list(nodes_list)[0]  # Extract the head node
            tail_nodes = list(nodes_list[1:])  # Extract the duplicate nodes

            # Move edges from duplicate nodes to the head node
            for duplicate_node in tail_nodes:  # Note the comma here to indicate unpacking a single value tuple
                if duplicate_node in graph:
                    neighbors = list(graph.neighbors(duplicate_node))
                    for neighbor in neighbors:
                        if graph.nodes[neighbor]['label'] == 'atwork':
                            if not graph.has_edge(head, neighbor):
                                graph.add_edge(head, neighbor, label='dealt_with', direction='forward')

                    graph.remove_node(duplicate_node)

def remove_nodes_by_regex_and_label(graph, regex_patterns=REGEX_PATTERNS_TO_REMOVE, property_key='name', label='actor'):
    """
    Remove nodes from the graph based on regex patterns and label.

    Parameters:
    - graph: NetworkX graph
    - regex_patterns: List of regex patterns
    - property_key: Key of the property to apply regex on
    - label: Label of the nodes to remove
    """
    nodes_to_remove = [node for node in graph.nodes() if graph.nodes[node]['label'] == label and any(re.search(pattern, graph.nodes[node]['properties'][property_key]) for pattern in regex_patterns)]
    graph.remove_nodes_from(nodes_to_remove)

def changeLabel(graph,count=0):
    """
    Change the label of nodes in the graph.

    Parameters:
    - graph: NetworkX graph
    """
    list_of_list = [GPE, OTHER, DATES, GENERICS]
    for x in list_of_list:
        for j in tqdm(x):
            delete_nodes_by_name(graph, j)
            count += 1
    return count

def normalize_name(name):
    """
    Normalize a name by converting it to lowercase and removing Unicode characters.

    Parameters:
    name (str): The input name to be normalized.

    Returns:
    str: The normalized name.
    """
    return unidecode(name.lower().strip())

def run_cypher_query(query, calctime=False):
    """
    Execute a Cypher query on the Neo4j database.

    Parameters:
    - query (str): The Cypher query to be executed.
    - calctime (bool, optional): Flag indicating whether to calculate and print elapsed time. Defaults to False.

    Returns:
    - list: List of records returned by the Cypher query.
    """
    # Record start time
    start_time = time.time()

    # Establish a connection to Neo4j
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        # Start a session
        with driver.session() as session:
            # Execute the Cypher query
            result = session.run(query)

            # Retrieve and store records
            records = [record for record in result]

    # Calculate and print elapsed time if required
    calc_time(calctime, start_time)

    # Return the list of records
    return records

def calc_time(calctime, start_time):
    """
    Calculate and print elapsed time if required.

    Parameters:
    - calctime (bool): Flag indicating whether to calculate and print elapsed time.
    - start_time (float): Start time for the calculation.
    """
    if calctime:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f'Elapsed time {format_time(execution_time)}')

def cleanNeo(calctime=True):
    """
    Clean Neo4j nodes based on specified lists of entities.

    Parameters:
    - calctime (bool, optional): Flag indicating whether to calculate and print elapsed time. Defaults to True.
    """
    # Record start time
    start_time = time.time()

    # Define a dictionary mapping label names to entity lists
    list_of_list = {'location': GPE, 'other': OTHER, 'date': DATES}

    # Iterate over the dictionary items
    for k, v in list_of_list.items():
        # Iterate over entities in the current list
        for x in tqdm(v, desc=k):
            # Construct Cypher query to match nodes by name and update labels
            query = f'MATCH (n:actor) WHERE toLower(toString(n.name)) = "{x.lower()}" SET n:{k} REMOVE n:actor'

            # Execute the Cypher query
            run_cypher_query(query)

    # Calculate and print elapsed time
    calc_time(calctime, start_time)

def generalQuery(query):
    with GraphDatabase.driver(uri, auth=(username, password), encrypted=False) as driver:
        with driver.session() as session:
            result = session.run(query)
            records = list(result)

    print(query)
    return records

def nodes_and_edges(graph, printing=True):
    """
    Print or return the number of nodes and edges in the graph.

    Parameters:
    - graph (NetworkX Graph): The graph for which to calculate nodes and edges.
    - printing (bool, optional): Flag indicating whether to print the results. Defaults to True.

    Returns:
    - tuple: A tuple containing the number of nodes and edges.
    """
    nodes = graph.number_of_nodes()
    edges = graph.number_of_edges()

    # Print the results if required
    if printing:
        print(f'Nodes: {nodes}')
        print(f'Edges: {edges}')

    # Return the results as a tuple
    return nodes, edges

def merge_nodes_same_name(graph, name, count):
    normalized_name = normalize_name(name)
    nodes_to_merge = [node for node in graph.nodes() if
                      graph.nodes[node]['label'] == 'actor' and normalized_name == normalize_name(
                          graph.nodes[node]['properties']['name'])]

    if len(nodes_to_merge) > 1:
        nodes_to_merge_names = [graph.nodes[node]['properties']['name'] for node in nodes_to_merge]
        # merged_node_id = name
        # print(merged_node_id)
        # graph.add_node(merged_node_id, label='actor', properties={'name': merged_node_id})
        for node in nodes_to_merge[1:]:
            neighbors = list(graph.neighbors(node))
            for neighbor in neighbors:
                if graph.nodes[neighbor]['label'] == 'artwork':
                    head = nodes_to_merge[0]
                    if not graph.has_edge(head, neighbor):
                        graph.add_edge(head, neighbor, label='dealt_with', direction='forward')
            count += 1
            graph.remove_node(node)


    return graph, count

def merge_nodes_by_node(graph, node1, node2, count, nodes_to_remove):
    """
    Merge nodes in the graph based on two given nodes.

    Parameters:
    - graph: NetworkX graph
    - node1: First node to merge
    - node2: Second node to merge
    - count: Counter for tracking iterations
    - nodes_to_remove: List to store nodes that should be removed from the graph

    Returns:
    - graph: Updated graph after merging nodes
    - count: Updated counter
    - nodes_to_remove: Updated list of nodes to remove
    """
    nodes_to_merge = [node1, node2]  
    if len(nodes_to_merge) > 1:
        nodes_to_merge_names = [graph.nodes[node]['properties']['name'] for node in nodes_to_merge]
        print(nodes_to_merge_names)
        for node in nodes_to_merge[1:]:
            neighbors = list(graph.neighbors(node))
            for neighbor in neighbors:
                if graph.nodes[neighbor]['label'] == 'artwork':
                    head = nodes_to_merge[0]
                    if not graph.has_edge(head, neighbor):
                        graph.add_edge(head, neighbor, label='dealt_with', direction='forward')
            count += 1
            nodes_to_remove.append(node)
            
    return graph, count, nodes_to_remove

def delete_nodes_by_name(graph, target_name):
    """
    Delete nodes from the graph based on the target name.

    Parameters:
    - graph: NetworkX graph
    - target_name: Name of nodes to be deleted
    """
    nodes_to_delete = [node for node in graph.nodes() if graph.nodes[node]['label'] == 'actor' and normalize_name(graph.nodes[node]['properties']['name']) == normalize_name(target_name)]
    for node in nodes_to_delete:
        graph.remove_node(node)
    return graph

def merge_nodes_with_name(graph, name, count):
    """
    Merge nodes in the graph based on a given name.

    Parameters:
    - graph: NetworkX graph
    - name: Name to identify nodes to merge
    - count: Counter for tracking iterations

    Returns:
    - graph: Updated graph after merging nodes
    - count: Updated counter
    """
    normalized_name = normalize_name(name)
    nodes_to_merge = [node for node in graph.nodes() if graph.nodes[node]['label'] == 'actor' and normalized_name in normalize_name(graph.nodes[node]['properties']['name'])]  
    
    if len(nodes_to_merge) > 1:
        nodes_to_merge_names = [graph.nodes[node]['properties']['name'] for node in nodes_to_merge]
        
        for node in nodes_to_merge[1:]:
            neighbors = list(graph.neighbors(node))
            for neighbor in neighbors:
                if graph.nodes[neighbor]['label'] == 'artwork':
                    head = nodes_to_merge[0]
                    if not graph.has_edge(head, neighbor):
                        graph.add_edge(head, neighbor, label='dealt_with', direction='forward')
            count += 1
            graph.remove_node(node)
    
    return graph, count































