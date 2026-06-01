#Creating the code my transpiler will need to generate
import os
from typing import Literal, Union
from pydantic import BaseModel, ConfigDict, ValidationError, Field
from litellm import completion
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

def add(**numbers):
   """Tool to add all # in a dict"""
   return sum(numbers.values())
registry.register("add", add)
def subtract(**numbers):
   """Tool to subtract all # in a dict"""
   values = list(numbers.values())
   total = values[0]
   for x in values[1:]:
       total -= x
   return total
registry.register("subtract", subtract)
def multiply(**numbers):
   """Tool to multiply all # in a dict"""
   total = 1
   for x in numbers.values():
       total *= x
   return total
registry.register("multiply", multiply)
def create_docs(collection_name, dir):
    """Tool to create a chromadb RAG. Takes args: collection_name, dir"""
    collection = client.get_or_create_collection(name=collection_name,)
    splitter = RecursiveCharacterTextSplitter( chunk_size=500,chunk_overlap=50,separators=["\n\n", "\n", ". ", " "]) #taken from the docs website
    
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
    """Tool to search docs(RAG chromadb database), takes args: query, collection_name, k_results"""
    collection = client.get_or_create_collection(name=collection_name,)
    MAX_CHARS = 6000
    final = ""
    results = collection.query(query_texts=[query], n_results=k_results)
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


system_prompt = 'You are a mathematical genius. You can only respond with one of two formats: one for calling tools: {"state": "tool", "tool_name": "tool", "tool_args": {"a": x, "b": y} } or one for stating an answer: {"state": "final", "final_answer": "blah blah blah"} Respond only in JSON'
user_prompt = 'Subract 5 from 10'
tool_prompt = "TOOLS: \n"
for key, value in registry.all().items():
    tool_prompt = tool_prompt + f"Name: {key} - " + f"Description: {value['description']}" + "\n"
print(tool_prompt)
system_prompt = system_prompt + tool_prompt 
print(system_prompt)
message_history = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
MAX_ITERATIONS = 5
fails = 0
while True:
  response = completion(model="mistral/mistral-tiny",messages=message_history)
  response = response.choices[0].message.content
  message_history.append({"role":"assistant", "content": response})
  print("llm:",response)
  try:
    amount_chars = len(response) #getting json
    start_index = response.index("{") 
    end_index = response.rfind("}", start_index, amount_chars)
    data = json.loads(response[start_index:end_index+1])
    try:
      response = LLMResponse(response_type=data)
      result = response.response_type #need to extract data from response
      if result.state == "final":
        print(result.final_answer)
        fails = 0
        break
      if result.state =="tool":
         if registry.get(result.tool_name):
            try:
              tool_response = registry.get(result.tool_name)['function'](**result.tool_args)
              message_history.append({"role":"user", "content": f"Tool({result.tool_name}) Response: {tool_response}"})
              print(f"Tool Called! {result.tool_name}({result.tool_args}) Response: {tool_response}")
              fails = 0
            except Exception as e:
               message_history.append({"role":"user", "content": f"Args were invalid: {result.tool_args}"})
               fails += 1
               if fails == MAX_ITERATIONS:
                  fails = 0
                  print(f'Max Fails({MAX_ITERATIONS} reached.)')
                  break
         else:
            message_history.append({"role":"user", "content": f"No tool with name: {result.tool_name}"})
            fails += 1
            if fails == MAX_ITERATIONS:
                  fails = 0
                  print(f'Max Fails({MAX_ITERATIONS} reached.)')
                  break
    
                
        
    except ValidationError as e:
      e = f"{e}"
      message_history.append({"role": "user", "content": "error:" + e})
      fails += 1
      if fails == MAX_ITERATIONS:
         fails = 0
         print(f'Max Fails({MAX_ITERATIONS} reached.)')
         break

      
  except Exception as e:
     message_history.append({"role": "user", "content": "Invalid JSON"})
     fails += 1
     if fails == MAX_ITERATIONS:
         fails = 0
         print(f'Max Fails({MAX_ITERATIONS} reached.)')
         break
