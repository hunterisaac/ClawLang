

## ClawLang

*A domain specific language(DSL) that compiles simple .ai files into a standalone ReAct agent loop with tools, optional RAG, and structured LLM responses via Pydantic.*

  

## How it works!

Pipeline

- Lark parses the .ai file into an AST(abstract syntax tree)

- The script processes the abstract syntax tree, checking for errors, duplicates, and logic flaws.

- The script then generates output.py and runs ast.parse to check if it's valid code.

- It also dynamically generates a requirements.txt based on the modules required to run it.

  

What the output contains:

- The file imports the required modules such as pydantic for strict response regulation, litellm for easily interacting with different providers, chromadb for RAG databases, and other modules for data parsing.

- It initializes the script:

	- checks for the api key

	- creates the tool registry

	- defines all the tools written in the .ai file

	- creates the RAG collection if needed (and generates the search_docs if needed)

	- defines the possible llm response formats(toolresponse and finalresponse)

	- generates the main ReAct loop which sends the actual message to the llm and loops until it is done. if it fails at any point, retries with an error message appended. will keep retrying until a defined max amount of fails is reached.

	- At the end, the main loop will print the responses(if written) and loop through the different agents.

  

## Installation

    git clone https://github.com/hunterisaac/ClawLang.git
    
    cd ClawLang
    
    py -m pip install -r requirements.txt
    
    CLI Usage
    
    You can run
    
    py -m lark_file --filename north_star.ai

and the output will be generated in the /output folder with the specific modules you need to pip install:

    cd output
    
    py -m pip install -r requirements.txt

  

## Syntax

Use statement sets the model and the llm provider(view litellm docs for supported providers - https://models.litellm.ai/providers)

- use provider Provider(model="model") - the Provider must be capitalized

>  ex: use provider Mistral(model="mistral/mistral-tiny")

  

Knowledge statement defines a RAG database and arguments

- knowledge Knowledge_name:

  &nbsp;&nbsp;&nbsp;&nbsp;source: "./directory" *required

  &nbsp;&nbsp;&nbsp;&nbsp;top_k: int *optional, defaults to 3

ex: 
> 
> knowledge secret_docs:
> 
>  &nbsp;&nbsp;&nbsp;&nbsp;source: "./rag_docs"
> 
> &nbsp;&nbsp;&nbsp;&nbsp;top_k: 3

  

Agent statement defines an agent with a system prompt and available tools(generates template)

- agent Agent_name:

	&nbsp;&nbsp;&nbsp;&nbsp;persona: "system prompt"

 	&nbsp;&nbsp;&nbsp;&nbsp;tools: [tool, second_tool]

ex:

> - agent Hacker:
> 
> 	&nbsp;&nbsp;&nbsp;&nbsp;persona: "You are a master hacker. You think out of bounds and in unique way with the tools given to you."
> 
> 	&nbsp;&nbsp;&nbsp;&nbsp;tools: [add, multiply]

  

The flow statement puts everything together, specifying when agents are run, if they have a RAG database, and where the outputs go.

flow Main_func_name(Func_param):

*there are three different types of paramaters that you can use in the flow statement.

- a knowledge name (needs to plug into an agent)

- an agent and its paramater(prompt)

- the output variable where the response of the llm goes into

example statements:

> secret_docs >> Hacker(query) >> answer
> 
> secret_docs >> Student(answer) >> answer2

Additionally, it includes a print function where at the end of the code, it will print the output variables you want.

Use "print Variable"

ex:
> print answer2

Some Workflow Rules:

- Must start with either knowledge or agent

- Must end with output variable

  

Examples

plain_agent.ai - The simplest version. Contains a working agent example, defines a simple agent without tools, and creates a query that will have it respond to a single prompt.

north_star.ai - The original goal of the project was to run this finished version. It defines the provider, creates an agent, but also includes a RAG database. It essentially does the same as plain_agent.ai while including an optional RAG database for the agent to call.

agent_to_agent.ai - This is a more complex version of the north_star.ai It includes the same knowledge plugged into an agent which will output a variable, but that output is plugged into another agent creating a chain of agentic reasoning.

knowledge_agent.ai - Essentially the same as agent_to_agent.ai, but it has two agents running one after another with a knowledge doc plugged into each.

Known Limitations / Coming in V2

Only handles one RAG database

  

Errors

Please open a github pull request if any errors are found.

  

Motivation

The technical innovations behind OpenClaw inspired me to attempt the creation of my own ReAct loop using LangGraph. I quickly finished the tutorial, but realized that there were two problems:

1. I had absolutely no clue what the code was doing because of the unfamiliar modules like pydantic.

2. I wouldn't be able to recreate this on my own, even architecturally, without the use of a guide.

This led to the creation of ClawLang, the language inspired by openclaw, that would allow users to easily generate ReAct loops to build upon without the intense technical jargon.

  

Usage of AI within this project

- I used AI minimally, hand-writing all code and only asking it for specific architectural feedback along with finding niche test cases where my script would fail.
