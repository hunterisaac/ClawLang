#TODO
#Multiple agents with system prompt for tools too
#Multiple knowledge banks including feeding multiple into one agent
#Providers switching
import logging
from lark import Lark, UnexpectedInput, ast_utils, Transformer, v_args
from lark.tree import Meta
from lark.indenter import Indenter
import sys
import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--filename", default="north_star.ai")
args = parser.parse_args()
print(args.filename)
this_module = sys.modules[__name__]
grammar = r"""
start: statement+
statement: use_stm | knowledge_stm | agent_stm | main_stm | print_stm

use_stm: "use" "provider" PROVIDER "(" "model="string")" _NL

knowledge_stm: "knowledge" IDENTIFIER ":" _NL _INDENT knowledge_args _DEDENT 
knowledge_args: (source_args | topk_args)+
source_args: "source:" string _NL?
topk_args: "top_k:" ("-"? (INT | FLOAT)) _NL? #takes invalid params to later throw an error so people know what went wrong.

agent_stm: "agent" IDENTIFIER ":" _NL _INDENT system_p tool_args? _DEDENT
system_p: "persona:" string _NL?
tool_args: "tools:" "[" (IDENTIFIER ("," IDENTIFIER)*)? "]" _NL?

main_stm: "flow" IDENTIFIER "(" IDENTIFIER ")" ":" _NL _INDENT (workflow | print_stm)+ _DEDENT
workflow: (FLOW | IDENTIFIER) (">>" (FLOW  | IDENTIFIER ) )+ _NL
print_stm: "print" IDENTIFIER _NL?

%import common.ESCAPED_STRING
%import common.INT
%import common.SH_COMMENT
string : ESCAPED_STRING
PROVIDER: /[A-Z][a-zA-Z]*/ #string only
IDENTIFIER: /[A-Za-z][A-Za-z0-9\-\_]*/ #string,number combo
FLOAT: /((\d+\.\d*|\.\d+)(e[-+]?\d+)?|\d+(e[-+]?\d+))/i
FLOW: /[A-Za-z][A-Za-z0-9_\-]*\([A-Za-z0-9_, ]*\)/ #match actual functionish stuff
_NL: (/\r?\n[\t ]*/ | SH_COMMENT)+
%ignore " "
%declare _INDENT _DEDENT
"""
already_defined = ['ToolRegistry', '__init__', 'create_docs', 'search_docs', 'ToolResponse', 'FinalResponse', 'LLMResponse', 'system_prompt']
has_knowledge = False
class CompileError(Exception):
    def __init__(self, line, node_type, message, value):
        self.line = line
        self.node_type = node_type
        self.message = message
        self.value = value
    def __str__(self):
        return f"CompileError at line {self.line} in [{self.node_type}]: {self.message} '{self.value}'"
class writer:
    def __init__(self):
        self.lines = []
        self.ind_level = 0
        pass
    def writes(self, string):
        indent = ""
        for i in range(self.ind_level):
            indent = indent + "    "
        text = indent + string
        self.lines.append(text)
    def writelines(self, lines):
        for line in lines.splitlines():
            self.writes(line)
    def indent(self):
       self.ind_level += 1
    def dedent(self):
        self.ind_level -= 1
class TreeIndenter(Indenter):
    NL_type = '_NL'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 8
