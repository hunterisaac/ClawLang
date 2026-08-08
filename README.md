ClawLang
A domain specific language(DSL) that compiles simple .ai files into a standalone ReAct agent loop with tools, optional RAG, and structured LLM responses via Pydantic.

How it works!
Pipeline
- Lark parses the .ai file into an AST(abstract syntax tree)
- The script processes the abstract syntax tree, checking for errors, duplicates, and logic flaws.
- The script then generates output.py and runs ast.parse to check if its valid code.
- It also dynamically generates a requirements.txt based on the modules required to run it.

What the output contains:
- The file imports the required modules such as pydantic for strict response regulation, litellm for easily interacting with different providers, chromadb for RAG databases, and other modules for data parsing.
- It initializes the script: 
-- checks for the api key
-- creates the tool registry
-- defines all the tools written in the .ai file
-- creates the RAG collection if needed (and generates the search_docs if needed)
-- defines the possible llm response formats(toolresponse and finalresponse)
-- generates the main ReAct loop which sends the actual message to the llm and loops until it is done.
-- At the end, the main loop will print the responses(if written) and loop through the different agents.

Installation
git clone https://github.com/hunterisaac/ClawLang.git
cd ClawLang
py -m pip install -r requirements.txt
CLI Usage
You can run
py -m lark_file --filename north_star.ai
and the output will be generated in the /output folder with the specific modules you need to pip install:
cd output
py -m pip install -r requirements.txt
Syntax

Examples
plain_agent.ai -
north_star.ai - 
agent_to_agent.ai -
knowledge_agent.ai -
Known Limitations / Coming in V2
Only handles one RAG database

Errors
Please open a github pull request if any errors are found. 

Motivation
The technical innovations behind OpenClaw inspired me to attempt the creation of my own ReAct loop using LangGraph. I quickly finished the tutorial, but realized that there were two problems:
1. I had absolutely no clue what the code was doing because of the unfamiliar modules like pydantic.
2. I wouldn't be able to recreate this on my own, even architecturally, without the use of a guide.
This led to the creation of ClawLang, the language inspired by openclaw, that would allow users to easily generate ReAct loops to build upon without the intense technical jargon.

License