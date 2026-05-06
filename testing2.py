#results = {'ids': [['secret.txt_0', 'alpha.txt_0']], 'embeddings': None, 'documents': [['Implementing a rag code stuff\nSecret code is 19854', 'Nothing useful here!']], 'uris': None, 'included': ['metadatas', 'documents', 'distances'], 'data': None, 'metadatas': [[None, None]], 'distances': [[1.437341570854187, 1.6425095796585083]]}
results = {'ids': [['secret.txt_0', 'alpha.txt_0', 'blop.txt_0', 'yadda.txt_0', 'roop.txt_0']], 'documents': [['Implementing a rag code stuff\nSecret code is 19854', 'Nothing useful here!', 'Why are you here lol', 'Who are you?!', "How's it going?"]], 'included': ['metadatas', 'documents', 'distances'], 'distances': [[1.437341570854187, 1.6425095796585083, 1.7057721614837646, 1.7472952604293823, 1.89181387424469]]}
removal = []

documents = results['ids'][0]
text = results['documents'][0]

for i in range(len(documents)): #realized i didn't need the crazy loops lol
    print(f"Source: documents[i], Content: text[i]")