try:
    data_file_path = os.path.join(os.path.dirname(__file__), args.filename)
    with open(data_file_path) as f:
        text = f.read()
    tools_list = []
    workflow_items = []
    agents = {}
    knowledges = []
    top_k_args = None
    source_args = None
    printing = []
    parser = Lark(grammar, parser='lalr', postlex=TreeIndenter(), propagate_positions=True)
    tree = parser.parse(text)
    print(tree.pretty())
    knowledge_name = None
    for statement in tree.children:
        node = statement.children[0]  

        if node.data == "knowledge_stm":
            has_knowledge = True
            knowledge_name = node.children[0]
            for arg in range(len(node.children[1].children)):
                print(arg)
                if node.children[1].children[arg].data == "source_args":
                    source_args = node.children[1].children[arg].children[0].children[0]
                if node.children[1].children[arg].data == "topk_args":
                    top_k_args = node.children[1].children[arg].children[0]
            if source_args == None:
                raise CompileError(node.meta.line, "knowledge args", "Missing source args", str(node.children[1].children)) # check if it has source args
            top_k_args = top_k_args if top_k_args is not None else "3"
            if top_k_args.isdigit():
                top_k_args = int(top_k_args)
            else:
                raise CompileError(node.meta.line, "knowledge args", "Cannot be a float", str(node.children[1].children))
            if top_k_args < 1:
                raise CompileError(node.meta.line, "knowledge args", "top k args cannot be less than 1", str(node.children[1].children))    
            if knowledge_name.strip() not in knowledges:
                knowledges.append(str(knowledge_name.strip()))
            else:
                raise CompileError(node.meta.line, "knowledge args", "Knowledge already defined!", str(knowledge_name.strip()))
                 
        if node.data == "agent_stm":
            temp = []
            agent_name = node.children[0]
            for arg in node.children[1:]:
                if arg.data == "system_p":
                    system_prompt = arg.children[0].children[0]
                if arg.data == "tool_args":
                    for tool in arg.children:
                        tools_list.append(str(tool))
                        temp.append(str(tool))
            system_prompt = system_prompt if system_prompt is not None else "You are a helpful AI assistant."
            if str(agent_name.strip()) in agents:
                raise CompileError(node.meta.line, "Agent", "Agent already defined", str(agent_name.strip()))
            else:
                agents[str(agent_name.strip())] = {"system": system_prompt.strip(), "tools":temp}
            
        if node.data == "use_stm":
            provider = node.children[0]
            model = node.children[1].children[0]

        if node.data == "main_stm":
            func_name = node.children[0]
            func_params = node.children[1]
            for arg in node.children[2:]:
                if arg.data == "workflow":
                    for item in arg.children:
                        workflow_items.append(item)
                if arg.data == "print_stm":
                    printing.append(arg.children[0])
    #trying to assign pipeline 
    pipeline_knowledge = None
    pipeline_agent = None
    pipeline_agents = []
    pipeline_agent_param = []
    pipeline_output_var = []
    for item in workflow_items:
        if item == str(knowledge_name).strip():
            pipeline_knowledge = item
            if pipeline_knowledge not in knowledges:
                raise CompileError(item.line, "knowledge", f"Knowledge(rag database): {pipeline_knowledge} not defined in the knowledge list:", knowledges)
        elif "(" in item:
            pipeline_agent = item.split("(")[0]
            pipeline_agents.append(pipeline_agent)
            param = item.split("(")[1].strip(")")
            pipeline_agent_param.append(param)
            if pipeline_agent not in agents:
                raise CompileError(item.line, "agent", f"Agent: {pipeline_agent} not defined in the agent list:", agents)
        else:
            pipeline_output_var.append(item)
        print(item)
    if workflow_items[0] in pipeline_output_var:
        raise CompileError(workflow_items[0].line, "workflow", "Cannot start with an output variable", str(workflow_items))
    if pipeline_agent is None: 
        raise CompileError(0, "workflow", "Needs to have an agent", str(workflow_items))
    if not pipeline_output_var: 
        raise CompileError(0, "workflow", "Needs to have an output variable", str(workflow_items))
    # need to make it only knowledge -> agent and only agent -> output variable, decided to make new loop(cleaner)
    for item in range(len(workflow_items)):
        temp_agent_test = ""
        temp_param_test = "" #resest every loop
        real_agent = False
        try:
            temp_agent_test = workflow_items[item+1].split("(")[0]
            temp_param_test = workflow_items[item+1].split("(")[1].strip(")")
            if temp_agent_test in pipeline_agents and temp_param_test in pipeline_agent_param:
                real_agent = True
        except:
            pass
        if workflow_items[item] == pipeline_knowledge:      
            if real_agent: #making sure the knowledge is feeding into agent
                pass
            else:
                raise CompileError(workflow_items[item].line, "workflow", "Knowledge can only feed into the agent", str(workflow_items))
            
        if real_agent: #detects if agent exists and if it feeds into
            if item+2 >= len(workflow_items):
                raise CompileError(workflow_items[item+2].line, "workflow", "Workflow cannot end on an agent", str(workflow_items))
            nexttwo = workflow_items[item+2]
            try:
                temp_agent_test = nexttwo.split("(")[0]
                temp_param_test = nexttwo.split("(")[1].strip(")")
                if temp_agent_test in pipeline_agents and temp_param_test in pipeline_agent_param:
                    pass
                else:
                    raise CompileError(workflow_items[item+2].line, "workflow", "Agent cannot feed into undefined agent", str(temp_agent_test))
            except:
                if nexttwo not in pipeline_output_var : #needs +2 because its already +1 above
                    raise CompileError(workflow_items[item+2].line, "workflow", "Agent can only feed into an output variable or agent", str(workflow_items))

    print(workflow_items)
    w = writer()
    w.writelines("""import os
from typing import Literal, Union
from pydantic import BaseModel, ConfigDict, ValidationError, Field
from litellm import completion
import chromadb 
import json 
from langchain_text_splitters import RecursiveCharacterTextSplitter""")
    w.writes("")
    # Imports
    w.writes('api_key = os.environ.get("API_KEY")')
    w.writes(f'os.environ["{provider.upper()}_API_KEY"] = api_key')
    w.writes('client = chromadb.PersistentClient()')
    w.writes("")
    # Initialization
    w.writes("class ToolRegistry:")
    w.indent()
    w.writes("def __init__(self):")
    w.indent()
    w.writes("self.tools={}")
    w.dedent()
    w.writes("def register(self, name, fn):")
    w.indent()
    w.writes('self.tools[name] = {"description": fn.__doc__, "function": fn}')
    w.dedent()
    w.writes("def get(self, name):")
    w.indent()
    w.writes("try:")
    w.indent()
    w.writes("return self.tools[name]")
    w.dedent()
    w.writes("except:")
    w.indent()
    w.writes("return None")
    w.dedent()
    w.dedent()
    w.writes("def all(self):")
    w.indent()
    w.writes("return self.tools")
    w.dedent()
    w.dedent()
    w.writes("registry = ToolRegistry()")
    w.writes("")
    # Tool registry class
    if tools_list:
        tools_list = list(dict.fromkeys(tools_list)) #remove dupes, planning on per-agent tools later
        for tool in tools_list:
            w.writes(f"def {tool}(**args):")
            w.indent()
            w.writes('"""Tool Description for LLM"""')
            w.writes("# Logic goes here")
            w.writes("return None # change to return tool response ")
            w.dedent()
            w.writes(f'registry.register("{tool}", {tool})')
            w.writes("")
            if tool not in already_defined:
                already_defined.append(tool)
            else:
                raise CompileError(node.meta.line, "tools", "conflicting tool name; already defined", already_defined)
    # Tool Templates
    if has_knowledge:
        w.writes("def create_docs(collection_name, dir): #NOT AN LLM TOOL")
        w.indent()
        w.writes('"""Creates a chromadb RAG from all .txt files in directory. Takes args: collection_name, dir"""')
        w.writes("collection = client.get_or_create_collection(name=collection_name)")
        w.writes(r'splitter = RecursiveCharacterTextSplitter( chunk_size=500,chunk_overlap=50,separators=["\n\n", "\n", ". ", " "])')
        w.writes("arr = os.listdir(dir)")
        w.writes("ids = []")
        w.writes("texts = []")
        w.writes("for i in arr:")
        w.indent()
        w.writes("if i.endswith('.txt'): #only accepts .txt")
        w.indent()
        w.writes('with open(f"{dir}/{i}", "r") as f:')
        w.indent()
        w.writes("text = f.read()")
        w.dedent()
        w.writes("chunks = splitter.split_text(text)")
        w.writes("for x in range(len(chunks)):")
        w.indent()
        w.writes('ids.append(f"{i}_{x}")')
        w.writes('texts.append(chunks[x])')
        w.dedent()
        w.dedent()
        w.dedent()
        w.writes("if not ids:")
        w.indent()
        w.writes("print('No ids')")
        w.writes("return")
        w.dedent()
        w.writes("collection.upsert(ids = ids, documents=texts)")
        w.dedent()
        source_args_san = repr(str(source_args).strip('"'))
        w.writes(f'create_docs("{knowledge_name}", {source_args_san}) #generates RAG automatically on run')
        w.writes("")
        ###### Create docs
        w.writes(f"def search_docs(query, collection_name, k_results={top_k_args}):")
        w.indent()
        w.writes('"""Tool to search docs(RAG chromadb database), takes args: query, collection_name, k_results"""')
        w.writes("collection = client.get_or_create_collection(name=collection_name)")
        w.writes("MAX_CHARS = 6000")
        w.writes('final = ""')
        w.writes('results = collection.query(query_texts=[query], n_results=k_results)')
        w.writes("citations = results['ids'][0]")
        w.writes("text = results['documents'][0]")
        w.writes("for i in range(len(citations)):")
        w.indent()
        w.writes(r'chunk = f"Source: {citations[i]}, Content: {text[i]} \n"')
        w.writes("if len(final) + len(chunk) > MAX_CHARS:")
        w.indent()
        w.writes("break")
        w.dedent()
        w.writes("final = final + chunk")
        w.dedent()
        w.writes("return(final.strip())")
        w.dedent()
        w.writes('registry.register("search_docs", search_docs)')
        w.writes("")
    w.writes("class ToolResponse(BaseModel):")
    w.indent()
    w.writes("state: Literal['tool']")
    w.writes("tool_name: str")
    w.writes("tool_args: dict")
    w.dedent()
    w.writes("")
    # Tool response
    w.writes("class FinalResponse(BaseModel):")
    w.indent()
    w.writes("state: Literal['final']")
    w.writes("final_answer: str")
    w.dedent()
    w.writes("")
    # Final Response
    w.writes("class LLMResponse(BaseModel):")
    w.indent()
    w.writes("response_type: Union[ToolResponse, FinalResponse] = Field(discriminator='state')")
    w.dedent()
    w.writes("")
    #
    w.writes(f"def {func_name}({func_params},system_prompt):")
    w.indent()
    w.writes("")
    # LLM Response Class
    w.writes('message_history = [{"role": "system", "content": system_prompt}, {"role": "user", "content": ' + str(func_params) + '}]')
    w.writes("MAX_ITERATIONS = 5")
    w.writes("fails = 0")
    w.writes("")
    # some values
    w.writes("while True:")
    w.indent()
    model_san = repr(str(model).strip('"'))
    w.writes(f'response = completion(model={model_san},messages=message_history)')
    w.writes('response = response.choices[0].message.content')
    w.writes('message_history.append({"role":"assistant", "content": response})')
    w.writes('try:')
    w.indent()
    w.writes("amount_chars = len(response)")
    w.writes('start_index = response.index("{")')
    w.writes('end_index = response.rfind("}", start_index, amount_chars)')
    w.writes('data = json.loads(response[start_index:end_index+1])')
    w.writes('try:')
    w.indent()
    w.writes('response = LLMResponse(response_type=data)')
    w.writes('result = response.response_type')
    w.writes('if result.state == "final":')
    w.indent()
    w.writes("return(result.final_answer)")
    w.writes('fails = 0')
    w.writes('break')
    w.dedent()
    w.writes('if result.state =="tool":')
    w.indent()
    w.writes('if registry.get(result.tool_name):')
    w.indent()
    w.writes('try:')
    w.indent()
    w.writes("tool_response = registry.get(result.tool_name)['function'](**result.tool_args)")
    w.writes('message_history.append({"role":"user", "content": f"Tool({result.tool_name}) Response: {tool_response}"})')
    w.writes('print(f"Tool Called! {result.tool_name}({result.tool_args}) Response: {tool_response}")')
    w.writes('fails = 0')
    w.dedent()
    w.writes('except Exception as e:')
    w.indent()
    w.writes('message_history.append({"role":"user", "content": f"Args were invalid: {result.tool_args}"})')
    w.writes('fails += 1')
    w.writes('if fails == MAX_ITERATIONS:')
    w.indent()
    w.writes('fails = 0')
    w.writes("print(f'Max Fails({MAX_ITERATIONS} reached.)')")
    w.writes('break')
    w.dedent()
    w.dedent()
    w.dedent()
    w.writes("else:")
    w.indent()
    w.writes('message_history.append({"role":"user", "content": f"No tool with name: {result.tool_name}"})')
    w.writes('fails += 1')
    w.writes('if fails == MAX_ITERATIONS:')
    w.indent()
    w.writes('fails = 0')
    w.writes("print(f'Max Fails({MAX_ITERATIONS} reached.)')")
    w.writes('break')
    w.dedent()
    w.dedent()
    w.dedent()
    w.dedent()
    w.writes("")
    w.writes('except ValidationError as e:')
    w.indent()
    w.writes('e = f"{e}"')
    w.writes('message_history.append({"role": "user", "content": "error:" + e})')
    w.writes('fails += 1')
    w.writes('if fails == MAX_ITERATIONS:')
    w.indent()
    w.writes('fails = 0')
    w.writes("print(f'Max Fails({MAX_ITERATIONS} reached.)')")
    w.writes('break')
    w.dedent()
    w.dedent()
    w.dedent()
    w.writes("")
    w.writes('except Exception as e:')
    w.indent()
    w.writes('message_history.append({"role": "user", "content": "Invalid JSON"})')
    w.writes('fails += 1')
    w.writes('if fails == MAX_ITERATIONS:')
    w.indent()
    w.writes('fails = 0')
    w.writes("print(f'Max Fails({MAX_ITERATIONS} reached.)')")
    w.writes('break')
    w.dedent()
    w.dedent()
    w.dedent()
    w.dedent()
    w.writes("")
    w.writes('if __name__ == "__main__":')
    w.indent()
    json_prompt = 'You can only respond with one of two formats: one for calling tools: {"state": "tool", "tool_name": "tool", "tool_args": {"a": x, "b": y} } or one for stating an answer: {"state": "final", "final_answer": "blah blah blah"} Respond only in JSON '
    for pos, agent in enumerate(pipeline_agents):
        chunk = agents[agent]
        persona = str(chunk['system']).strip('"')
      #  if has_knowledge:
     #       w.writes(f"system_prompt = '{persona} {str(json_prompt)} Available RAG databases: {source_args}' ") - add knowledge databases later
      #  else:
        sanitize_system = repr(f'{persona} {str(json_prompt)}') #sanitized
        w.writes(f"system_prompt = {sanitize_system}")
        w.writes(r'tool_prompt = "TOOLS: \n"')
        w.writes("for key, value in registry.all().items():")
        w.indent()
        w.writes(f'existing = {chunk["tools"]}')
        w.writes(f'if key in existing:')
        w.indent()
        w.writes('tool_prompt = tool_prompt + f"Name: {key} - " + f"Description: {value[\'description\']}" + "\\n"')
        w.dedent()
        w.dedent()
        w.writes("system_prompt = system_prompt + tool_prompt")
        w.writes(f"{pipeline_output_var[pos]} = {func_name}('your query here',system_prompt) # query goes here")
        if printing:
            for prints in printing:
                w.writes(f'print({prints})') #prints all of them
    print(w.lines)
    w.dedent()
    with open('output.py', 'w') as f:
        for line in w.lines:
            f.write(f"{line}\n")
    print(workflow_items)
except UnexpectedInput as e:
    print("Error on line:", e.line, e)
except CompileError as e:
    print("Compile Error:", e)