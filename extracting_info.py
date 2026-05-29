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
text = """flow Main(query):
    secret_docs >> Hacker(query) >> answer 
    print answer
"""

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
    data = {}
    testing = []
    
    for statement in tree.children:
        node = statement.children[0]  
        if node.data == "knowledge_stm":
            name = node.children[0]
            for arg in node.children[1].children:
                if arg.data == "source_args":
                    source_args = node.children[1].children[0].children[0].children[0]
                if arg.data == "topk_args":
                    top_k_args = node.children[1].children[1].children[0]
        if node.data == "agent_stm":
            tools_list = []
            name = node.children[0]
            for arg in node.children[1:3]:
                if arg.data == "system_p":
                    system_prompt = arg.children[0].children[0]
                if arg.data == "tool_args":
                    for tool in arg.children:
                        print(tool)
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
               # if arg.data == "persona":
               #     persona = node.children[1].children[0].children[0].children[0]
               # if arg.data == "tool_args":
               #     tool_args = node.children[1].children[1].children[0]
              #  print(persona, tool_args)
            #print(knowledge_args)
            #print(name)
            #print(node.children[1].children[0].children[0].children)
       # print(value)
       
        
except UnexpectedInput as e:
    print("Error on line:", e.line, e)

class CompileError(Exception):
    def __init__(self, line, node_type, message, value):
        self.line = line
        self.node_type = node_type
        self.message = message
        self.value = value
    def __str__(self):
        return f"CompileError at line {self.line} in [{self.node_type}]: {self.message} '{self.value}'"
