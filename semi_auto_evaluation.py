from setup.config import REPLACEMENTS,GRAPH_FOLDER
from src.utils.cleaning import normalize_name
import re
import pickle

replacements=REPLACEMENTS
def process_names(node, replacements):
    no = node
    for rep in replacements:
        no = re.sub(rep, '', no, flags=re.IGNORECASE)
        no = no.replace('-',' ')
        no = no.replace('\xa0',' ')
    return sorted(no.strip().split(' '), reverse=True)

actors = []
graph = 'sub.pickle'
sub = pickle.load(open(f'{GRAPH_FOLDER}{graph}', 'rb'))
for node in sub.nodes():
    if sub.nodes[node]['label'] == 'actor':
        name = sub.nodes[node]['properties']['name']
        actors.append(name)

namelist = sorted(actors, reverse=False)
namelist_len = len(namelist)
namedentities = {}
other = []
gpe = []
dates = []
deletes = []
removal = []
try:
    for k, v in namedentities.items():
        removal.append(k)
        removal.append(v)  # Corrected variable name here
except:
    pass

def cleanNamelist(namelist, *lists):
    for element in lists:
        for j in element:
            if j in namelist:
                namelist.remove(j)

    for i, name in enumerate(namelist):
        if '\xa0' in name:
            namelist[i] = name.replace('\xa0', ' ')
            print(namelist[i])

    return namelist, other, gpe, dates, deletes, removal

namelist, other, gpe, dates, deletes, removal = cleanNamelist(namelist, other, gpe, dates, deletes, removal)

while namelist:
    print(len(namelist))
    node = namelist.pop(0)
    node = re.sub(r'[\xa0\s]+', ' ', node)
    question = input(f'Going on with {node}?')

    if question == 'other':
        other.append(node)
        continue

    elif question == 'gpe':
        gpe.append(node)
        continue

    elif question == 'date':
        dates.append(node)
        continue

    elif question == 'delete':
        deletes.append(node)
        continue

    elif question == 'append':
        new_replacement = input('What to append? ')
        replacements.append(r'\b{}\b'.format(new_replacement))
        if node not in namelist:
            namelist.append(node)
        print('replacements = ', replacements)
        print(f'{namelist[-1]}')
        continue

    elif question == '2':
        namelist.append(node)

    elif question == '1':
        names = process_names(node, replacements)
        break_outer_loop = False
        nodestocheck_ = []


        for name in names:
            if name and not break_outer_loop:

                for node_ in namelist[:]:
                    node_ = re.sub(r'[\xa0\s]+', ' ', node_)
                    names_ = process_names(node_, replacements)
                    check = 0
                    similars_ = []
                    for name_ in sorted(names_, reverse=True):

                        if name_ and normalize_name(name_) == normalize_name(name):
                            check += 1

                            print(f'Matching names: {name}, {name_}')
                            if name_ not in nodestocheck_:
                                nodestocheck_.append(node_)
                        elif normalize_name(name_) and fuzz.ratio(normalize_name(name),normalize_name(name_)) > 72:
                            print(name,fuzz.ratio(normalize_name(name),normalize_name(name_)), name_)
                            similars_.append(node_)
                            check += 1
                        if len(similars_) == 0:
                            if len(normalize_name(name_)) > 5 and len(normalize_name(name)) > 5:
                                if normalize_name(name_) and 68 < fuzz.ratio(normalize_name(name),normalize_name(name_)) < 72:
                                    print(name,fuzz.ratio(normalize_name(name),normalize_name(name_)), name_)
                                    similars_.append(node_)
                                    check += 1







                    for similar in similars_:
                        if similar not in nodestocheck_:
                            nodestocheck_.append(similar)


        if len(nodestocheck_) == 0:
            if node not in namedentities:
                namedentities[node] = [node]
            else:
                enties = namedentities[node]
                enties.append(node)
                enties = list(set(enties))
                namedentities[node] = enties
            pass
        else:
            nodestocheck_copy = []
            for n in nodestocheck_:
                na_ = n.split(' ')
                na = node.split(' ')
                if na_[-1] and na[-1]:
                    if na_[-1] == na[-1][0]:
                        print(n)
                        nodestocheck_copy.append(na_[-1])
            for x in nodestocheck_:
                if x not in nodestocheck_copy:
                    nodestocheck_copy.append(x)

            print(node + '\n', nodestocheck_copy)

            question_ = input('Are there nodes to merge?')

            if question_ == '1':
                for node_ in nodestocheck_:
                    while True:
                        print(f'based on {name_.upper()}')
                        if node not in namedentities:
                            question = input(f'Is {node_.upper()} to be merged with {node.upper()}? (1/2/append): ')
                        else:
                            question = input(
                                f'Is {node_.upper()} to be merged with {node.upper()}:{namedentities[node]}? (1/2/append): ')

                        if question == '1':
                            if node not in namedentities:
                                namedentities[node] = [node_]
                            else:
                                enties = namedentities[node]
                                enties.append(node_)
                                enties.append(node)
                                enties = list(set(enties))
                                namedentities[node] = enties

                            if node_ in namelist:
                                namelist.remove(node_)
                            print('Now at:', len(namelist) / namelist_len * 100, ' still ', len(namelist), ' to go......')
                            break

                        elif question == '2':
                            break



                        elif question == 'append':
                            new_replacement = input('What to append? ')
                            replacements.append(r'\b{}\b'.format(new_replacement))
                            print('replacements = ', replacements)
                            break

                        else:
                            if question != '3':
                                print('Invalid input, redo 1, 2, append, or pass')
                            else:
                                print('Skipping to the next node.')
                                namelist.append(node)
                                break_outer_loop = True
                                break

                        if break_outer_loop:
                            break

                    if break_outer_loop:
                        continue

            elif question_ == '2':
                check = input('Send tail or remove?1/2')
                if check == '1':
                    namelist.append(node)
                    continue
                elif check == '2':
                    if node not in namedentities:
                        namedentities[node] = [node]
                    else:
                        enties = namedentities[node]
                        enties.append(node)
                        enties = list(set(enties))
                        namedentities[node] = enties
                    continue


            elif question_ == '3':
                namelist.append(node)

            elif question == 'other':
                other.append(node)
                break

            elif question == 'gpe':
                gpe.append(node)
                break

            elif question == 'date':
                dates.append(node)
                break

            elif question == 'delete':
                deletes.append(node)
                break

            elif question == 'append':
                new_replacement = input('What to append? ')
                replacements.append(r'\b{}\b'.format(new_replacement))
                print('replacements = ', replacements)
                break

            else:
                continue

    else:
        if node not in namedentities:
            namedentities[node] = [node]
        else:
            enties = namedentities[node]
            enties.append(node)
            enties = list(set(enties))
            namedentities[node] = enties
        continue

MERGINGS = {}
for k, v in namedentities.items():
    setm = [k]

    for item in v:
        setm.append(item)

    setm = set(setm)

    # Find the minimum length element in the set
    value = min(setm, key=len)
    value = re.sub(r'^"|"$', '',  value)

    # Update the dictionary with mappings
    for i in setm:
        i = re.sub(r'^"|"$', '', i)
        MERGINGS[i] = value