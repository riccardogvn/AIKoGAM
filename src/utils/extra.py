def nodeName(graph, node):
    name = graph.nodes[node]['properties']['name']
    return name


def printTexTab(dictionary, file):
    """
    Print a dictionary as a LaTeX table.

    Parameters:
    - dictionary: Dictionary to be printed
    - file: File to save the LaTeX table
    """
    latex_content = """
    \\begin{tabular}{|l|r|} 
    \\hline
    \\textbf{Metric} & \\textbf{Value} \\\\
    \\hline
    """
    for k, v in dictionary.items():
        latex_content += f"{k} & {v:.4f} \\\\ \n"
    latex_content += "\\hline\n\\end{tabular}\n"
    with open(file, "w") as file:
        file.write(latex_content)
    print(f"TeX file saved at {file}")


def plot_scatter(x, y, x_label, y_label, subplot_position, order_letter):
    from scipy.stats import linregress
    """
    Plot a scatter plot with regression line.

    Parameters:
    - x: X-axis data
    - y: Y-axis data
    - x_label: Label for X-axis
    - y_label: Label for Y-axis
    - subplot_position: Position of the subplot
    """
    plt.subplot(subplot_position)
    plt.scatter(x, y, alpha=0.5)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    slope, intercept, r, _, _ = linregress(x, y)
    plt.plot(x, slope * x + intercept, color='red', linestyle='--', label=f"Slope = {slope:.2f}")
    plt.legend()

    plt.title(f"{order_letter}) {x_label} vs {y_label} (Pearson's r = {r:.2f})")


# Create scatter plots

def printTexTab3(centrality_dict, centrality_name, file, graph):
    """
    Print the top nodes based on centrality values in LaTeX format.

    Parameters:
    - centrality_dict: Dictionary of centrality values
    - centrality_name: Name of the centrality metric
    - file: File to save the LaTeX table
    """
    sorted_nodes = sorted(centrality_dict, key=centrality_dict.get, reverse=True)
    top_nodes = sorted_nodes[:50]
    header = '''
    \\begin{tabular}{|r|r|l|} 
    \\textbf{Node ID} & \\textbf{Centrality Value} & \\textbf{Name}
    \\hline 
    '''
    for node in top_nodes:
        centrality_value = centrality_dict[node]
        node_label = graph.nodes[node]['properties']['name']
        header += f"{node[:6]}... & {centrality_value:.4f} & {node_label}"
        header += "\\\\"
    header += '''
    \hline 
    \end{tabular}
    '''
    with open(file, 'w') as f:
        f.write(header)
    print(f"TeX file saved at {file}")

def export_to_neo4j(graph, session):
    """
    Export a NetworkX graph to Neo4j.

    Parameters:
    - graph: NetworkX graph
    - session: Neo4j session
    """
    # Unique constraint on node id
    # session.run("CREATE CONSTRAINT FOR (n:actor) REQUIRE n.id IS UNIQUE")

    # Iterate through nodes
    id = 0
    for node in tqdm(graph.nodes(data=True), desc='Processing nodes'):
        node_id, properties = node
        label = properties.get('label', 'Node')  # Adjust as needed
        props = properties.get('properties', {})
        name = props.get('name')
        # Adjust as needed
        id += 1

        # Cypher query to create a node or match existing node
        query = (
            f'MERGE (n:{label} {{id: "{node_id}"}}) '
            f'SET n.name = "{name}"'
        )
        session.run(query)

    # Iterate through edges
    for edge in tqdm(graph.edges(data=True), desc='Processing edges'):
        start_node, end_node, properties = edge
        relationship_type = properties.get('label', 'CONNECTED')  # Adjust as needed

        # Cypher query to create a relationship between nodes
        query = (
            f"MATCH (a),(b) WHERE a.id = '{start_node}' AND b.id = '{end_node}' "
            f"CREATE (a)-[r:{relationship_type}]->(b)"
        )
        session.run(query)


