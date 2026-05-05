from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import chromadb 
splitter = RecursiveCharacterTextSplitter( #taken from the docs website
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " "]
)
dir = 'rag_docs'
arr = os.listdir(dir)
client = chromadb.PersistentClient()
collection = client.get_or_create_collection(
    name="RAG",
)
ids = []
texts = []
for i in arr:
    f = open(f"{dir}/{i}")
    text = f.read()
    chunks = splitter.split_text(text)
    for x in range(len(chunks)):
        ids.append(f"{i}_{x}")
        texts.append(chunks[x])
    f.close()

collection.add(ids = ids, documents=texts) 
results = collection.query(
    query_texts=["what is the password"], #semantic match
    n_results=2,
)
removal = []
print(results)
def remove_nones(x):
        if isinstance(x, list):
            cleaned = [remove_nones(i) for i in x if i is not None]
            return [i for i in cleaned if i != []]
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




