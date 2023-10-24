"""
hixenbaugh_scraper.py

This module contains functions to scrape data from Hixenbaugh's gallery pages
and update a JSON file with information about various objects.

Dependencies:
- os
- json
- requests
- BeautifulSoup (from bs4)
- tqdm
"""
import os
import json
import re
import requests
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

DATA_FILE_PATH = 'datasets/hixenbaugh.json'
BASE_PATH = 'https://www.hixenbaugh.net/gallery/'
PAGE_URL = 'gallery.cfm?PageNum_pics='
TIMEOUT = 20
SECTIONS = ['height', 'length', 'dimension', 'dimensions', '$',
            ['published', 'cf.:', 'literature', 'bibliography'],
            ['provenance', 'acquired from', 'previously in', 'purchased in',
             'subsequently with', 'collection', 'owner', 'from above'],
            'exhibited', 'inv#']
CONTROL = ['published', 'cf.:', 'literature', 'bibliography', 'provenance',
           'acquired from', 'previously in', 'purchased in', 'subsequently with',
           'formerly', 'collection', 'owner', 'from above', 'exhibited']

def get_last_page(url, timeout):
    """
    Get the last page number from the given URL.

    Args:
        url (str): The URL to scrape.
        timeout (int): Request timeout in seconds.

    Returns:
        str: The last page number as a string.
    """
    page_response = requests.get(url, timeout=timeout)
    page_soup = bs(page_response.content, 'html.parser')
    totpages = page_soup.findAll('div', {'id': 'extra'})
    totpage = [page.text for page in totpages if 'Page' in str(page)][0].replace('\xa0',
                                                                                 ' ').split(' ')
    return max((item for item in totpage if item.isdigit()), default='0')

def load_existing_data(data_file_path):
    """
    Load existing data from a JSON file.

    Args:
        data_file_path (str): The path to the JSON data file.

    Returns:
        dict: The loaded data as a dictionary.
    """
    if os.path.isfile(data_file_path):
        with open(data_file_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    return {}

def clean_item_data(item_data):
    """
    Clean and format the item data.

    Args:
        item_data (dict): The item data to be cleaned.

    Returns:
        dict: The cleaned and formatted item data.

    This function performs the following operations on the item data:
    1. If 'Exhibited' and 'Provenance' have the same content, they are split into separate fields.
    2. It removes any leading colons (': ') in the values of the item data.
    3. It replaces consecutive periods ('..') with a single period ('.') in the values.
    4. It strips leading and trailing whitespace from the values.

    The cleaned item data is then returned.

    """
    if 'Exhibited' in item_data and 'Provenance' in item_data:
        if item_data['Exhibited'] == item_data['Provenance']:
            if 'Exhibited' in item_data['Provenance']:
                new_c = item_data['Provenance'].split('Exhibited')
                item_data['Provenance'] = new_c[0]
                item_data['Exhibited'] = new_c[1]

    pattern = r'^: '
    for k, v in item_data.items():
        v = re.sub(pattern, '', v)
        item_data[k] = v.replace('..', '.').strip()

    return item_data


def parse_item_data(item_url, timeout):
    """
        Parse data for an item from the given URL.

        Args:
            item_url (str): The URL of the item to parse.
            timeout (int): Request timeout in seconds.

        Returns:
            dict: Parsed data for the item.
    """
    item_response = requests.get(item_url, timeout=timeout)
    item_soup = bs(item_response.content, 'html.parser')
    item_content = item_soup.find('div', {'id': 'content'})

    img = f"www.hixenbaugh.net{item_content.find('img')['src']}"
    next_ = item_soup.find('h1')
    title = next_.string
    item_data = {'lotPage': item_url, 'Image': img, 'lotName': title}
    siblings = []

    while next_ is not None:
        next_ = next_.nextSibling

        if next_ is not None and next_.text is not None and len(next_.text) > 5:
            siblings.append(next_)

    paragraphs = []
    for sibling in siblings:
        if sibling is not None:
            list_of_siblings = str(sibling).split('</p>')
            for string_sibling in list_of_siblings:
                if len(string_sibling) > 1:
                    paragraphs.append(bs(string_sibling).text)

    nextsections = SECTIONS.copy()

    for idx, paragraph in enumerate(paragraphs):
        if idx == 0:
            item_data['Description'] = paragraph
        elif idx in [1, 2]:
            pas = None
            for i in CONTROL:
                if i in paragraph.lower():
                    pas = 1
            if pas is None:
                details = []
                various = {}
                elaborated_paragraph = paragraph

                for section in SECTIONS:
                    nextsections.remove(i)

                    if isinstance(section, str) and section in elaborated_paragraph.lower():
                        second_paragraph = elaborated_paragraph.lower().rsplit(section, 1)[1]
                        various[section.title()] = second_paragraph.strip().title()
                        elaborated_paragraph = elaborated_paragraph.replace(second_paragraph, '')

                        for nextsection in nextsections:
                            if isinstance(nextsection, str) and nextsection in second_paragraph.lower():
                                elaborated_paragraph = paragraph

                    nextsections = SECTIONS.copy()

                for k, v in various.items():
                    paragraph = paragraph.lower().replace(k.lower(), '').replace(v.lower(), '')
                    item_data[k] = v

                details.append(paragraph.title().strip())
            else:
                paragraphs.append(paragraph)
        else:
            for section in SECTIONS:
                if isinstance(section, str) and section in paragraph.lower():
                    item_data[section.title()] = paragraph.strip()
                    break
                if isinstance(section, list):
                    for subsection in section:
                        if subsection in paragraph.lower():
                            item_data[section[0].title()] = paragraph.strip()
                            break

    detail = ''

    for element in details:
        detail += element
        detail += '. '

    item_data['Details'] = detail
    item_data = clean_item_data(item_data)

    return item_data


if __name__ == "__main__":
    last_page = get_last_page(f'{BASE_PATH}{PAGE_URL}', TIMEOUT)
    existing_data = load_existing_data(DATA_FILE_PATH)

    for _ in tqdm(range(int(last_page)), desc=f"Collecting {last_page}"):
        response = requests.get(f'{BASE_PATH}{PAGE_URL}{_}', timeout=TIMEOUT)
        soup = bs(response.content, 'html.parser')
        content = soup.find('div', {'id': 'content'})

        for link in tqdm(content.findAll('a'), desc=f"Parsing {last_page} objects"):
            if 'PageNum' not in str(link):
                uri = f"{BASE_PATH}{link['href']}"
                if uri not in existing_data:
                    item = parse_item_data(uri, TIMEOUT)
                    existing_data[uri] = item

    # Save the updated data to the file
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file)
