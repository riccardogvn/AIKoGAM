#statistical_analysis.py
from tqdm.notebook import tqdm
from setup.config import PLOTS_FOLDER
from src.utils.cleaning import normalize_name
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import time
import os
import re
from scipy.stats import pearsonr
from scipy.stats import norm
import numpy as np
from unidecode import unidecode
import pandas as pd
from pandas.plotting import table
xscale = 'log'


def barDegree(graph,filename='total_degree_plot.png',num=20,figsize=(14,7),dpi=300,xscale='log',xlabel=f'Total Degree ({xscale} scale)',ylabel='Actor Name'):
    title=f'Top {str(num)} Actors based on Total Degree'

    # Calculate total degree for each actor node
    actor_degrees = {node: graph.degree(node) for node in graph.nodes() if graph.nodes[node]['label'] == 'actor'}
    # Sort nodes by total degree in descending order
    sorted_nodes = sorted(actor_degrees, key=actor_degrees.get, reverse=True)
    # Choose the top 20 nodes (actors with highest total degree)
    top_nodes = sorted_nodes[:20]
    # Get names and total degree values for the top nodes
    #node_names = [sub.nodes[node]['properties']['name'] for node in top_nodes]
    node_names = []
    for node in top_nodes:
        node_names.append(sub.nodes[node]['properties']['name'].lower().title())
    node_total_degrees = [actor_degrees[node] for node in top_nodes]
    name_degree = dict()
    for node in top_nodes:
        name_degree[graph.nodes[node]['properties']['name']] = actor_degrees[node]
    for k,v in name_degree.items():
        print(f'{k} Degree -> {v}')

    # Create a bar plot with logarithmic scale
    plt.figure(figsize=(14, 7))  # Adjust the figure size for a 2:1 ratio
    bars = plt.barh(node_names, node_total_degrees, color='lightcoral')  # Use a light coral color
    plt.xscale(xscale)  # Set x-axis to logarithmic scale
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.gca().invert_yaxis()  # Invert y-axis to have the highest degree at the top

    # Display total degree values inside the bars
    for i, bar in enumerate(bars):
        plt.text(bar.get_width() + 20, bar.get_y() + bar.get_height()/2, f'{node_total_degrees[i]}', va='center')

    # Adjust margins to prevent text from going outside the figure boundary
    plt.subplots_adjust(left=0.2, right=15)

    # Set the x-axis ticks to display values in a readable format on a logarithmic scale
    plt.gca().xaxis.set_major_formatter(ticker.ScalarFormatter())
    plt.gca().xaxis.set_major_locator(ticker.LogLocator(base=10, numticks=15))  # Adjust the number of ticks as needed

    # Set x-axis limits to start from a lower value
    plt.xlim(1, max(node_total_degrees)*1.5)  # Adjust multiplier as needed

    # Create 'plots' directory if it doesn't exist
    os.makedirs({PLOTS_FOLDER}, exist_ok=True)

    plt.tight_layout()  # Adjust layout for better appearance
    plt.savefig(f'{PLOTS_FOLDER}{filename}', dpi=dpi, bbox_inches='tight')

    plt.show()

def countLabelsData(graph):
    node_labels_data = {}

    for node in graph.nodes(data=True):
        label = node[1]['label']
        if label in node_labels_data:
            node_labels_data[label] += 1
        else:
            node_labels_data[label] = 1
    print(node_labels_data)

def plot_bar_chart(data, title, x_label, y_label, color, label_rotation=False):
    labels, values = zip(*sorted(data.items(), key=lambda x: x[1], reverse=True))
    bars = plt.bar(labels, values, color=color)

    for label, v in zip(labels, values):
        plt.text(label, v, str(v), ha='center', va='bottom', rotation=0, color='black')

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=45 if label_rotation else 0, ha='right')
    plt.tight_layout()