def refactoring(string, graph):
    old_actors_nodes = set()

    # Identify actor nodes with 'Sotheby's' in their name
    for node in tqdm(subgraph.nodes(), desc=f"Identifying {string.capitalize()} nodes"):
        if graph.nodes[node]['label'] == 'actor':
            name = graph.nodes[node]['properties']['name']
            if string in name.lower():
                old_actors_nodes.add(node)

    # Create the super node and update relationships
    # Update relationships for super node
    if old_actors_nodes:
        for actor in tqdm(old_actors_nodes, desc=f'Updating relationships for {string.capitalize()}'):
            neighbors = list(graph.neighbors(actor))
            for neighbor in neighbors:
                edges = graph.edges(actor, neighbor)
                for edge in edges:
                    graph.add_edge(string.capitalize(), neighbor, attr_dict=edge[2])

        graph.add_edges_from(edges_to_add)
        graph.remove_nodes_from(nodes_to_remove)

    return graph

def newNodeId(subgraph):
    all_ids = {node for node in subgraph.nodes() if isinstance(node, int)}
    new_node_id = str(min(set(range(1, max(all_ids) + 2)) - all_ids))
    return new_node_id


def generate_ngrams(string, n):
    """
    Generate n-grams of length n from a given string.

    Parameters:
    string (str): The input string from which n-grams will be generated.
    n (int): The length of each n-gram.

    Returns:
    list: A list of n-grams.
    """
    return [string[i:i + n] for i in range(len(string) - n + 1)]


def exception_append(shorter_string, merges, ngram_index):
    """
    Append a string to the list of merges if it doesn't meet any exception criteria.
    Also, check if the string's n-grams match with any existing strings using the n-gram index.

    Parameters:
    shorter_string (str): The string to be added to the merges list.
    merges (list): The list of merged strings.
    ngram_index (defaultdict): The n-gram index built from build_ngram_index function.

    Returns:
    list: The updated merges list.
    """
    if shorter_string in merges or shorter_string.lower() in exceptionsin or shorter_string.lower() in exceptionsequals:
        return merges
    # Check if any of the n-grams of the new string are present in the n-gram index
    ngrams = generate_ngrams(shorter_string, 3)  # Using 3-grams for comparison
    for ngram in ngrams:
        if ngram in ngram_index:
            print(f"Similarity found for '{shorter_string}': {ngram_index[ngram]}")
            break
    merges.append(shorter_string)
    print(f"Added to merges: {shorter_string}")
    return merges


def build_ngram_index(strings, n=3):
    """
    Build an n-gram index for a list of strings.
    Each n-gram maps to a list of strings containing that n-gram.

    Parameters:
    strings (list): List of strings to build the n-gram index from.
    n (int): The length of each n-gram.

    Returns:
    defaultdict: A defaultdict containing the n-gram index.
    """
    ngram_index = defaultdict(list)
    for string in strings:
        ngrams = generate_ngrams(string, n)
        for ngram in ngrams:
            ngram_index[ngram].append(string)
    return ngram_index


def find_similar_nodes_b(graph, merges, threshold=0.8):
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
    ngram_index = build_ngram_index(merges)

    for node1 in tqdm(graph.nodes(), desc='Calculating similarity'):
        if graph.nodes[node1]['label'] == 'actor':
            name1 = graph.nodes[node1]['properties']['name']
            normalized_name1 = normalize_name(name1)

            for node2 in graph.nodes():
                if node1 != node2 and graph.nodes[node2]['label'] == 'actor':
                    name2 = graph.nodes[node2]['properties']['name']
                    normalized_name2 = normalize_name(name2)

                    if normalized_name2 == normalized_name1:
                        shorter_string = normalized_name1 if len(normalized_name1) < len(
                            normalized_name2) else normalized_name2
                        shorter_string = shorter_string.title()
                        merges = exception_append(shorter_string, merges, ngram_index)
                    else:
                        similarity = fuzz.ratio(normalized_name1, normalized_name2) / 100
                        if similarity >= threshold:
                            similar_nodes.append((node1, node2, similarity))
                            similarity = round(similarity, 2)
                            if similarity == 1.00:
                                shorter_string = normalized_name1 if len(normalized_name1) < len(
                                    normalized_name2) else normalized_name2
                                shorter_string = shorter_string.title()
                                merges = exception_append(shorter_string, merges, ngram_index)

    return similar_nodes, merges


