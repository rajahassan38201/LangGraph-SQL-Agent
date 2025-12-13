import json
import uvicorn
from typing import TypedDict, Annotated, Optional
from uuid import uuid4

from langgraph.graph import add_messages, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from dotenv import load_dotenv 

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware  


# Import database setup and tools from sql.py
from sql import setup_database, list_tables_tool, query_sql_tool, tools

# Load API keys from .env file
load_dotenv()

# --- LangGraph Agent Setup ---

# Initialize memory saver
memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize the LLM and bind the imported tools
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools=tools)

# Define the agent nodes
async def model(state: State):
    """LLM node."""
    result = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [result]}

async def tools_router(state: State):
    """Router node to check for tool calls."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tool_node"
    else: 
        return END
    
async def tool_node(state):
    """Custom tool node that handles the SQL tool calls."""
    tool_calls = state["messages"][-1].tool_calls
    tool_messages = []
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]
        
        print(f"--- Executing Tool: {tool_name} with args {tool_args} ---")
        
        try:
            # We use the imported tool variables here
            if tool_name == "sql_db_list_tables":
                result = await list_tables_tool.ainvoke({}) 
            elif tool_name == "sql_db_query":
                result = await query_sql_tool.ainvoke(tool_args)
            else:
                result = f"Error: Unknown tool {tool_name}"
        except Exception as e:
            print(f"Error executing tool {tool_name}: {e}")
            result = f"Error executing tool: {str(e)}"

        tool_messages.append(ToolMessage(
            content=str(result),
            tool_call_id=tool_id,
            name=tool_name
        ))
    
    return {"messages": tool_messages}

# Build the graph
graph_builder = StateGraph(State)
graph_builder.add_node("model", model)
graph_builder.add_node("tool_node", tool_node)
graph_builder.set_entry_point("model")
graph_builder.add_conditional_edges("model", tools_router)
graph_builder.add_edge("tool_node", "model")

graph = graph_builder.compile(checkpointer=memory)

# --- FastAPI App Setup ---

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

# System prompt to guide the LLM
SYSTEM_PROMPT = (
    "You are a helpful AI assistant that interacts with a SQL database. "
    "The database is named 'company.db' and contains a table named 'Employees'. "
    "The 'Employees' table has the following columns: id (INTEGER, PRIMARY KEY), Name (TEXT), Age (INTEGER), "
    "Department (TEXT), Salary (REAL), Mobile (TEXT), Email (TEXT). "
    "Given a user's question, you must first decide if you need to query the database. "
    "If you need to query, you can use `sql_db_list_tables` to see tables, and then `sql_db_query` to get the answer. "
    "You must generate the SQL query yourself. Only query the columns necessary to answer the question. "
    "After you receive the SQL result, you must answer the user's original question in plain, natural language. "
    "If the question is not about the database, answer it as a general AI assistant."
)

async def generate_chat_responses(message: str, checkpoint_id: Optional[str] = None):
    """
    Generates and streams chat responses using Server-Sent Events (SSE).
    """
    is_new_conversation = checkpoint_id is None
    
    if is_new_conversation:
        new_checkpoint_id = str(uuid4())
        config = {"configurable": {"thread_id": new_checkpoint_id}}
        
        # Send the new checkpoint ID first
        yield f"data: {json.dumps({'type': 'checkpoint', 'checkpoint_id': new_checkpoint_id})}\n\n"
        
        # Prepare input with system prompt
        input_messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=message)
        ]
    else:
        config = {"configurable": {"thread_id": checkpoint_id}}
        input_messages = [HumanMessage(content=message)]

    # Start streaming events from the graph
    events = graph.astream_events(
        {"messages": input_messages},
        version="v2",
        config=config
    )

    async for event in events:
        event_type = event["event"]
        
        if event_type == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                # Stream content chunks
                yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"
                
        elif event_type == "on_chat_model_end":
            # Check if a SQL query tool call was made
            tool_calls = event["data"]["output"].tool_calls if hasattr(event["data"]["output"], "tool_calls") else []
            sql_query_calls = [call for call in tool_calls if call["name"] == "sql_db_query"]
            
            if sql_query_calls:
                sql_query = sql_query_calls[0]["args"].get("query", "")
                yield f"data: {json.dumps({'type': 'sql_query_start', 'query': sql_query})}\n\n"
                
        elif event_type == "on_tool_end":
            # Send SQL query results back to the client
            if event["name"] == "sql_db_query":
                output = event["data"]["output"]
                yield f"data: {json.dumps({'type': 'sql_query_result', 'result': output})}\n\n"

    # Send an end event when the stream is finished
    yield f"data: {json.dumps({'type': 'end'})}\n\n"

@app.get("/chat_stream/{message}")
async def chat_stream(message: str, checkpoint_id: Optional[str] = Query(None)):
    """
    FastAPI endpoint to handle streaming chat responses.
    """
    return StreamingResponse(
        generate_chat_responses(message, checkpoint_id), 
        media_type="text/event-stream"
    )

# Run the app
if __name__ == "__main__":
    setup_database() # Create and populate the database on startup

    uvicorn.run(app, host="127.0.0.1", port=8000)



