"""
catawiki_scraper.py

Scrapes data from Catawiki's archaeology category and updates a JSON file.

Dependencies:
- os
- json
- requests
- BeautifulSoup (from bs4)
"""

import os
import json
import requests
from bs4 import BeautifulSoup as bs

BASE_URL = 'https://www.catawiki.com/en/c/569-archaeology?page='
DATA_FILE_PATH = 'datasets/catawiki.json'

def scrape_catawiki_data(base_url, data_file_path, timeout=20):
    """
    Scrape data from Catawiki's archaeology category and update a JSON file.

    This function performs the following tasks:
    1. Sends an HTTP request to a Catawiki webpage to scrape data.
    2. Parses the HTML content using BeautifulSoup.
    3. Extracts data related to archaeology items from the webpage.
    4. Checks if a JSON file already exists and loads it.
    5. Iterates through multiple pages to collect data.
    6. Updates the data and stores it in a JSON file.

    :param base_url: The base URL for Catawiki's archaeology category.
    :param data_file_path: The path to the JSON data file.
    :param timeout: The timeout value for HTTP requests.

    :return: A dictionary containing scraped data.
    """
    # Initialize data structures
    catawiki_data = {'dictobjects': {}, 'data_id': None, 'tot_pages': None}

    # Send an HTTP request to the Catawiki webpage and scrape its content
    soup = bs(requests.get(base_url, timeout=timeout).content, 'html.parser')

    # Extract relevant data from the webpage
    for script_tag in soup.findAll('script'):
        if 'totalNumberOfLots' in script_tag.text:
            data_layer = script_tag.text.replace('dataLayer = [',
                                                 '').replace(']', '').replace(';', '')
            datal = json.loads(data_layer)
            catawiki_data['tot_pages'] = int(datal['totalNumberOfLots'] / 24)
            catawiki_data['data_id'] = datal['category_L1_id']

    # Check if a JSON file exists and load it
    if os.path.isfile(data_file_path):
        with open(data_file_path, 'r', encoding='utf-8') as json_file:
            catawiki_data['dictobjects'] = json.load(json_file)

    # Iterate through multiple pages to collect data
    for page_number in range(catawiki_data['tot_pages']):
        soup = bs(requests.get(f'{base_url}{page_number + 1}',
                               timeout=timeout).content, 'html.parser')
        data = json.loads(soup.find('div', {'data-id': catawiki_data['data_id']})['data-props'])

        # Process and update the data
        for item in data['results']:
            if item['id'] not in catawiki_data['dictobjects']:
                soup = bs(requests.get(item['url'], timeout=timeout).content, 'html.parser')
                item_data = soup.find('div', {'class': "lot-details-page-wrapper"})['data-props']
                item['data'] = json.loads(item_data)
                catawiki_data['dictobjects'][item['id']] = item

    # Save the updated data to the file
    with open(data_file_path, 'w', encoding='utf-8') as file:
        json.dump(catawiki_data['dictobjects'], file)

    return catawiki_data['dictobjects']