def delete_nodes_by_name(graph, target_name):
    nodes_to_delete = [node for node in graph.nodes() if
                       graph.nodes[node]['label'] == 'actor' and graph.nodes[node]['properties']['name'] == target_name]
    for node in nodes_to_delete:
        graph.remove_node(node)
    print("Node count:", graph.number_of_nodes())
    print("Edge count:", graph.number_of_edges())
    return graph


def generate_ngrams(string, n):
    """
    Generate n-grams of length n from a given string.

    Parameters:
    string (str): The input string from which n-grams will be generated.
    n (int): The length of each n-gram.

    Returns:
    list: A list of n-grams.
    """
    return [string[i:i + n] for i in range(len(string) - n + 1)]


def exception_append(shorter_string, merges, ngram_index):
    """
    Append a string to the list of merges if it doesn't meet any exception criteria.
    Also, check if the string's n-grams match with any existing strings using the n-gram index.

    Parameters:
    shorter_string (str): The string to be added to the merges list.
    merges (list): The list of merged strings.
    ngram_index (defaultdict): The n-gram index built from build_ngram_index function.

    Returns:
    list: The updated merges list.
    """
    if shorter_string in merges or shorter_string.lower() in exceptionsin or shorter_string.lower() in exceptionsequals:
        return merges
    # Check if any of the n-grams of the new string are present in the n-gram index
    ngrams = generate_ngrams(shorter_string, 3)  # Using 3-grams for comparison
    for ngram in ngrams:
        if ngram in ngram_index:
            print(f"Similarity found for '{shorter_string}': {ngram_index[ngram]}")
            break
    try:
        merges.append(shorter_string)
    except:
        merges.add(shorter_string)
    print(f"Added to merges: {shorter_string}")
    return merges


def build_ngram_index(strings, n=3):
    """
    Build an n-gram index for a list of strings.
    Each n-gram maps to a list of strings containing that n-gram.

    Parameters:
    strings (list): List of strings to build the n-gram index from.
    n (int): The length of each n-gram.

    Returns:
    defaultdict: A defaultdict containing the n-gram index.
    """
    ngram_index = defaultdict(list)
    for string in strings:
        ngrams = generate_ngrams(string, n)
        for ngram in ngrams:
            ngram_index[ngram].append(string)
    return ngram_index


def find_similar_nodes_old(graph, merges, threshold=0.8):
    """
    Find similar nodes in the graph based on fuzzy string matching.

    Parameters:
    - graph: NetworkX graph
    - merges: List of merges
    - threshold: Similarity threshold
    """
    similar_nodes = []
    ngram_index = build_ngram_index(merges)

    for node1 in tqdm(graph.nodes(), desc='Calculating similarity'):
        if graph.nodes[node1]['label'] == 'actor':
            name1 = graph.nodes[node1]['properties']['name']
            normalized_name1 = normalize_name(name1)

            for node2 in graph.nodes():
                if node1 != node2 and graph.nodes[node2]['label'] == 'actor':
                    name2 = graph.nodes[node2]['properties']['name']
                    normalized_name2 = normalize_name(name2)

                    if normalized_name2 == normalized_name1:
                        shorter_string = normalized_name1 if len(normalized_name1) < len(
                            normalized_name2) else normalized_name2
                        shorter_string = shorter_string.title()
                        merges = exception_append(shorter_string, merges, ngram_index)
                    else:
                        similarity = fuzz.ratio(normalized_name1, normalized_name2) / 100
                        if similarity >= threshold:
                            similar_nodes.append((node1, node2, similarity))
                            similarity = round(similarity, 2)
                            if similarity == 1.00:
                                shorter_string = normalized_name1 if len(normalized_name1) < len(
                                    normalized_name2) else normalized_name2
                                shorter_string = shorter_string.title()
                                merges = exception_append(shorter_string, merges, ngram_index)

    return similar_nodes, merges


