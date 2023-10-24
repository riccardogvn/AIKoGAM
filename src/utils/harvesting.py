#harvesting.py
from src.utils.utils import openJson, saveJson,split_text,Pic
from tqdm.notebook import tqdm
import time
import requests
from bs4 import BeautifulSoup
import spacy
import logging
import os
import json
from fake_useragent import UserAgent
from datetime import datetime
import random
from typing import Dict, Any
from setup.config import RATE_LIMIT_SECONDS, DEPGOOD, API_CONFIG,HEADERS,PARAMS
# Example query parameters


logging.basicConfig(filename='error_log.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')
nlp = spacy.load("en_core_web_md")

def process_sentences(sentences):
    """Process the given sentences using spaCy for sentence segmentation."""
    processed = []
    for sentence in sentences:
        # Use spaCy for sentence segmentation
        doc = nlp(sentence)
        for sent in doc.sents:
            processed.append(sent.text)

    return processed

def get_random_headers():
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random
    }
    return headers

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
                directory = os.path.join("images", f"christies_{str(date_and_hour)}")
                os.makedirs(directory, exist_ok=True)
                localPath = save_image(img_link, directory)
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

def format_date(input_date):
    try:
        date_obj = datetime.strptime(input_date, '%Y-%m-%dT%H:%M%z')
        formatted_date = date_obj.strftime('%d %B %Y')
        return formatted_date
    except:
        try:
            date_obj = datetime.strptime(input_date, '%Y-%m-%dT%H:%M:%S')
            formatted_date = date_obj.strftime('%d %B %Y')
            return formatted_date
        except ValueError:
            return "Invalid date format."

def collect_sales(start_year, end_year, log_file, storeImage=False):
    #years_complete = openJson('years_complete.json')
    try:
        event_done = openJson('ch_done.json')
    except:
        event_done = []
    try:
        antiquities = openJson('christies_raw.json')
    except:
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
                            if event in event_done:
                                pass
                            else:
                                print(f"Moving to {event['title_txt']}")
                                event_data, lots_data = scrape_lots(event, storeImage)
                                event_data['saleLots'] = lots_data
                                event_data['auction'] = "Christie's"
                                event_data['reference'] = f"{event_data['auction']} {format_date(event_data['start_date'])}"

                                antiquities.append(event_data)
                                event_done.append(event)
                                saveJson(event_done,'ch_done.json')
                                saveJson(antiquities,'christies_raw.json')



                                print(f"done with {event['title_txt']}")

                    print(f'Finished getting data from {url}, now moving to {str(month + 1)}')

                else:
                    errors.append(url)

                time.sleep(random.uniform(1, 5))

            except Exception as e:
                errors.append(url)
                logging.error(f"Exception occurred while fetching data from {url}: {str(e)}")
                time.sleep(random.uniform(1, 5))

    saveJson(event_done, 'ch_done.json')
    saveJson(antiquities, 'christies_raw.json')


    print(f"Data scraped successfully. Log file: {log_file}")

    return antiquities

def scrape_objects(obj):
    """Scrape object data."""
    # Your existing code for scraping object data here...
    return new_objs

