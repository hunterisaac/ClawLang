import logging
from lark import Lark, logger
from lark.indenter import Indenter
grammar = r"""
start: statement+
statement: use_stm | knowledge_stm | agent_stm | main_stm | workflow | print_stm

use_stm: "use" "provider" PROVIDER "(" "model="string")" _NL

knowledge_stm: "knowledge" IDENTIFIER ":" _NL _INDENT knowledge_args _DEDENT 
knowledge_args: (source_args | topk_args)+
source_args: "source:" string _NL?
topk_args: "top_k:" INT _NL?

agent_stm: "agent" IDENTIFIER ":" _NL _INDENT system_p tool_args? _DEDENT
system_p: "persona:" string _NL?
tool_args: "tools:" "[" (WORD ("," WORD)*)? "]" _NL?

main_stm: "flow" IDENTIFIER "(" IDENTIFIER ")" ":" _NL _INDENT
workflow: IDENTIFIER (">>" (FLOW  | IDENTIFIER ) )+ _NL + _DEDENT?
print_stm: "print" FLOW _NL

%import common.ESCAPED_STRING
%import common.INT
%import common.WORD
%import common.SH_COMMENT
string : ESCAPED_STRING
PROVIDER: /[A-Z][a-zA-Z]*/ #string only
IDENTIFIER: /[A-Za-z][A-Za-z0-9\-\_]*/ #string,number combo
FLOW: /[A-Za-z][A-Za-z0-9\-\_\(\)]*/ #string,number combo parenthesis
_NL: (/\r?\n[\t ]*/ | SH_COMMENT)+
%ignore " "
%declare _INDENT _DEDENT
"""
text = '''use provider Mistral(model="mistral/mistral-tiny")
knowledge secret_docs:
    source: "./rag_docs"
    top_k: 3
agent Hacker: 
    persona: "You are a master hacker. You think out of bounds and in unique ways with the tools given to you."
    tools: [add, multiply]
flow Main(query):
    secret_docs >> Hacker(query) >> answer 
print answer 
'''  





class TreeIndenter(Indenter):
    NL_type = '_NL'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 8
parser = Lark(grammar, parser='lalr', postlex=TreeIndenter())
tree = parser.parse(text)
print(tree.pretty())