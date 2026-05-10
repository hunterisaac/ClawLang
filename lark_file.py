import logging
from lark import Lark, logger
grammar = r"""
start: statement+
statement: use_stm | knowledge_stm
use_stm: "use" "provider" PROVIDER "(" "model="string")" NEWLINE
knowledge_stm: "knowledge" RAGNAME ":" NEWLINE 

%import common.ESCAPED_STRING
%import common.NEWLINE
%import common.INDENT
string : ESCAPED_STRING
PROVIDER: /[A-Z][a-zA-Z]*/
RAGNAME: /[A-Za-z][A-Za-z0-9\-\_]*/
%ignore " "
"""
text = '''use provider Mistral(model="mistral/mistral-tiny")
knowledge secret_docs:
    source: "./rag_docs"
    top_k: 3'''
#agent Hacker: 
#    persona: "You are a master hacker. You think out of bounds and in unique ways with the tools given to you."
#    tools: [add, multiply]
#
#flow Main(query):
#    secret_docs >> Hacker(query) >> answer 
#    print answer'''
parser = Lark(grammar)
tree = parser.parse(text)
print(tree.pretty())