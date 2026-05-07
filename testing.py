from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import chromadb 
client = chromadb.PersistentClient()

query = "what is the password"
dir = 'rag_docs'
def create_docs(collection_name, dir):
    collection = client.get_or_create_collection(
        name=collection_name,
    )
    splitter = RecursiveCharacterTextSplitter( #taken from the docs website
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " "]
    )
    
    arr = os.listdir(dir)
    
    ids = []
    texts = []
    for i in arr:
        if i.endswith('.txt'): #only accepts .txt
            with open(f"{dir}/{i}", "r") as f:
                text = f.read()
        chunks = splitter.split_text(text)
        for x in range(len(chunks)):
            ids.append(f"{i}_{x}")
            texts.append(chunks[x])
    if not ids:
        print('No ids')
        return
    collection.upsert(ids = ids, documents=texts) 
def search_docs(query, collection_name, k_results):
    collection = client.get_or_create_collection(
        name=collection_name,
    )
    MAX_CHARS = 6000
    final = ""
    results = collection.query(
        query_texts=[query], #semantic match
        n_results=k_results,
    )
    citations = results['ids'][0]
    text = results['documents'][0]
    for i in range(len(citations)): #realized i didn't need the crazy loops lol
        chunk = f"Source: {citations[i]}, Content: {text[i]} \n"
        if len(final) + len(chunk) > MAX_CHARS:
            break
        final = final + chunk

    return(final.strip())
print(search_docs(query, "RAG", k_results=5))
#create_docs("RAG", dir)

