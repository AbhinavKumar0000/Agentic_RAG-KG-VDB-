from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from agent import app_agent, vector_store, graph
from visualizer import generate_3d_graph, generate_2d_graph
from langchain_core.documents import Document

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

@app.route('/upload', methods=['POST'])
def upload_file():
    user_id = request.headers.get('X-User-ID')
    if 'file' not in request.files or not user_id:
        return jsonify({"error": "Missing data"}), 400
        
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    # 1. Postgres Ingestion
    content = f"Content of {filename}. This file is about AI and Graphs."
    doc = Document(page_content=content, metadata={"user_id": user_id, "source": filename})
    vector_store.add_documents([doc])
    
    # 2. Neo4j Ingestion (FIXED: Creates CONNECTIONS now)
    # We explicitly link the Document to the User so the visualizer has an edge to find.
    print(f"Ingesting graph data for {user_id}...")
    
    cypher_query = """
    MERGE (u:User {id: $uid})
    MERGE (d:Document {name: $fname, user_id: $uid})
    MERGE (u)-[:UPLOADED]->(d)
    MERGE (c:Concept {name: 'AI', user_id: $uid})
    MERGE (d)-[:MENTIONS]->(c)
    MERGE (c2:Concept {name: 'GraphRAG', user_id: $uid})
    MERGE (d)-[:USES]->(c2)
    """
    graph.query(cypher_query, params={"uid": user_id, "fname": filename})

    return jsonify({"message": f"Processed {filename}. Added to Postgres & Neo4j."})

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