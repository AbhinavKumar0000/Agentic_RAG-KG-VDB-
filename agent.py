import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# FIXED IMPORT: Use langchain_neo4j if available, else fallback
try:
    from langchain_neo4j import Neo4jGraph, Neo4jVector
except ImportError:
    from langchain_community.graphs import Neo4jGraph
    from langchain_community.vectorstores import Neo4jVector
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

# Connect to Graph
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"), 
    username=os.getenv("NEO4J_USERNAME"), 
    password=os.getenv("NEO4J_PASSWORD")
)

# Connect to Vector
# Note: For simple local testing without pgvector setup, you can use FAISS/Chroma
# But assuming you have Postgres running:
from langchain_postgres import PGVector
CONNECTION_STRING = os.getenv("POSTGRES_CONNECTION", "postgresql+psycopg2://postgres:password@localhost:5432/postgres")
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="rag_docs",
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

class AgentState(TypedDict):
    question: str
    context: str
    answer: str
    user_id: str
    tool_used: str  # <--- Added this to track the tool

def router(state: AgentState):
    print(f"--- ROUTING: {state['question']} ---")
    system = "Classify: 'GRAPH' for relationships/connections, 'VECTOR' for content/summary."
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{question}")])
    classification = (prompt | llm).invoke({"question": state["question"]}).content.upper()
    
    if "GRAPH" in classification: return "graph_retrieval"
    return "vector_retrieval"

def vector_retrieval(state: AgentState):
    print(f"--- VECTOR SEARCH ---")
    results = vector_store.similarity_search(state["question"], k=2, filter={"user_id": state["user_id"]})
    context = "\n".join([d.page_content for d in results])
    return {"context": context, "tool_used": "Vector Search"}

def graph_retrieval(state: AgentState):
    print(f"--- GRAPH SEARCH ---")
    try:
        # Simple constrained retrieval for demo
        chain = GraphCypherQAChain.from_llm(llm, graph=graph, allow_dangerous_requests=True, verbose=True)
        # Inject filter into query
        q = f"{state['question']} (Limit to nodes with user_id='{state['user_id']}')"
        res = chain.invoke(q)
        return {"context": res['result'], "tool_used": "Graph Cypher"}
    except Exception as e:
        print(f"Graph Error: {e}")
        return {"context": "No graph data found.", "tool_used": "Graph Search (Failed)"}

def generate_answer(state: AgentState):
    prompt = f"Context: {state['context']}\nQuestion: {state['question']}\nAnswer:"
    res = llm.invoke(prompt)
    return {"answer": res.content}

workflow = StateGraph(AgentState)
workflow.add_node("vector_retrieval", vector_retrieval)
workflow.add_node("graph_retrieval", graph_retrieval)
workflow.add_node("generate_answer", generate_answer)

workflow.set_conditional_entry_point(router, {"vector_retrieval": "vector_retrieval", "graph_retrieval": "graph_retrieval"})
workflow.add_edge("vector_retrieval", "generate_answer")
workflow.add_edge("graph_retrieval", "generate_answer")
workflow.add_edge("generate_answer", END)

app_agent = workflow.compile()