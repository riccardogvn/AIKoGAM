#batch_detector.py

import json
from multiprocessing import Pool
from src.utils.language_detection import detect_language_batch
from tqdm import tqdm
from memory_profiler import profile
import gc
import os
import re
from setup.config import batch_size,num_processes, DATASET_FOLDER, RAW_DATASET, BATCH_FOLDER, PATTERN



# Define a custom JSON encoder to handle custom data structures
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, tuple):
            # Serialize tuple as a list
            return list(obj)
        return super().default(obj)


# Function to convert dict_values to a list of dictionaries
def dict_values_to_list(dict_values):
    """
    Convert a sequence of dict_values (e.g., from a dictionary) into a list of dictionaries.

    Args:
        dict_values (dict_values): A sequence of dict_values.

    Returns:
        list: A list of dictionaries converted from the input dict_values.
    """
    return [dict(value) for value in dict_values]


@profile
def main():
    """
    The main function for processing a dataset, detecting languages, and creating batch files.

    This function reads a dataset, splits it into batches, and processes each batch using
    parallel processing. It then merges the processed batch files into a single dataset.

    Args:
        None

    Returns:
        None
    """
    # Load your dataset
    with open(RAW_DATASET, 'r', encoding='utf-8') as j:
        dataset = json.load(j)

    # Create a new dictionary to store the results
    new_dataset = {'lots': {}}

    # Define the number of processes (workers) to use
    global num_processes # Adjust this based on your CPU cores

    # Split the texts into batches for processing
    global batch_size  # You can adjust this based on your requirements

    batch_num = 0  # Initialize batch number
    
    # Initialize a multiprocessing Pool
    with Pool(processes=num_processes) as pool:
        lot_keys = list(dataset['lots'].keys())  # Get the keys of the 'lots' dictionary
        for i in tqdm(range(0, len(lot_keys), batch_size), desc="Processing Batches"):
            batch_num += 1  # Increment batch number
            batch_keys = lot_keys[i:i + batch_size]
            batch_entries = [dataset['lots'][key] for key in batch_keys]
            text_batch = [list(entry['lotProvenance'].values()) for entry in batch_entries]
            os.makedirs(BATCH_FOLDER, exist_ok=True)
            # Get a list of files in the batch folder
            batch_files = os.listdir(BATCH_FOLDER)
            # Initialize a list to store batch numbers
            batch_ns = []
            # Iterate over the batch files
            for batch_file in batch_files:
                # Check if the file is a JSON file and matches the pattern
                match = re.match(PATTERN, batch_file)
                if match:
                    # Extract the batch number from the regex match
                    batch_n = int(match.group(1))
                    batch_ns.append(batch_n)
            # Sort the batch numbers in ascending order
            batch_ns.sort()
            # If you want to store the latest batch number as a variable, you can do this:
            latest_batch_number = batch_ns[-1] if batch_ns else None

            if latest_batch_number is not None and batch_num < latest_batch_number:
                pass

            else:
                print(latest_batch_number)
                processed_results = pool.map(detect_language_batch, text_batch)

                # Create a new list to store the results for this batch
                batch_results = []

                for entry, (input_texts, detected_languages, spacy_models) in tqdm(
                        zip(batch_entries, processed_results), total=len(batch_entries)):

                    # Iterate over the provenance texts
                    for idx, provenance_text in enumerate(input_texts):
                        provenance_key = f'provenance_{idx + 1}'  # Create the provenance key

                        # Create a dictionary for the current provenance
                        provenance_dict = {
                            'text': provenance_text,  # Store the input text
                            'detected_language': detected_languages[idx],  # Store the detected language
                            'spacy_model': spacy_models[idx]  # Store the Spacy model
                        }

                        entry['lotProvenance'][provenance_key] = provenance_dict  # Update the entry

                    # Append the processed entry to the batch results
                    batch_results.append(entry)

                # Serialize the batch data using the custom encoder and save it to a separate JSON file

                batch_filename = f'{BATCH_FOLDER}batch_{batch_num}.json'
                with open(batch_filename, 'w', encoding='utf-8') as batch_file:
                    batch_data = {'lots': {key: entry for key, entry in zip(batch_keys, batch_results)}}
                    json.dump(batch_data, batch_file, cls=CustomEncoder, ensure_ascii=False, indent=4)

                # Delete variables to free up memory
                del text_batch, processed_results, batch_results
                gc.collect()  # Perform garbage collection to release memory

    # Merge all batch files into a single new dictionary
    for batch_num in range(1, batch_num + 1):
        batch_filename = f'{BATCH_FOLDER}batch_{batch_num}.json'
        with open(batch_filename, 'r', encoding='utf-8') as batch_file:
            batch_data = json.load(batch_file)
            new_dataset['lots'].update(batch_data['lots'])

    # Save the merged new dataset to a JSON file
    with open(f'{DATASET_FOLDER}lang_db.json', 'w', encoding='utf-8') as new_db_file:
        json.dump(new_dataset, new_db_file, cls=CustomEncoder, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
