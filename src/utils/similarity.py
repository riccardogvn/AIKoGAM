#similarity.py
from tqdm.notebook import tqdm
from unidecode import unidecode
from fuzzywuzzy import fuzz
from collections import defaultdict
import networkx as nx
from src.utils.cleaning import merge_nodes_same_name, merge_nodes_by_node, normalize_name, merge_nodes_with_name
from setup.config import TO_REMOVE, PROPERTY_PATTERN, COLLECTION_PATTERN
from datasketch import MinHash, MinHashLSH
import re


def removePatterns(graph):
    removePattern(graph)
    removeVar(graph)

def removePattern(graph):
    for node in graph.nodes():
        if graph.nodes[node]['label'] == 'actor':
            name = graph.nodes[node]['properties']['name'].lower()
            for pattern in PROPERTY_PATTERN:
                if pattern.lower() in name:
                    name = name.replace(pattern.lower(),'')
            for pattern in COLLECTION_PATTERN:
                if pattern.lower() in name:
                    name = name.replace(pattern.lower(),'')
            graph.nodes[node]['properties']['name'] = name

def removeVar(graph):
    for node in graph.nodes():
        if graph.nodes[node]['label'] == 'actor':
            name = graph.nodes[node]['properties']['name']

            # Define the regex patterns
            pattern_the = re.compile(r'^(the|The)\s', re.IGNORECASE)
            pattern_ltd = re.compile(r'\bltd\b|,\sltd\b', re.IGNORECASE)

            # Check if the 'the ' or 'The ' pattern matches the beginning of the string
            match_the = pattern_the.match(name)

            if match_the:
                # If there's a match, replace 'the ' or 'The ' with ''
                name = re.sub(pattern_the, '', name)

            # Check if the 'ltd' or ', ltd' pattern is present
            match_ltd = pattern_ltd.search(name)

            if match_ltd:
                # If there's a match, replace 'ltd' or ', ltd' with ''
                name = re.sub(pattern_ltd, '', name)

            # Update the graph with the modified name
            graph.nodes[node]['properties']['name'] = name

def find_similar_nodes(graph, merges, threshold=0.8):
    """
    Find nodes with similar names in the graph and update the list of merges accordingly.
    Also, utilize the n-gram index to identify similar strings.

    Parameters:
    graph (NetworkX Graph): The graph containing nodes to compare.
    merges (list): The list of merged strings.
    threshold (float, optional): The similarity threshold for node comparison.

    Returns:
    tuple: A tuple containing the list of similar nodes and the updated merges list.
    """
    similar_nodes = []
    lsh = MinHashLSH(threshold=threshold, num_perm=128)

    # Build MinHash for each node
    minhashes = {}
    for node_id, data in tqdm(graph.nodes(data=True), desc='Building MinHash'):
        if data['label'] == 'actor':
            name = normalize_name(data['properties']['name'])
            minhash = build_minhash(name)
            minhashes[node_id] = minhash
            lsh.insert(node_id, minhash)

    # Query LSH for similar nodes
    total_nodes = len(graph.nodes())
    for node_id1, data1 in tqdm(graph.nodes(data=True), total=total_nodes, desc='Querying LSH'):
        if data1['label'] == 'actor':
            minhash1 = minhashes[node_id1]
            results = lsh.query(minhash1)
            for node_id2 in results:
                if node_id1 != node_id2:
                    similarity = minhash1.jaccard(minhashes[node_id2])
                    similar_nodes.append((node_id1, node_id2, similarity))

    return similar_nodes, merges

def build_minhash(name):
    """
    Build MinHash for a given name.

    Parameters:
    - name: Name for which MinHash is built
    """
    minhash = MinHash()
    for word in name.split():
        minhash.update(word.encode('utf-8'))
    return minhash

def similarityCheckRemoval(similar_nodes, graph, count=0):
    similarity_check = similar_nodes
    subgraph_merg = graph.copy()
    # instantiate a list where to store nodes merged for similarity
    to_remove_pairs = []
    # instantiate a list where to store eventual nodes that don't have to be changed
    excluded_labels = []
    # instantiate a list where to store the nodes to remove from the graph after merging
    nodes_to_remove = []
    for node1, node2, similarity in similarity_check:
        if node1 in subgraph_merg.nodes and node2 in subgraph_merg.nodes:
            label1 = subgraph_merg.nodes[node1]['properties']['name'].lower().strip()
            label2 = subgraph_merg.nodes[node2]['properties']['name'].lower().strip()
            if similarity == 1.0:
                graph, count, nodes_to_remove = merge_nodes_by_node(graph, node1, node2, count, nodes_to_remove)
                # Add to the list of nodes to remove from similarity_check
                to_remove_pairs.extend([(node1, node2, similarity), (node2, node1, similarity)])
            else:
                print(f"Label1: {label1}, Label2: {label2}, Similarity: {similarity}")
                answer = input('Add to merge? (y/n): ')
                if answer.lower() == 'e':
                    excluded_labels.add(label1)
                if answer.lower() == 'y':
                    graph, count, nodes_to_remove = merge_nodes_by_node(graph, node1, node2, count, nodes_to_remove)
                    # Add to the list of nodes to remove from similarity_check
                    to_remove_pairs.extend([(node1, node2, similarity), (node2, node1, similarity)])

                    # Remove processed triples from similarity_check
    similarity_check = [triple for triple in similarity_check if triple not in to_remove_pairs]
    # Remove processed nodes from the graph after merging
    for i in nodes_to_remove:
        subgraph.remove_node(i)

    print('Nodes merged:', count)
    excls = []
    for node1, node2, similarity in similar_nodes:
        if node1 in graph.nodes and node2 in graph.nodes:
            label1 = graph.nodes[node1]['properties']['name'].lower().strip()
            label2 = graph.nodes[node2]['properties']['name'].lower().strip()
            # Check if label1 is in the list of excluded labels
            if label1 in excluded_labels:
                excls.append((node1, node2, similarity))
                print(f"Label1: {label1} is excluded from further checks.")
                continue
            for pattern in TO_REMOVE:
                if pattern.match(label1) is not None:
                    excls.append((node1, node2, similarity))
                    print(f"Match found for label1: {label1}")
                    break
    return excls, count

def checkManual(mergesraw, graph):
    merges = []
    mergings = []
    for x in mergesraw:
        mergings.append(x.lower())
    mergy = list(set(mergings))
    excluded = []
    count = 0
    for name in mergy:
        if len(name.split(' ')) == 1:
            print(name)
            answer = input(f"{name} is to be merged?")
            if answer == 'y':
                merges.append(name)
                mergy.remove(name)
                count += 1
            else:
                excluded.append(name)
                mergy.remove(name)
        else:
            merges.append(name)
            mergy.remove(name)
            print(f"Going to merge {len(merges)} nodes")
            count += 1

    sub = subgraph.copy()

    # Refactor nodes
    nodes_and_edges(sub)
    for x in merges:
        merge_nodes_with_name(sub, x, count)
    nodes_and_edges(sub)

    return sub, merges














