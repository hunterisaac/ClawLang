#results = {'ids': [['secret.txt_0', 'alpha.txt_0']], 'embeddings': None, 'documents': [['Implementing a rag code stuff\nSecret code is 19854', 'Nothing useful here!']], 'uris': None, 'included': ['metadatas', 'documents', 'distances'], 'data': None, 'metadatas': [[None, None]], 'distances': [[1.437341570854187, 1.6425095796585083]]}
results = {'ids': ['hi', None, 'yes', [None, 'hi']], 'dicts':{'htsdfdsf':None, 'dude': {'hi': 'hi', 'bra': None}}}
removal = []

def remove_nones(x):
    if isinstance(x, list):
        cleaned = [remove_nones(i) for i in x if i is not None]
        return [i for i in cleaned if i != []]

    elif isinstance(x, dict):
        cleaned = {
            k: remove_nones(v)
            for k, v in x.items()
            if v is not None
        }
        return {k: v for k, v in cleaned.items() if v != {} and v != []}

    return x
for key, data in results.items(): #my friend helped me with this recursion
    cleaned = remove_nones(data)
    if not cleaned:
        removal.append(key)
    print(cleaned)
    results[key] = cleaned
for i in removal:
    results.pop(i)

print(results)