def collect_sales_sothebys(auctionIds, storeImage=False):
    sothebys = []
    not_working = []

    # Load the file containing already processed auction IDs
    done_file = 'sothebys_done.json'
    try:
        auction_ids_done = openJson(done_file)
    except:
        auction_ids_done = []

    sothebys = openJson('sothebys_raw.json')



    url = "https://clientapi.prod.sothelabs.com/graphql"
    head = {'content-type': 'application/json'}
    data = dict()
    success_threshold = 0.8  # Set the threshold to 80%

    for auction in tqdm(auctionIds):
        # Check if the auction ID is in the list of already processed IDs
        if auction in auction_ids_done:
            pass
        else:

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
                auction_data = feed['auction']

                auction_data['saleLots'] = []
                all_lots_successful = True

                exception_count = 0  # Initialize the exception count
                total_lots = len(auction_data['lotCards'])
                successful_lots_count = 0  # Initialize the count of successful lots

                for lot in tqdm(auction_data['lotCards']):  # Wrap the inner loop with tqdm
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
                        lot_data = json.loads(r.content)
                        try:
                            img_link = lot_data['data']['lotV2']['media']['images'][0]['renditions'][0]['url']

                            if storeImage:
                                try:
                                    directory = os.path.join("images", f"sothebys_{str(date_and_hour)}")
                                    os.makedirs(directory, exist_ok=True)
                                    localPath = save_image(img_link, directory)
                                except Exception as e:
                                    localPath = None
                                    logging.error(f"Exception occurred while saving image for lot {lotId}: {str(e)}")

                                lot_data['data']['lotV2']['media']['images'][0]['renditions'][0]['localPath'] = localPath
                            else:
                                lot_data['data']['lotV2']['media']['images'][0]['renditions'][0]['localPath'] = None
                        except Exception as e:
                            print(f'Error in img_link of lot {lotId}: {str(e)}')

                        auction_data['saleLots'].append(lot_data)
                        successful_lots_count += 1  # Increment the count for successful lots

                    except Exception as e:
                        print(f'Error in lot {lotId}: {str(e)}')
                        not_working.append(lotId)
                        all_lots_successful = False

                # Calculate the success rate for this auction
                success_rate = successful_lots_count / total_lots

                if success_rate >= success_threshold:
                    # Store the auction data as before
                    auction_data.pop('lotCards')
                    x2 = {}
                    x2['saleTitle'] = auction_data['title']
                    x2['saleId'] = auction_data['auctionId']
                    slug = auction_data['slug']
                    saleUrl = f'www.sothebys.com/en/buy/auction/{slug["year"]}/{slug["name"]}'
                    x2['saleUrl'] = saleUrl
                    x2['saleSubtitle'] = auction_data['sapSaleNumber']
                    saleStart = auction_data['dates']['published']
                    saleEnd = auction_data['dates']['closed']
                    x2['saleStart'] = saleStart
                    x2['saleEnd'] = saleEnd
                    saleLocation = auction_data['locationV2']['displayLocation']['name']
                    x2['saleLocation'] = saleLocation
                    x2['saleRef'] = f"Sotheby's {saleLocation} {format_date(saleStart)}"
                    x2['auction'] = "Sotheby's"
                    x2['saleLots'] = auction_data['saleLots']
                    sothebys.append(x2)

                    # Mark the auction ID as done
                    auction_ids_done.append(auction)
                    saveJson(auction_ids_done,done_file)
                    saveJson(sothebys,'sothebys_raw.json')


            except Exception as e:
                print(f'Error in auction {auction}: {str(e)}')

    saveJson(sothebys,'sothebys_raw.json')

    return sothebys

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
    event_done = openJson('paa_done.json')
    woas_db = openJson('paa_raw.json')
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

    debug = []

    for woa in tqdm(woas, desc='Processing Lots'):  # Wrap the loop with tqdm
        if woa in event_done:
            pass
        else:
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
                        directory = os.path.join("images", f"paa_{str(date_and_hour)}")
                        os.makedirs(directory, exist_ok=True)

                        data['local_image'] = saveImagePAA(image_link, directory)
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
                event_done.append(woa)
                saveJson(event_done,'paa_done.json')
                saveJson(event_done,'paa_raw.json')
                with open('paa_raw.json', 'w') as file:
                    json.dump(woas_db, file)
            else:
                debug.append(woa)
                pass
            '''except Exception:
               debug.append(woa)
    '''


    return woas_db


def parse_auction_data(response):
    try:
        result = BeautifulSoup(response.content, 'html.parser')
        data = result.find('script', {'id': '__NEXT_DATA__'}).string
        json_like_string = f'{{"data": {data}}}'
        json_data = json.loads(json_like_string)
        return json_data
    except (AttributeError, KeyError, json.JSONDecodeError) as e:
        logging.error(f"Error parsing data: {e}")
        return None

