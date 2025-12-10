from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import threading
from agent import app_agent, vector_store, graph, llm
from visualizer import generate_3d_graph, generate_2d_graph
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get('message')
    user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "No User ID provided"}), 400

    # Run Agent
    inputs = {"question": user_query, "user_id": user_id}
    result = app_agent.invoke(inputs)
    
    # Return answer AND the tool that was used (Graph vs Vector)
    return jsonify({
        "response": result['answer'],
        "tool": result.get('tool_used', 'Unknown')
    })

def process_graph_background(splits, user_id, filename):
    print(f"Background: Extracting graph data for {user_id}...")
    try:
        llm_transformer = LLMGraphTransformer(llm=llm)
        graph_documents = llm_transformer.convert_to_graph_documents(splits)
        
        # Add user_id to all nodes to support multi-tenancy/filtering
        for doc in graph_documents:
            for node in doc.nodes:
                node.properties["user_id"] = user_id
                
        graph.add_graph_documents(graph_documents)
        
        # Manually link documents to the user for visualization entry point
        # We can use a simple Cypher query to link the source documents to the User
        cypher_query = """
        MERGE (u:User {id: $uid})
        MERGE (d:Document {name: $fname})
        MERGE (u)-[:UPLOADED]->(d)
        """
        graph.query(cypher_query, params={"uid": user_id, "fname": filename})
        print(f"Background: Graph extraction complete for {filename}")
    except Exception as e:
        print(f"Background: Graph extraction failed: {e}")

@app.route('/upload', methods=['POST'])
def upload_file():
    user_id = request.headers.get('X-User-ID')
    if 'file' not in request.files or not user_id:
        return jsonify({"error": "Missing data"}), 400
        
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    # 1. Read File
    if filename.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        docs = loader.load()
    else:
        loader = TextLoader(file_path)
        docs = loader.load()
        
    # 2. Chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    # Add metadata
    for split in splits:
        split.metadata["user_id"] = user_id
        split.metadata["source"] = filename

    # 3. Postgres Ingestion (Vector)
    vector_store.add_documents(splits)
    
    # 4. Neo4j Ingestion (Graph) - Run in background
    thread = threading.Thread(target=process_graph_background, args=(splits, user_id, filename))
    thread.start()

    return jsonify({"message": f"Processed {filename}. Vector ingestion done. Graph extraction started in background."})

@app.route('/visualize/<mode>')
def visualize(mode):
    user_id = request.headers.get('X-User-ID')
    
    if mode == "2d":
        filename = generate_2d_graph(user_id)
    else:
        filename = generate_3d_graph(user_id)
    
    if not filename:
        return jsonify({"error": "No graph data found. Upload a file first!"}), 404
        
    return jsonify({"url": f"/static/{filename}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)