#Creating the code my transpiler will need to generate
import os
from typing import Literal, Union
from pydantic import BaseModel, ConfigDict, ValidationError, Field
from litellm import completion
import os
import chromadb 
import json 
from langchain_text_splitters import RecursiveCharacterTextSplitter
api_key = os.environ.get("API_KEY")
os.environ["MISTRAL_API_KEY"] = api_key
client = chromadb.PersistentClient()
#Storing tool calls using decorators

class ToolRegistry:
    def __init__(self):
        self.tools={}
    def register(self, name, fn):
        self.tools[name] = {"description": fn.__doc__, "function": fn}
    def get(self, name):
        return self.tools[name]
    def all(self):
        return self.tools
registry = ToolRegistry()

def add(numbers):
   """Tool to add all # in a dict"""
   total = 0
   for x in numbers:
      total += numbers[x]
   return total
registry.register("add", add)
for i in registry.all().items():
    print(i)
def subtract(numbers):
   """Tool to subtract all # in a dict"""
   total = 0
   for x in numbers:
      total -= numbers[x]
   return total
registry.register("subtract", subtract)
def create_docs(collection_name, dir):
    """Tool to create a chromadb RAG. Takes args: collection_name, dir"""
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
registry.register("create_docs", create_docs)
def search_docs(query, collection_name, k_results):
    """Tool to search docs(RAG chromadb database), takes arges: query, collection_name, k_results"""
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
registry.register("search_docs", search_docs)
class ToolResponse(BaseModel):
    state: Literal['tool']
    tool_name: str
    tool_args: dict
class FinalResponse(BaseModel):
    state: Literal['final']
    final_answer: str
class LLMResponse(BaseModel):
    response_type: Union[ToolResponse, FinalResponse] = Field(discriminator='state')


