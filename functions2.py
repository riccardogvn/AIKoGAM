import os
import re
import spacy
from datetime import datetime
import json
import requests
import logging
import time
import random
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from tqdm.notebook import tqdm
from datetime import datetime
import urllib
from typing import Dict, Any
from html import unescape

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")
now = datetime.now()
date_and_hour = datetime.now().strftime("%d%m%Y_%H%M")
now = datetime.now()
date_and_hour = datetime.now().strftime("%d%m%Y_%H%M")
directory = rf'/logs/run' 
os.makedirs(directory, exist_ok=True)
filename = f'{directory}.json'
# Set up logging
log_file = f'{directory}_{datetime.now().strftime("%d%m%Y_%H%M")}_log.txt'
logging.basicConfig(filename=f'{directory}_{datetime.now().strftime("%d%m%Y_%H%M_%S")}_log.txt', level=logging.ERROR)

def format_date(input_date):
    try:
        date_obj = datetime.strptime(input_date, '%Y-%m-%dT%H:%M%z')
        formatted_date = date_obj.strftime('%d %B %Y')
        return formatted_date
    except ValueError:
        return "Invalid date format."

def dict_hash(dictionary: Dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()

def save_image(url, directory):
    """Download and save an image from the given URL to the specified directory."""
    try:
        response = requests.get(url, timeout=10)
        if 'christie' in url:
            id_name = url.rsplit('?')[0].lower().rsplit('lotimages/')[-1].replace('/', '_')
        elif 'sotheby' in url:
            id_name = url.split('/')[-2] + '_' + url.split('/')[-1]
        elif 'phoenixancientart' in url:
            id_name = id_name = url.rsplit('uploads/')[1].replace('/', '_')
        file_path = os.path.join(directory, id_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(file_path, 'wb+') as local_file:
            local_file.write(response.content)
        return file_path
    except Exception as e:
        logging.error(f"Exception occurred while saving image: {str(e)}")
        return None

def get_random_headers():
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random
    }
    return headers

def split_text(text):
    """Split the given text into sentences and phrases."""
    # Split the text using regex patterns
    sentences = re.split(r'(<br>|\r\n|\r|\n|<p>|</p>|<br>|<[^>]+>)', text)

    # Remove any leading or trailing whitespaces from each sentence
    sentences = [sentence.strip() if sentence else '' for sentence in sentences]

    # Remove empty sentences
    sentences = [sentence for sentence in sentences if sentence]

    # Split sentences into phrases using semicolons as stop phrases
    phrases = []
    for sentence in sentences:
        phrases.extend([phrase.strip() for phrase in re.split(r';', sentence) if phrase.strip()])

    return phrases


def process_sentences(sentences):
    """Process the given sentences using spaCy for sentence segmentation."""
    processed = []
    for sentence in sentences:
        # Use spaCy for sentence segmentation
        doc = nlp(sentence)
        for sent in doc.sents:
            processed.append(sent.text)

    return processed

    
def scrape_objects(obj):
    """Scrape object data."""
    # Your existing code for scraping object data here...
    return new_objs


def process_lot(lot, storeImage):
    """Process a lot by scraping data and extracting objects."""
    loturl = lot['url']
    try:
        response = requests.get(loturl, headers=get_random_headers()).text
        soup = BeautifulSoup(response, 'html.parser')
        objects = {}
        # Define the section names to search for
        keywords = ['Details', 'Provenance', 'Exhibited', 'Literature', 'Lot Essay', 'Special Notice', 'Sale Notice']
        # Find all elements that contain the section names (ignoring case) excluding script elements
        elements = soup.find_all(text=lambda t: any(keyword.lower() in t.lower() for keyword in keywords) and t.parent.name != 'script')
        for element in elements:
            if len(element) > 13:
                elements.remove(element)
        for element in elements:
            content = element.parent.find_next()
            if content:
                sentence_dict = {}
                text = content.get_text()
                section_name = element.strip().lower().replace(' ', '_')
                sentences = split_text(text)
                try:
                    processed_sentences = process_sentences(sentences)
                except Exception as e:
                    processed_sentences = sentences
                    logging.error(f"Exception occurred while processing sentence with NLP: {str(e)}")
                for index, prosentence in enumerate(processed_sentences):
                    sentence_dict[f'{section_name}_{index}'] = prosentence
                objects[section_name] = sentence_dict
            else:
                section_name = element.strip().lower().replace(' ', '_')
                objects[section_name] = None
        lot['objects'] = objects
        img_link = lot['image']['image_src']
        if storeImage:
            try:
                localPath = save_image(img_link, rf"\\images_\chri_{str(date_and_hour)}")
            except Exception as e:
                localPath = None
                logging.error(f"Exception occurred while saving image for lot {lot['object_id']}: {str(e)}")
            lot['image']['local_path'] = localPath
        else:
            lot['image']['local_path'] = None
    except Exception as e:
        logging.error(f"Exception occurred while scraping lot {lot['object_id']}: {str(e)}")


def scrape_lots(event, storeImage):
    event_data = event.copy()
    lots_data = []
    if 'lots' in event:
        for obj in tqdm(event['lots'], desc='Processing Lots'):
            if 'objects' in obj:
                pass
            else:
                new_objs = scrape_objects(obj)
                obj['objects'] = new_objs[0]
                obj['image']['local_path'] = new_objs[1]
            lots_data.append(obj)
    else:
        url_lots = f'https://www.christies.com/api/discoverywebsite/auctionpages/lotsearch?language=en&SaleId={event["event_id"]}'
        try:
            resplot = requests.get(url_lots, headers=get_random_headers())
            if resplot.status_code == 200:
                event_data['lots'] = resplot.json()['lots']
                for lot in tqdm(event_data['lots'], desc='Processing Lot'):
                    process_lot(lot, storeImage)
                    lots_data.append(lot)
            else:
                logging.error(
                    f"Error occurred while fetching lot data from {url_lots}. Status code: {resplot.status_code}")
        except Exception as e:
            logging.error(f"Exception occurred while fetching lot data from {url_lots}: {str(e)}")

    return event_data, lots_data


def collect_sales(start_year, end_year, log_file, storeImage=False):
    
    antiquities = []
    errors = []

    if start_year < 1998:
        start_year = 1998

    for year in tqdm(range(start_year, end_year), desc='Processing Years'):
        for month in tqdm(range(1, 13), desc=f'Year {year}'):
            url = f'https://www.christies.com/api/discoverywebsite/auctioncalendar/auctionresults?language=en&month={month}&year={year}'
            try:
                resp = requests.get(url, headers=get_random_headers())

                if resp.status_code == 200:
                    print(f'{resp.status_code} Getting data from {url}')
                    jsy = json.loads(resp.text)
                    jsyev = jsy['events']
                    for event in tqdm(jsyev, desc='Processing Events'):
                        if 'category_10' in event['filter_ids'] or 'antiquities' in event['title_txt'].lower():
                            event_data, lots_data = scrape_lots(event, storeImage)
                            event_data['saleLots'] = lots_data
                            event_data['auction'] = "Christie's"
                            event_data['reference'] = f"{event_data['auction']} {format_date(event_data['start_date'])}"
    
                            antiquities.append(event_data)
                            with open('christies_raw.json', 'w') as file:
                                json.dump(antiquities, file)
                    print(f'Finished getting data from {url}, now moving to {str(month + 1)}')
                    print(event['title_txt'])
                else:
                    errors.append(url)

                time.sleep(random.uniform(1, 5))

            except Exception as e:
                errors.append(url)
                logging.error(f"Exception occurred while fetching data from {url}: {str(e)}")
                time.sleep(random.uniform(1, 5))

    with open('christies_raw.json', 'w') as file:
        json.dump(antiquities, file)

    print(f"Data scraped successfully. Log file: {log_file}")

    return antiquities

def format_date(input_date: str) -> str:
    """Convert date from 'YYYY-MM-DDTHH:MMZ' to 'DD Month YYYY' format."""
    try:
        try:
            date_obj = datetime.strptime(input_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            date_obj = datetime.strptime(input_date, '%Y-%m-%dT%H:%M:%S')
        formatted_date = date_obj.strftime('%d %B %Y')
        return formatted_date
    except ValueError:
        return "Invalid date format."

def collect_sales_sothebys(auctionIds, storeImage=False):
    sothebys = []
    not_working = []
    url = "https://clientapi.prod.sothelabs.com/graphql"
    head = {'content-type': 'application/json'}
    data = dict()
    
    for auction in tqdm(auctionIds):  # Wrap the outer loop with tqdm
        query = '''query
        Auction($auctionId: String!) {
            auction(id: $auctionId) {
            auctionId
        dates
        {
            published
        closed
        }
        title
        locationV2
        {
            displayLocation
        {
            name
        }
        }
        saleResult
        {
            totalFinalPrice
        }
        sapSaleNumber
        slug
        {
            name
        year
        }
        lotCards(filter: ALL) {
            lotId
        }
        }
        }
                    '''
    
        variables = {'auctionId': auction}
        data['query'] = query
        data['variables'] = variables
    
        try:
            r = requests.post(url, data=json.dumps(data), headers=head, timeout=3)
            feed = r.content
            feed = feed.decode('utf8')
            feed = json.loads(feed)['data']
            sothebys.append(feed)
        except:
            print('error')
            pass

    for auction in sothebys:
        auction['auction']['saleLots'] = []

        for lot in tqdm(auction['auction']['lotCards']):  # Wrap the inner loop with tqdm
            lotId = lot['lotId']
            data = dict()
            query = '''query LotV2($lotId: String!){ lotV2(lotId: $lotId) { 
                        ... on LotV2 {
                          departmentNames
                          lotId
                          lotNumber {
                            ... on VisibleLotNumber {
                              lotNumber
                            }
                          }
                          slug
                          title
                          subtitle
                          designationLine
                          objects {
                            creationDate {
                              from
                              to
                            }
                            dimensionMetadata {
                              description
                              id
                              key
                              unit
                              value
                            }
                            exhibition
                            literature
                            provenance
                            metadata {
                              description
                              id
                              key
                              value {
                                ... on ObjectMetadataStringValue {
                                  stringValue
                                }
                                ... on ObjectMetadataStringValues {
                                  stringValues
                                }
                                ... on ObjectMetadataBooleanValue {
                                  boolValue
                                }
                                ... on ObjectMetadataIntegerValue {
                                  integerValue
                                }
                                ... on ObjectMetadataFloatValue {
                                  floatValue
                                }
                              }
                            }
                            objectTypeName
                            objectId
                            id
                            creators {
                              creatorId
                              displayName
                              id
                              role
                            }
                          }
                          estimateV2 {
                            ... on LowHighEstimateV2 {
                              highEstimate {
                                amount
                                currency
                              }
                              lowEstimate {
                                amount
                                currency
                              }
                            }
                          }
                          withdrawnState {
                            state
                          }
                          isSaved
                          media {
                            images {
                              renditions {
                                url
                              }
                              title
                            }
                          }
                          lotTags
                          condition {
                            ... on ConditionPublished {
                              report
                            }
                          }
                          bidState {
                            sold {
                              ... on ResultVisible {
                                premiums {
                                  finalPriceV2 {
                                    amount
                                    currency
                                  }
                                }
                              }
                            }
                          }
                          provenance
                          catalogueNote
                          description
                          literature
                          id
                          auction {
                            auctionId
                          }
                        }
                      }}
                        '''
            variables = {'lotId': lot['lotId']}
            data['query'] = query
            data['variables'] = variables

            try:
                r = requests.post(url, data=json.dumps(data), headers=head, timeout=3)
                auction['auction']['saleLots'].append(json.loads(r.content))
                for lot in auction['auction']['saleLots']:
                    img_link = lot['data']['lotV2']['media']['images'][0]['renditions'][0]['url']
                if storeImage:
                    try:
                        localPath = save_image(img_link, rf"\\images_\sothe_{str(date_and_hour)}")
                    except Exception as e:
                        localPath = None
                        logging.error(f"Exception occurred while saving image for lot {lot['object_id']}: {str(e)}")
                    lot['data']['lotV2']['media']['images'][0]['renditions'][0]['localPath'] = localPath
                else:
                    lot['data']['lotV2']['media']['images'][0]['renditions'][0]['localPath'] = None
                
                

            except:
                print('error in lot ' + lot['lotId'] + ':' + str(r.status_code))
                not_working.append(lot['lotId'])
                auction['auction']['saleLots'].append(lot['lotId'])

        auction['auction'].pop('lotCards')

    sothe = [auction['auction'] for auction in sothebys]
    sothe2 = []
    for x in tqdm(sothe, desc='Commencing Sotheby\'s: '):
        x2 = {}
        x2['saleTitle']=x['title']
        x2['saleId'] = x['auctionId']
        slug = x['slug']
        saleUrl = f'www.sothebys.com/en/buy/auction/{slug["year"]}/{slug["name"]}'
        x2['saleUrl'] = saleUrl
        x2['saleSubtitle'] = x['sapSaleNumber']
        saleStart = x['dates']['published']
        saleEnd = x['dates']['closed']
        x2['saleStart'] = saleStart
        x2['saleEnd'] = saleEnd
        saleLocation = x['locationV2']['displayLocation']['name']
        x2['saleLocation'] = saleLocation    
        x2['saleRef'] = f"Sotheby's {saleLocation} {format_date(saleStart)}"
        x2['auction'] = "Sotheby's"
        x2['saleLots'] = x['saleLots']
        sothe2.append(x2)
        
        with open('sothebys_raw.json', 'w') as file:
            json.dump(sothe2, file)
    with open('sothebys_raw.json', 'w') as file:
            json.dump(sothe2, file)

    return sothe2

def saveImagePAA(url, directory):
    id_name = url.rsplit('uploads/')[1].replace('/', '_')
    filePath = os.path.join(directory, id_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        response = requests.get(url, headers = {'User-Agent': UserAgent().random.strip()})

        with open(filePath, 'wb') as file:
            file.write(response.content)
        print('img_download_at ' + filePath )
    except:
        print('didnot work with ' + url)
        filePath = None
    return filePath


def collectPAA(storeImage=False):
    # Create a list to store the data
    data = []
    # Get the list of works of art
    url = "https://phoenixancientart.com/works-of-art/"
    response = requests.get(url, headers=get_random_headers())
    soup = BeautifulSoup(response.content, "html.parser")
    # Find all the work of art cards
    cards = soup.find('div', {'id': 'woa-posts'})
    cards = cards.findAll('h3')
    woas = []
    for i in cards:
        woa = i.find('a')['href']
        woas.append(woa)

    woas_db = []

    debug = []

    for woa in tqdm(woas, desc='Processing Lots'):  # Wrap the loop with tqdm
        resp = requests.get(woa, headers=get_random_headers())
        if resp:
            soup = BeautifulSoup(resp.content, 'html.parser')
            data = {}
    
            # Extract the title
            title = soup.find('h1').text.strip()
            data['title'] = title
    
            # Extract the subtitle
            subtitle = soup.find('p', class_='subtitle').text.strip()
            data['subtitle'] = subtitle
    
            # Extract material, dimensions, reference, and price
            details_container = soup.find('section', class_='content-module woa-details')
            materials_container = details_container.find('div', class_='materials')
            material = materials_container.find_all('p')
            if len(material) >= 2:
                materials = material[1:]
                materials_data = {}
                for mat in materials:
                    materials_data[material[0].text.strip().lower() + str(materials.index(mat))] = mat.text.strip()
    
                data['material'] = materials_data
            dimensions_container = details_container.find('div', class_='dimensions')
            dimensions = dimensions_container.find_all('p')
            if len(dimensions) >= 2:
                dimensions = dimensions[1:]
            dimensions_data = {}
    
            for dimension in dimensions:
                dimension_text = dimension.text.split('(')[0].strip()
                if ':' in dimension_text:
                    key, value = dimension_text.split(':',1)
                    value = value.split('(')[0].strip()  # Exclude contents inside parentheses
                    dimensions_data[key.strip()] = value.strip()
            data['dimensions'] = dimensions_data
            reference_container = details_container.find('div', class_='reference')
            reference = reference_container.find_all('p')
            if len(reference) >= 2:
                data['reference'] = reference[1].text.strip()
            price_container = details_container.find('div', class_='price')
            price = price_container.find_all('p')
            if len(price) >= 2:
                price_value = price[1].text.strip()
                if price_value.lower() == 'POR'.lower() or price_value.lower() == 'SOLD'.lower():
                    data['price'] = {'price': price_value}
                elif '$' in price_value:
                    currency = 'USD'
                    value = price_value.split('$')[1].replace(",","")
                    data['price'] = {'price': value, 'currency': currency}
                else:
                    currency = price_value.split()[0]
                    value = price_value.split()[1].replace("'", "")
                    data['price'] = {'price': value, 'currency': currency}
    
    
    
    
            # Extract overview
            overview = soup.find('section', class_='content-module woa-accordion').find('div', class_='accordion-item')
            overview_content = overview.find('div', class_='accordion-content').find_all('p')
            overview_data = {}
            for i, content in enumerate(overview_content):
                key = f'overview_{i}'
                value = content.text.strip()
                overview_data[key] = value
            data['overview'] = overview_data
            keywords = ['Provenance', 'Overview', 'Bibliography', 'Condition', 'Published', 'Exhibited']
            accordion_items = soup.find('section', class_='content-module woa-accordion').find_all('div', class_='accordion-item')
            for item in accordion_items:
                section_title = item.find('h2').get_text(strip=True)
                if section_title in keywords:
                    section_container = item.find('div', class_='accordion-content')
                    if '<br/>' in str(section_container):
                        section_container = BeautifulSoup(str(section_container).replace('<br/>','</p><p>'))
                    sections = section_container.find_all('p')
    
                    section_data = {}
                    for section in sections:
                        if len(section.text.strip()) > 2:
                            section_data[section_title.lower() + '_' + str(sections.index(section))] = section.text.strip()
    
                    data[section_title.lower()] = section_data
                    keywords.remove(section_title)
            for unused_key in keywords:
                data[unused_key.lower()] = None
    
            # Extract image link
            image_meta = soup.find('meta', property='og:image')
            image_link = image_meta['content']
            data['image'] = image_link
            if storeImage:
                try:
                    data['local_image'] = saveImagePAA(image_link, rf"\\images_\paa_{str(date_and_hour)}")
                except:
                    pass
            else:
                data['local_image'] = None
    
            # Extract content URL
            content_url_meta = soup.find('meta', property='og:url')
            content_url = content_url_meta['content']
            data['url'] = content_url
    
            # Extract modified time
            try:
                modified_time_meta = soup.find('meta', property='article:modified_time')
                modified_time = modified_time_meta['content']
                data['page_modified'] = modified_time
            except:
                data['pafe_modified'] = None
    
            woas_db.append(data)
            with open('PAA.json', 'w') as file:
                json.dump(woas_db, file)
        else:
            debug.append(woa)
            pass
        '''except Exception:
           debug.append(woa)
    '''
        with open('paa_raw.json', 'w') as file:
            json.dump(woas_db, file)

    return woas_db

# Import necessary libraries
import logging
from datetime import datetime
from tqdm import tqdm  # tqdm provides a progress bar for loops

# Set up logging
logging.basicConfig(filename='error_log.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to map Sotheby's data to the final keys
def map_sothebys_data(data):
    final_data = []
    for item in tqdm(data, desc='Mapping Sotheby\'s data'):  # Adding tqdm progress bar
        try:
            final_item = {
                "saleTitle": item["saleTitle"],
                "saleId": item["saleId"],
                "saleUrl": item["saleUrl"],
                "saleSubtitle": item["saleSubtitle"],
                "saleStart": datetime.strptime(item["saleStart"], "%Y-%m-%dT%H:%M:%S.%fZ").isoformat(),
                "saleEnd": datetime.strptime(item["saleEnd"], "%Y-%m-%dT%H:%M:%S.%fZ").isoformat(),
                "saleLocation": item["saleLocation"],
                "saleRef": item["saleRef"],
                "auction": "Sotheby's",
                "saleLots": item["saleLots"]
            }
            saleLots = []
            for lot in item['saleLots']:
                if type(lot) == str:  # Fixed variable name 'x' to 'lot'
                    pass
                else:
                    lot = lot['data']['lotV2']
                    if len(lot['estimateV2']) == 0:
                        low = ""
                        high = ""
                        currency = ""
                    else:
                        low = lot['estimateV2']['lowEstimate']['amount']
                        high = lot['estimateV2']['highEstimate']['amount']
                        currency = lot['estimateV2']['lowEstimate']['amount']

                    final_x = {
                        'lotId': lot['lotId'],
                        'lotNumber': lot['lotNumber']['lotNumber'],
                        'lotUrl': item['saleUrl'] + lot["slug"],
                        'lotTitle': lot['title'],
                        'lotSubtitle': lot['subtitle'],
                        'lotOther': "",
                        'lotLastOwner': lot['designationLine'],
                        'lotDescription': lot['description'],
                        'lotImage': lot['media']['images'][0]['renditions'][0]['url'],
                        'lotImageLocalPath': lot['media']['images'][0]['renditions'][0]['localPath'],
                        'lotEstimateLow': low,
                        'lotEstimateHigh': high,
                        'lotCurrency': currency,
                        'lotWithdrawn': lot['withdrawnState']['state'],
                        'lotPrice': lot['bidState']['sold'],
                        'lotSale': final_item['saleRef'],
                        'lotReference': f'{final_item["saleRef"]} lot {lot["lotNumber"]["lotNumber"]}',
                        'lotProvenance': dict(),
                        'lotDetails': dict(),
                        'lotEssay': dict(),
                        'lotExhibited': dict(),
                    }

                    for object in ['provenance', 'catalogueNote', 'description', 'literature', 'exhibition']:
                        if object == 'exhibition':
                            if (lot['objects']):
                                element = lot['objects'][0]['exhibition']
                            else:
                                element = ""
                        else:
                            element = lot[object]
                        if element:
                            if len(element) > 5:
                                element = element.replace('<br>', '</p><p>').replace('<br />', '</p><p>')
                                elements = element.split('</p>')
                                elements_clean = []
                                for elem in elements:
                                    soup = BeautifulSoup(unescape(elem), 'lxml')
                                    if len(soup.text) == 0:
                                        pass
                                    else:
                                        elements_clean.append(soup.text)
                                elemdict = dict()
                                for el in elements_clean:
                                    elemdict[f'{object}_{elements_clean.index(el)}'] = el
                                if object == 'description':
                                    final_x['lotDetails'] = elemdict
                                elif object == 'catalogueNote':
                                    final_x['lotEssay'] = elemdict
                                elif object == 'exhibition':
                                    final_x['lotExhibited'] = elemdict
                                else:
                                    final_x[f'lot{object.capitalize()}'] = elemdict

                    final_x['lotProvenance'][f'provenance_{str(len(final_x["lotProvenance"]) + 1)}'] = lot['designationLine']
                    final_x['lotProvenance'][f'provenance_{str(len(final_x["lotProvenance"]) + 1)}'] = final_x['lotReference']
                    saleLots.append(final_x)
                final_item['saleLots'] = saleLots
            final_data.append(final_item)

        except Exception as e:
            logging.error(f"Error occurred in map_sothebys_data: {str(e)}")

    return final_data


# Function to remap Christie's data to the final keys
def remap_christies_data(data):
    final_data = []
    for item in tqdm(data, desc='Remapping Christie\'s data'):  # Adding tqdm progress bar
        try:
            final_item = {
                "saleTitle": item["title_txt"],
                "saleId": item["event_id"],
                "saleUrl": item["landing_url"],
                "saleSubtitle": item["subtitle_txt"],
                "saleStart": datetime.strptime(item["start_date"], "%Y-%m-%dT%H:%M:%S").isoformat(),
                "saleEnd": datetime.strptime(item["end_date"], "%Y-%m-%dT%H:%M:%S").isoformat(),
                "saleLocation": item["location_txt"],
                "saleRef": item["reference"],
                "auction": "Christie's",
            }
            saleLots = []
            for lot in item['saleLots']:
                try:
                    lotImageLocalPath = lot['image']['local_path']
                except KeyError:
                    logging.error(f"KeyError occurred in remap_christies_data: {str(lot)}")
                    lotImageLocalPath = None  # Provide a default value or handle the absence of 'image' key

                final_x = {
                    'lotId': lot['object_id'],
                    'lotNumber': lot['lot_id_txt'],
                    'lotUrl': lot['url'],
                    'lotTitle': lot['title_primary_txt'],
                    'lotSubtitle': lot['title_secondary_txt'],
                    'lotOther': lot['title_tertiary_txt'],
                    'lotLastOwner': lot['consigner_information'],
                    'lotDescription': lot['description_txt'],
                    'lotImage': lot['image']['image_src'],
                    'lotImageLocalPath': lotImageLocalPath,
                    'lotEstimateLow': lot['estimate_low'],
                    'lotEstimateHigh': lot['estimate_high'],
                    'lotWithdrawn': lot['lot_withdrawn'],
                    'lotPrice': lot['price_realised'],
                    'lotPriceCurrency': lot['price_realised_txt'].split(' ')[0],
                    'lotSale': final_item['saleRef'],
                    'lotReference': f'{final_item["saleRef"]} lot {lot["lot_id_txt"]}',
                }
                
                final_x['lotProvenance'] = dict()
                for object in ['details','lot_essay','provenance','literature','exhibited','special_notice','others']:
                    if object in lot['objects']:
                        if '_' in object:
                            no = object.split('_')[1]
                            final_x[f'lot{no.capitalize()}'] = lot['objects'][object]
                        else:
                            final_x[f'lot{object.capitalize()}'] = lot['objects'][object]
                    else:
                        final_x[f'lot{object.capitalize()}'] = dict()
                final_x['lotProvenance'][f'provenance_{str(len(lot["lotProvenance"])+1)}'] = lot['consigner_information']
                final_x['lotProvenance'][f'provenance_{str(len(lot["lotProvenance"])+1)}'] = final_x['lotReference']
                saleLots.append(lot)
            final_item['saleLots'] = saleLots
            final_data.append(final_item)

        except Exception as e:
            logging.error(f"Error occurred in remap_christies_data: {str(e)}")

    return final_data

from datetime import datetime

def remap_paa_lot(item):
    lot = {
        'lotId': item['reference'],
        'lotNumber': item['reference'],
        'lotUrl': item['url'],
        'lotTitle': item['title'],
        'lotSubtitle': item['subtitle'],
    }

    if len(item['price']) > 1:
        lot['lotPrice'] = item['price']['price']
        lot['lotCurrency'] = item['price']['currency']
    else:
        lot['lotPrice'] = item['price']
        lot['lotCurrency'] = dict()

    lot['lotImage'] = item['image']
    lot['lotImageLocalPath'] = item['local_image']
    lot['lotProvenance'] = item['provenance']
    lot['lotExhibited'] = item['exhibited']

    literature = []
    if 'published' in item:
        if item['published']:
            for k, v in item['published'].items():
                literature.append(v)
    if 'bibliography' in item:
        if item['bibliography']:
            for k, v in item['bibliography'].items():
                literature.append(v)

    litdict = {f'literature_{i}': lit for i, lit in enumerate(literature)}
    lot['lotLiterature'] = litdict
    lot['lotLastOwner'] = 'Phoenix Ancient Art'

    uber = f'{lot["lotLastOwner"]} {datetime.now().strftime("%Y")}'
    if 'page_modified' in item:
        date = datetime.strptime(item['page_modified'], '%Y-%m-%dT%H:%M:%S+00:00').strftime('%d %B %Y')
    else:
        date = datetime.now().strftime('%d %B %Y')

    ref = f'{lot["lotLastOwner"]} lot {item["reference"]} {date}'
    lot['saleRef'] = ref

    lot['lotProvenance'][f'provenance_{str(len(lot["lotProvenance"]) + 1)}'] = f'{lot["lotLastOwner"]} {date} - {datetime.now().strftime("%d %B %Y")}'
    lot['lotWithdrawn'] = {}
    lot['lotDescription'] = item['overview']
    lot['lotCondition'] = item['condition']
    lot['lotDetails'] = {}

    if 'material' in item:
        lot['lotDetails']['material'] = item['material']
    if 'dimensions' in item:
        lot['lotDetails']['dimensions'] = item['dimensions']

    return lot

def remap_paa_data(paa_data):
    final_data = []
    for item in tqdm(paa_data, desc='Remapping PAA data'):  # Adding tqdm progress bar
        try:
            saleLots = [remap_paa_lot(item)]
            paa_entity = {
                'gallery': 'Phoenix Ancient Art',                
                'saleLots': saleLots
            }
            final_data.append(paa_entity)
        except Exception as e:
            logging.error(f"Error occurred in remap_paa_data: {str(e)}")

    return final_data