def api_req(url, headers=HEADERS, params=PARAMS, allow_redirects=False):
    try:
        if allow_redirects:
            response = requests.get(url, headers=HEADERS, allow_redirects=True)
        else:
            response = requests.get(url, headers=HEADERS, params=PARAMS)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None



def collectBon(storeImage = False):
    logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    aucPic = Pic('datasets/auctions_')
    nwPic = Pic('datasets/not_working')
    nwlPic = Pic('datasets/not_working_lots')
    refPic = Pic('datasets/refined_data')

    auctions_ = aucPic.load()
    not_working = nwPic.load()
    not_working_lots = nwlPic.load()
    refined_data = refPic.load()

    if auctions_ is None:
        auctions_ = dict()
    if not_working is None:
        not_working = dict()
    if not_working_lots is None:
        not_working_lots = []




    for _,y in tqdm(enumerate(refined_data), desc=f'Scraping auction'):
        urlc = y['id']

        # API endpoint URL (replace with the actual endpoint from the documentation)
        base_url = 'https://www.bonhams.com/auction/'  # Replace with the actual endpoint
        api_url = f"{base_url}{urlc}"

        if api_url in auctions_:
            print('already there')

        elif api_url in not_working:
            print('already there in not working')

        else:
            # Function to make API requests
            response = api_req(api_url, headers=HEADERS, allow_redirects=True)
            if response is None:
                not_working[api_url] = urlc
                nwPic.save(not_working)
                continue

            json_data = parse_auction_data(response)
            if json_data is None:
                not_working[api_url] = urlc
                nwPic.save(not_working)
                logging.error(f"data failed: {api_url}")
                continue

            auc = json_data['data']
            auctions_[api_url] = auc
            auctionLots = auctions_[api_url]['props']['pageProps']['lotData']['auctionLots']
            auctions_[api_url]['depLots'] = []
            auctions_[api_url]['lots'] = {}

            for lot in auctionLots:
                if 'name' in lot['department']:
                    if lot['department']['name'] in DEPGOOD:
                        auctions_[api_url]['depLots'].append(lot['lotId'])
                else:
                    auctions_[api_url]['depLots'].append(lot['lotId'])


            for lot in tqdm(auctions_[api_url]['depLots'], desc=f'Scraping lots'):
                api_url_lot = f"{api_url}/lot/{lot}"

                response_lot = api_req(api_url_lot, headers=HEADERS, allow_redirects=True)

                if response_lot is None:
                    not_working_lots.append(api_url_lot)
                    nwlPic.save(not_working_lots)
                    continue

                json_data = parse_auction_data(response_lot)
                if json_data is None:
                    not_working_lots.append(api_url_lot)
                    nwlPic.save(not_working_lots)
                    continue

                auctions_[api_url]['lots'][lot] = json_data['data']['props']['pageProps']
                if storeImage:
                    try:
                        images = auctions_[api_url]['lots'][lot]['images']
                        if len(images) >= 1:
                            image = images[0]
                            directory = os.path.join("images", f"bon_{str(date_and_hour)}")
                            os.makedirs(directory, exist_ok=True)
                            auctions_[api_url]['lots'][lot]['local_image'] = saveImageBon(image, directory)
                    except:
                        auctions_[api_url]['lots'][lot]['local_image'] = None
                        pass
                else:
                    auctions_[api_url]['lots'][lot]['local_image'] = None


            aucPic.save(auctions_)

            time.sleep(RATE_LIMIT_SECONDS)

    with open('bon_raw.json','w') as f:
        json.dump(auctions_,f)

    return auctions_


def saveImageBon(image_data, directory):
    id_name = image_data['iImageNo']
    url = image_data['image_url']
    filePath = os.path.join(directory, id_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        response = requests.get(url, headers={'User-Agent': UserAgent().random.strip()})

        with open(filePath, 'wb') as file:
            file.write(response.content)
        print('img_download_at ' + filePath)
        return filePath
    except:
        print('didnot work with ' + url)
        return None