def printSimilars(listoftuples):
    """
    Print similar nodes and prompt the user for merging decisions.

    Parameters:
    - listoftuples: List of tuples containing similar nodes
    """
    tomerge = []
    num = 0
    for x in listoftuples:
        num = num + 1
        print(num)
        print(subgraph.nodes[x[0]]['properties']['name'])
        print(subgraph.nodes[x[1]]['properties']['name'])
        question = input('Need them to be merged? y or n')
        if question == 'y':
            tomerge.append((x[0], x[1]))
        else:
            pass
    return tomerge


def changeName(list, graph):
    """
    Change the name of nodes based on user input.

    Parameters:
    - list: List of tuples containing nodes to be renamed
    - graph: NetworkX graph
    """
    newlist = []
    for x in list:
        print(subgraph.nodes[x[0]]['properties']['name'])
        print(subgraph.nodes[x[1]]['properties']['name'])
        question = input('Need them to be merged? y or n')
        if question == 'y':
            newlist.append(x)
            question2 = input('How they will be called?')
            graph.nodes[x[0]]['properties']['name'] = question2
            graph.nodes[x[1]]['properties']['name'] = question2
        else:
            pass
    return newlist


def findNode(target_name, subgraph):
    """
    Find a node in the subgraph based on the target name.

    Parameters:
    - target_name: Target name to search for
    - subgraph: NetworkX subgraph
    """
    found_node = None
    if len(target_name) > 1:
        for node in subgraph.nodes():
            properties = subgraph.nodes[node].get('properties')
            if properties is not None:
                node_name = properties.get('name')
                if node_name is not None and target_name.lower() in node_name.lower():
                    found_node = node
                    print(subgraph.nodes[found_node])
                else:
                    pass
    else:
        for node in subgraph.nodes():
            properties = subgraph.nodes[node].get('properties')
            if properties is not None:
                node_name = properties.get('name')
                if node_name is not None and node_name.lower() == target_name.lower():
                    found_node = node
                    print(subgraph.nodes[found_node])
                else:
                    pass

    if found_node is None:
        print('none')

    return found_node


def get_connected_nodes(graph, starting_node, num_nodes):
    """
    Perform a breadth-first search to collect connected nodes.

    Parameters:
    - graph: NetworkX graph
    - starting_node: Node to start the search from
    - num_nodes: Number of nodes to collect
    """
    connected_nodes = set()
    queue = [starting_node]

    while queue and len(connected_nodes) < num_nodes:
        current_node = queue.pop(0)
        connected_nodes.add(current_node)
        neighbors = list(graph.neighbors(current_node))
        for neighbor in neighbors:
            if neighbor not in connected_nodes:
                queue.append(neighbor)

    return connected_nodes


def merge_nodes_by_multnode(graph, nodes, count):
    """
    Merge nodes in the graph based on a list of node names.

    Parameters:
    - graph: NetworkX graph
    - nodes: List of node names to be merged
    - count: Counter for tracking the number of iterations
    """
    norm_nodes = [normalize_name(i) for i in nodes]

    nodes_to_merge = [node for node in graph.nodes() if graph.nodes[node]['label'] == 'actor' and normalize_name(
        graph.nodes[node]['properties']['name']) in norm_nodes]
    print(nodes_to_merge)
    if nodes_to_merge:
        head = nodes_to_merge[0]

        for node in nodes_to_merge[1:]:
            neighbors = list(graph.neighbors(node))
            for neighbor in neighbors:
                if graph.nodes[neighbor]['label'] == 'atwork':
                    if not graph.has_edge(head, neighbor):
                        graph.add_edge(head, neighbor, label='dealt_with', direction='forward')

            count += 1
            graph.remove_node(node)

    return graph, count


def get_event_id(ev_data):
    props = ev_data[0]
    vals = ev_data[1]
    ev_data_dict = {}
    for idx, prop_name in enumerate(props):
        ev_data_dict[prop_name] = vals[idx]
    event_id = dict_hash(ev_data_dict)
    return event_id