def statistics_graph(stat_dict, graph, filename='centrality_gaussian_plots_with_zscores.png',alpha=0.01):
    """
    Analyze and visualize network centrality measures.

    Parameters:
    - stat_dict (dict): Dictionary containing centrality measures.
    - graph (networkx.Graph): NetworkX graph object.
    - alpha (float): Significance level for hypothesis testing.

    Returns:
    None
    """
    z_scores = dict()
    centrality_values = dict()
    std_dev = dict()
    average_centrality = dict()

    print('ACTOR-ACTOR CONNECTED GRAPH')
    print('-----------------------------------------')

    # Display commonly used network measures
    num_nodes = len(graph.nodes())
    num_edges = len(graph.edges())

    print(f"Number of nodes: {num_nodes}")
    print(f"Number of edges: {num_edges}")
    print(f"Network density: {nx.density(graph)}")
    print(f"Global clustering coefficient: {nx.transitivity(graph)}")
    print('-----------------------------------------')

    for title, centrality_ in stat_dict.items():
        print('-----------------------------------------')
        for centrality, centrality_val in stat_dict.items():
            if centrality != title:
                r = pearsonr(
                    np.array([centrality_[node] for node in graph.nodes()]),
                    np.array([centrality_val[node] for node in graph.nodes()])
                )
                print(f'Pearson\'s r for {title} vs {centrality} -> {r[0]}')
                if r[1] < alpha:
                    rejection = False
                    significance = True
                else:
                    rejection = True
                    significance = False
                print(f"Null hypothesis: {rejection}")
                print(f"Significant difference: {significance}")
        print('-----------------------------------------')

    for title, centrality in stat_dict.items():
        print('')
        print(title)
        print('-----------------------------------------')
        std_dev_degree = np.std(list(centrality.values()))
        print("Standard deviation: " + str(std_dev_degree))
        highest_value = max(centrality, key=centrality.get)
        print(highest_value)
        print(
            f"Highest {title.lower()} node is {graph.nodes[highest_value]['properties']['name']} -> {centrality[highest_value]}")
        average = sum(centrality.values()) / len(centrality)
        print(f"The average {title.lower()} is {average}")
        print('')
        z_score = (centrality[highest_value] - average) / std_dev_degree
        critical_value = norm.ppf(1 - alpha / 2)
        if abs(z_score) > critical_value:
            rejection = False
            significance = True
        else:
            rejection = True
            significance = False

        print(f"Z_score: {z_score}")
        print(f"Null hypothesis: {rejection}")
        print(f"Significant difference: {significance}")
        tit = title.split(' ')[0]
        z_scores[tit] = z_score
        centrality_values[tit] = centrality.values()
        std_dev[tit] = std_dev_degree
        average_centrality[tit] = average

        centrality_colors = {
            "Degree": 'blue',
            "Closeness": 'green',
            "Betweenness": 'purple',
            "Eigenvector": 'orange'
        }

    # Create subplots in a 2x2 grid
    fig, axs = plt.subplots(2, 2, figsize=(15, 8))
    fig.suptitle('Centralities Distribution with Z-Scores', fontsize=16)
    i_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd'}
    # Iterate through each centrality measure
    for i, centrality_measure in enumerate(centrality_values):
        # Extract the highest centrality value for the current measure
        highest_value = max(centrality_values[centrality_measure])

        # Calculate the range of x values for the Gaussian (normal) distribution
        x_min = min(centrality_values[centrality_measure]) - 2 * std_dev[centrality_measure]
        x_max = max(centrality_values[centrality_measure]) + 2 * std_dev[centrality_measure]
        x = np.linspace(x_min, x_max, 300)
        # Create the Gaussian plot for the current centrality measure
        pdf = norm.pdf(x, average_centrality[centrality_measure], std_dev[centrality_measure])
        row, col = i // 2, i % 2  # Calculate row and column for subplot
        label = f'{i_map[i]}) {centrality_measure.lower()} centrality'
        axs[row, col].plot(x, pdf, label=label, color=centrality_colors[centrality_measure])

        # Highlight the highest centrality value in red
        axs[row, col].axvline(x=highest_value, linestyle='--', color='red',
                              label=f'Highest {centrality_measure} Centrality')

        # Add z-score as text
        axs[row, col].text(x_max, 0.8 * max(pdf), f'Z-Score: {z_scores[centrality_measure]:.2f}', color='black',
                           ha='right', va='center')

        axs[row, col].set_xlabel('Centrality Values')
        axs[row, col].set_ylabel('Probability Density')
        axs[row, col].set_title(f'{i_map[i]}) {centrality_measure.lower()} centrality')

    # Add legend to the first subplot (top-left)
    axs[0, 0].legend()

    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)

    # Save or display the plots
    plt.savefig(f'{PLOTS_FOLDER}{filename}',dpi=300)  # Adjust dpi as needed

    plt.show()

