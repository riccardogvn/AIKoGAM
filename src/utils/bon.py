from src.utils.harvesting import parse_auction_data,api_req
from src.utils.utils import Pic
from setup.config import RATE_LIMIT_SECONDS, DEPGOOD, API_CONFIG,HEADERS,PARAMS
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize variables
pages = 1
previous_length = None
total_data = []

api_url = 'https://www.bonhams.com/auctions/results/'  # Replace with the actual endpoint
refPic = Pic('datasets/refined_data')
refined_data = refPic.load()
if refined_data is None:
    refined_data = []

for depa in tqdm(DEPGOOD, desc='finding auctions in matching departments'):
    PARAMS['departments'] = depa
    while True:
        # Update the page parameter
        PARAMS['page'] = str(pages)

        response = api_req(api_url, headers=HEADERS, params=PARAMS)
        if response is None:
            break
        json_data = parse_auction_data(response)

        if json_data is None:
            logging.error(f"data failed: {PARAMS}")
            break

        page_data = json_data['data']['props']['pageProps']['pagesOfAuctions']
        # Check if the length is the same as the previous request
        if previous_length is not None and len(page_data) == previous_length:
            break
        previous_length = len(page_data)
        pages += 1
        total_data.extend(page_data)
        time.sleep(RATE_LIMIT_SECONDS)

# Rest of your code (continue with refined_data, auctions_, not_working, and redirects)


for x in total_data:
    for y in x:
        if y in refined_data:
            pass
        else:
            refined_data.append(y)
    refPic.save(refined_data)