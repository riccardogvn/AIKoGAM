# -*- coding: utf-8 -*-
from tqdm.notebook import tqdm
import logging
from bs4 import BeautifulSoup
import json
import re
from event_extraction import clean_provenance
from src.utils.utils import dict_hash
from datetime import datetime
from html import unescape
import logging
from src.utils.harvesting import format_date

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

def remap_bon(rawdata):
    final_data = []
    data = list(rawdata.values())
    del rawdata
    for item in tqdm(data, desc='Remapping Bonham\'s data'):
        try:
            auction_base = item['props']['pageProps']['auction']
            auctionId = item['query']['auctionId']
            auctionName = item["query"]['auctionName']
            page = f'{item["props"]["baseUrl"]}/auction/{auctionId}/{auctionName}'
            final_item = {
                "saleTitle": auctionName,
                "saleId": auctionId,
                "saleUrl": page,
                "saleSubtitle": auction_base['description'],
                "saleStart": datetime.strptime(auction_base["daStartDate"], "%Y-%m-%dT%H:%M:%S").isoformat(),
                "saleEnd": datetime.strptime(auction_base["daEndDate"], "%Y-%m-%dT%H:%M:%S").isoformat(),
                "saleLocation": auction_base["sVenue"],
            }
            saleRef = f"Bonham's {final_item['saleLocation']} {format_date(final_item['saleStart'])}"
            final_item['saleRef'] = saleRef

            saleLots = []

            for object in tqdm(list(item['lots'].values())):
                lot = object['lot']
                try:
                    lotImageLocalPath = lot['local_image']
                except KeyError:
                    #logging.error(f"KeyError occurred in remap_christies_data: {str(lot)}")
                    lotImageLocalPath = None  # Provide a default value or handle the absence of 'image' key
                final_x = {
                    'lotId': lot['iSaleLotNoUnique'],
                    'lotNumber': lot['iSaleLotNo'],
                    'lotUrl': f'{page}/lot/{lot["iSaleLotNo"]}',
                    'lotTitle': lot['lot_title'],
                    'lotSubtitle': '',
                    'lotOther': '',
                    'lotLastOwner': '',
                    'lotImage': lot['images'][0]['image_url'],
                    'lotImageLocalPath': lotImageLocalPath,
                    'lotEstimateLow': lot['dEstimateLow'],
                    'lotEstimateHigh': lot['dEstimateHigh'],
                    'lotWithdrawn': '',
                    'lotPrice': lot['dHammerPrice'],
                    'lotPriceCurrency': lot['sCurrencySymbol3'],
                    'lotSale': final_item['saleRef'],
                    'lotReference': f'{final_item["saleRef"]} lot {lot["iSaleLotNo"]}',
                }

                try:
                    final_x['lotDescription'] = {}
                    for k, v in lot.items():
                        if '<div ' in str(v):
                            subdesc = {}
                            pattern = r'<div\s+class=["\'](.*?)["\']>'
                            val = BeautifulSoup(v, 'html.parser')

                            matches = re.findall(pattern, str(val))
                            for match in matches:
                                # Replace 'Lot' in the class name and use it as the dictionary key
                                key = f'{match.strip()}'
                                # Find the <div> element with the specific class
                                soup = val.find('div', {'class': match})
                                if soup:
                                    # Extract text content, preserving line breaks
                                    result = '\n'.join(soup.stripped_strings)
                                    subdesc = result.strip().replace('\n','. ')
                                    final_x['lotDescription'][key] = subdesc
                except:
                    final_x['lotDescription'] = lot['sDesc']

                try:
                    extras = BeautifulSoup(lot['footnote_sExtraDesc'],'html.parser')
                    sections = [i.text for i in extras.findAll('b')]
                    for idx, section in enumerate(sections):
                        subsections = {}
                        soup = extras.find('b', text=section)
                        cn = 0
                        while soup is not None:
                            count = idx + 1
                            next_section = extras.find('b', text=sections[count]) if len(sections) > count else None

                            if next_section and soup == next_section:
                                pass
                            else:
                                subsection = soup.text.strip()
                                if subsection:
                                    if subsection != section.strip():
                                        if len(subsection) > 3:
                                            subsections[f'{section.lower()}_{cn}'] = subsection
                                            cn += 1

                            soup = soup.nextSibling

                        final_x[f'lot{section.strip()}'] = subsections
                except:
                    pass


                saleLots.append(final_x)
            final_item['saleLots'] = saleLots
            final_data.append(final_item)

        except Exception as e:
            logging.error(f"Error occurred in remap_christies_data: {str(e)}")
        gc.collect()

    return final_data




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
                    'lotProvenance': dict()
                }


                for object in ['details','lot_essay','provenance','literature','exhibited','special_notice','others']:
                    if object in lot['objects']:
                        if '_' in object:
                            no = object.split('_')[1]
                            final_x[f'lot{no.capitalize()}'] = lot['objects'][object]
                        else:
                            final_x[f'lot{object.capitalize()}'] = lot['objects'][object]
                    else:
                        final_x[f'lot{object.capitalize()}'] = dict()
                if 'lotProvenance' in final_x:
                  final_x['lotProvenance'][f'provenance_{str(len(final_x["lotProvenance"])+1)}'] = lot['consigner_information']
                  final_x['lotProvenance'][f'provenance_{str(len(final_x["lotProvenance"])+1)}'] = final_x['lotReference']
                else:
                  final_x['lotProvenance'] = {'provenance_0':lot['consigner_information'],'provenance_1': final_x['lotReference']}


                saleLots.append(final_x)
            final_item['saleLots'] = saleLots
            final_data.append(final_item)

        except Exception as e:
            logging.error(f"Error occurred in remap_christies_data: {str(e)}")

    return final_data

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

