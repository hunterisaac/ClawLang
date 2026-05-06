from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import chromadb 
def create_docs(collection):
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    splitter = RecursiveCharacterTextSplitter( #taken from the docs website
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "]
    )
    dir = 'rag_docs'
    arr = os.listdir(dir)
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

    collection.upsert(ids = ids, documents=texts) 
def search_docs(query, collection):
    
    results = collection.query(
        query_texts=[query], #semantic match
        n_results=3,
    )
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
        results[key] = cleaned
    for i in removal:
        results.pop(i)

    print(results)

query = "what is the password"
client = chromadb.PersistentClient()

collection = client.get_or_create_collection(
    name="RAG",
)
#search_docs(query, collection)
create_docs(collection)