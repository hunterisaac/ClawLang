import logging
from lark import Lark, UnexpectedInput, ast_utils, Transformer, v_args
from lark.tree import Meta
from lark.indenter import Indenter
import sys
this_module = sys.modules[__name__]
grammar = r"""
start: statement+
statement: use_stm | knowledge_stm | agent_stm | main_stm | print_stm

use_stm: "use" "provider" PROVIDER "(" "model="string")" _NL

knowledge_stm: "knowledge" IDENTIFIER ":" _NL _INDENT knowledge_args _DEDENT 
knowledge_args: (source_args | topk_args)+
source_args: "source:" string _NL?
topk_args: "top_k:" INT _NL?

agent_stm: "agent" IDENTIFIER ":" _NL _INDENT system_p tool_args? _DEDENT
system_p: "persona:" string _NL?
tool_args: "tools:" "[" (IDENTIFIER ("," IDENTIFIER)*)? "]" _NL?

main_stm: "flow" IDENTIFIER "(" IDENTIFIER ")" ":" _NL _INDENT (workflow | print_stm)+ _DEDENT
workflow: IDENTIFIER (">>" (FLOW  | IDENTIFIER ) )+ _NL
print_stm: "print" IDENTIFIER _NL?

%import common.ESCAPED_STRING
%import common.INT
%import common.SH_COMMENT
string : ESCAPED_STRING
PROVIDER: /[A-Z][a-zA-Z]*/ #string only
IDENTIFIER: /[A-Za-z][A-Za-z0-9\-\_]*/ #string,number combo

FLOW: /[A-Za-z][A-Za-z0-9_\-]*\([A-Za-z0-9_, ]*\)/ #match actual functionish stuff
_NL: (/\r?\n[\t ]*/ | SH_COMMENT)+
%ignore " "
%declare _INDENT _DEDENT
"""
with open(r"C:\Users\Hunter\Documents\GitHub\Python-Transpiler\lark_files\north_star.ai") as f:
    text = f.read()
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
    parser = Lark(grammar, parser='lalr', postlex=TreeIndenter(), propagate_positions=True)
    tree = parser.parse(text)
    print(tree.pretty())
    for statement in tree.children:
        node = statement.children[0]  
        if node.data == "knowledge_stm":
            knowledge_name = node.children[0]
            for arg in node.children[1].children:
                if arg.data == "source_args":
                    source_args = node.children[1].children[0].children[0].children[0]
                if arg.data == "topk_args":
                    top_k_args = node.children[1].children[1].children[0]
        if node.data == "agent_stm":
            tools_list = []
            agent_name = node.children[0]
            for arg in node.children[1:3]:
                if arg.data == "system_p":
                    system_prompt = arg.children[0].children[0]
                if arg.data == "tool_args":
                    for tool in arg.children:
                        tools_list.append(str(tool))
        if node.data == "use_stm":
            provider = node.children[0]
            model = node.children[1].children[0]
        if node.data == "main_stm":
            workflow_items = []
            func_name = node.children[0]
            func_params = node.children[1]
            for arg in node.children[2:]:
                if arg.data == "workflow":
                    for item in arg.children:
                        workflow_items.append(str(item))
                if arg.data == "print_stm":
                    printing = arg.children[0]
            print(knowledge_name, source_args, top_k_args, tools_list, system_prompt, provider, model, func_name, func_params, workflow_items, printing)
except UnexpectedInput as e:
    print("Error on line:", e.line, e)




w = writer()
w.writelines("""import os
from typing import Literal, Union
from pydantic import BaseModel, ConfigDict, ValidationError, Field
from litellm import completion
import chromadb 
import json 
from langchain_text_splitters import RecursiveCharacterTextSplitter""")
# Imports
w.writes('api_key = os.environ.get("API_KEY")')
w.writes(f'os.environ["{provider.upper()}_API_KEY"] = api_key')
w.writes('client = chromadb.PersistentClient()')
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
w.writes("return self.tools[name]")
w.dedent()
w.writes("def all(self):")
w.indent()
w.writes("return self.tools")
w.dedent()
w.dedent()
# Tool registry class
w.writes("class ToolResponse(BaseModel):")
w.indent()
w.writes("state: Literal['tool']")
w.writes("tool_name: str")
w.writes("tool_args: dict")
w.dedent()
# Tool response
w.writes("class FinalResponse(BaseModel):")
w.indent()
w.writes("state: Literal['final']")
w.writes("final_answer: str")
w.dedent()
# Final Response
w.writes("class LLMResponse(BaseModel):")
w.indent()
w.writes("response_type: Union[ToolResponse, FinalResponse] = Field(discriminator='state')")
w.dedent()
# LLM Response Class
w.writes(f"system_prompt = '{system_prompt}'")
w.writes("user_prompt = query")
w.writes('tool_prompt = "TOOLS: \n"')
w.writes("for key, value in registry.all().items():")
w.indent()
w.writes('tool_prompt = tool_prompt + f"Name: {key} - " + f"Description: {value["description"]}" + "\n"')
w.dedent()
w.writes("system_prompt = system_prompt + tool_prompt")
w.writes('message_history = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]')
w.writes("MAX_ITERATIONS = 5")
w.writes("fails = 0")
# some values

print(w.lines)