def print_top_nodes(centrality_dict, centrality_name, graph, num_top_nodes=50, file=None, basepath=None):
    """
    Print the top nodes based on centrality values.

    Parameters:
    - centrality_dict: Dictionary of centrality values
    - centrality_name: Name of the centrality metric
    - graph: NetworkX graph
    - num_top_nodes: Number of top nodes to print
    - file: File to save the LaTeX table
    """
    sorted_nodes = sorted(centrality_dict, key=centrality_dict.get, reverse=True)

    excl = ['Ancient Marbles', 'vhpt', 'Ltd']
    for node in sorted_nodes:
        if graph.nodes[node]:
            node_label = graph.nodes[node]['properties']['name']
            for i in excl:
                if normalize_name(node_label) == normalize_name(i):
                    print(node)
                    sorted_nodes.remove(node)

    top_nodes = sorted_nodes[:num_top_nodes]

    print(f"Top {num_top_nodes} nodes based on {centrality_name} centrality:")
    print("{:<10} {:<10} {:<20}".format("Node", "Score", "Label"))
    print("=" * 60)
    dictionary = {}
    for _, node in enumerate(top_nodes):
        centrality_value = f"{centrality_dict[node]:.3f}"  # Corrected line

        truncated_node = f'{node[:5]}...'
        node_label = graph.nodes[node]['properties']['name']
        print("{:<10} {:<10} {:<20}".format(truncated_node, centrality_value, node_label))
        dictionary[_] = {'Score': centrality_value, 'Node': node, 'Label': node_label}
    if file:
        file = basepath + file
        header = "\\begin{tabular}{rrl}"
        header += "\n"
        header += "\\toprule"
        header += "\n"
        header += "\\textbf{Node ID} & \\textbf{Score} & \\textbf{Name}\\\\"
        header += "\n"
        header += "\\midrule"
        for node in top_nodes:
            centrality_value = f"{centrality_dict[node]:.3f}"
            node_label = unidecode(graph.nodes[node]['properties']['name']).replace('&', '').title()
            header += '\n'
            header += f"{node[:5]}...& {centrality_value} & {node_label[:30]}"
            if len(node_label) > 30:
                header += '...'
            else:
                header += '\\hfill'
            header += "\\\\"
        header += "\n"
        header += '\\bottomrule'
        header += "\n"
        header += '\\end{tabular}'

        with open(file, 'w') as f:
            f.write(header)
        print(f"TeX file saved at {file}")

    return dictionary

def maxWeight(graph):
    edges_with_highest_weights = []
    max_weight = float('-inf')
    for u, v, d in graph.edges(data=True):
        weight = d.get('weight', 0)  # Default to 0 if 'weight' attribute is not present
        if weight > max_weight:
            edges_with_highest_weights = [(u, v)]
            max_weight = weight
        elif weight == max_weight:
            edges_with_highest_weights.append((u, v))

    return max_weight
# Function to read centrality data from a dictionary
def read_centrality_data(data_dict):
    df = pd.DataFrame.from_dict(data_dict, orient='index')
    return df
# Function to find common nodes in all centrality measures
def find_common_nodes(*dfs):
    common_nodes = set(dfs[0]['Label'])
    for df in dfs[1:]:
        common_nodes &= set(df['Label'])
    return common_nodes