def cleanSubdictionaries(partial_output):


    # Define a regular expression pattern to match non-alphanumeric characters (excluding foreign language characters)
    non_alphanumeric_pattern = re.compile(r'^[^\w]+$')
    to_clean = ['lotProvenance', 'lotDetails', 'lotExhibited', 'lotEssay']

    # Iterate through the 'saleLots' list
    for object in partial_output:
        for item in object['saleLots']:
            for element in to_clean:
                lot_provenance = item.get(element, {})

                if lot_provenance is None:
                    continue  # Skip None values

                # Create a set to keep track of unique 'text' values within the same 'lotProvenance'
                unique_texts = set()

                # Create a list of keys to remove based on 'text' values
                keys_to_remove = []

                # Create a dictionary to store the renumbered 'lotProvenance' subdictionaries
                new_lot_provenance = {}

                count = 1  # Counter for renumbering subdictionaries

                for key, value in lot_provenance.items():
                    text = clean_provenance(str(value))  # Ensure value is a string
                    if not text or non_alphanumeric_pattern.match(
                            text) or text in unique_texts or text == 'None' or text == "":
                        keys_to_remove.append(key)
                    else:
                        # Renumber the subdictionary keys as 'provenance_1', 'provenance_2', ...
                        base_key = element.replace('lot', '').lower()
                        new_key = f'{base_key}_{count}'
                        new_lot_provenance[new_key] = clean_provenance(text)
                        count += 1
                        unique_texts.add(text)

                # Remove the subdictionaries with duplicate, empty, or non-alphanumeric 'text' values
                for key in keys_to_remove:
                    lot_provenance.pop(key, None)

                # Replace the 'lotProvenance' dictionary with the renumbered and cleaned version
                item[element] = new_lot_provenance

    return partial_output

def hashAndClean(final_output):
    lots = dict()
    events = dict()
    
    for fin in final_output:
        for j in fin['saleLots']:
            j['lotHash'] = dict_hash(j)
        fin['saleHash'] = dict_hash(fin)
        for j in fin['saleLots']:
            j['saleHash'] = fin['saleHash']
        for j in fin['saleLots']:
            lots[j['lotHash']] = j
        events[fin['saleHash']] = fin
    for k,v in events.items():
        v.pop('saleLots')
    
    for k,v in lots.items():
        for x,j in v.items():
            if j == None:
                v[x] = ""
                print(v[x])
            if type(j) == dict:
                for a,b in j.items():
                    if b == None:
                        j[a] = ""
                        print(j)
                        
    db = {'events':events,'lots':lots}
    
    return db


