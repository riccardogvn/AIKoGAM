# PROVENANCE-KG: A Knowledge Graph of Artworks and Provenance Events

This project allows the extraction of events from artwork provenance into a Knowledge Graph (KG). The KG connects artworks through the common events.

Author: \
Hebatallah Mohamed (hebatallah.mohamed@iit.it)


## Installation:

1. Install Neo4J and adjust the following configurations in the 'config.py' under the 'setup' folder.
```
neo4j = {
    "uri":"bolt://localhost:7687",
    "username": "neo4j",
    "password": "admin",
    "encrypted": False
}
```

2. Install the dependencies listed in the the 'requirements.txt'.
```
pip3 install -r requirements.txt
```

3. Install spaCy's Named Entity Recognition (NER) model.
```
python -m spacy download en_core_web_md
```

## Execution:

1. Run the following to extract the events from the provenance texts. This module will store the events in the 'events' folder.
```
python event_extraction.py
```

2. Run the following to construct the KG.
```
python kg_construction.py
```

## Output:

The KG will consist of nodes of type "Artwork" and "Event", as illustrated below. The following Cypher query helps showing a subset of a connected part of the KG:

```
MATCH (n:event)--()
WITH n,count(*) as rel_cnt
WHERE rel_cnt > 1
WITH n LIMIT 20
CALL apoc.path.subgraphNodes(n, {minLevel:0}) YIELD node
return node
```

"Artwork" entity example:

<img src="imgs/artwork.png" width="85%" height="85%">

"Event" entity example:

<img src="imgs/event.png" width="85%" height="85%">
