# -*- coding: utf-8 -*-
# config.py

# Define configuration parameters

# Set the number of batch size for processing
batch_size = 50

# Set the number of processes (workers) to use for parallel processing
num_processes = 4

# Set the Neo4j database settings
neo4j = {
    "uri": "bolt://localhost:7687",  # URI for Neo4j database
    "username": "neo4j",  # Username for Neo4j authentication
    "password": "administrator",  # Password for Neo4j authentication
    "encrypted": False  # Set to True if the connection should be encrypted
}

# Spacy 3.6.0 models for various languages
SPACY_MODELS = {
    'ca': 'ca_core_news_sm',  # Catalan compatible with 3.6.0
    'da': 'da_core_news_sm',  # Danish compatible with 3.6.0
    'de': 'de_core_news_sm',  # German compatible with 3.6.0
    'el': 'el_core_news_sm',  # Greek compatible with 3.6.0
    'en': 'en_core_web_md',  # English compatible with 3.6.0
    'es': 'es_core_news_sm',  # Spanish compatible with 3.6.0
    'fi': 'fi_core_news_sm',  # Finnish compatible with 3.6.0
    'fr': 'fr_core_news_sm',  # French compatible with 3.6.0
    'hr': 'hr_core_news_sm',  # Croatian compatible with 3.6.0
    'it': 'it_core_news_sm',  # Italian compatible with 3.6.0
    'ja': 'ja_core_news_sm',  # Japanese compatible with 3.6.0
    'ko': 'ko_core_news_sm',  # Korean compatible with 3.6.0
    'lt': 'lt_core_news_sm',  # Lithuanian compatible with 3.6.0
    'mk': 'mk_core_news_sm',  # Macedonian compatible with 3.6.0
    'nb': 'nb_core_news_sm',  # Norwegian Bokmål compatible with 3.6.0
    'nl': 'nl_core_news_sm',  # Dutch compatible with 3.6.0
    'pl': 'pl_core_news_sm',  # Polish compatible with 3.6.0
    'pt': 'pt_core_news_sm',  # Portuguese compatible with 3.6.0
    'ro': 'ro_core_news_sm',  # Romanian compatible with 3.6.0
    'sl': 'sl_core_news_sm',  # Slovenian compatible with 3.6.0
    'sv': 'sv_core_news_sm',  # Swedish compatible with 3.6.0
    'ru': 'ru_core_news_sm',  # Russian compatible with 3.6.0
    'uk': 'uk_core_news_sm',  # Ukrainian compatible with 3.6.0
    'xx_ent_wiki': 'xx_ent_wiki_sm',  # Multi-language Entity Recognition  compatible with 3.6.0
    'xx_sent_ud': 'xx_sent_ud_sm',  # Multi-language Sentence Segmentation compatible with 3.6.0
    'zh': 'zh_core_web_sm',  # Chinese compatible with 3.6.0
}

# Language detection model URL
'''
ERCDiDip/langdetect: https://huggingface.co/ERCDiDip/langdetect

Detects languages in the input text and translates it to the target language using a machine translation model.
If the detected language is the same as the target language, no translation is performed.
If a custom translation model is not provided, a default translation model is used based on the detected language.

Detectable Languages:
Modern: Bulgarian (bg), Croatian (hr), Czech (cs), Danish (da), Dutch (nl), English (en),
Estonian (et), Finnish (fi), French (fr), German (de), Greek (el), Hungarian (hu), Irish (ga),
Italian (it), Latvian (lv), Lithuanian (lt), Maltese (mt), Polish (pl), Portuguese (pt),
Romanian (ro), Slovak (sk), Slovenian (sl), Spanish (es), Swedish (sv), Russian (ru),
Turkish (tr), Basque (eu), Catalan (ca), Albanian (sq), Serbian (se), Ukrainian (uk),
Norwegian (no), Arabic (ar), Chinese (zh), Hebrew (he)

Medieval: Middle High German (mhd), Latin (la), Middle Low German (gml), Old French (fro),
Old Church Slavonic (chu), Early New High German (fnhd), Ancient and Medieval Greek (grc)

'''
LANGUAGE_DETECTION_MODEL_URL = 'ERCDiDip/langdetect'

DATASET_FOLDER = 'datasets/'
RAW_DATASET = 'datasets/db.json'
BATCH_FOLDER = 'datasets/batches/'
PATTERN = r'batch_(\d+)\.json'


