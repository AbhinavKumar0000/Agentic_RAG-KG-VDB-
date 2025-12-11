# CortexRAG

CortexRAG is an advanced Retrieval-Augmented Generation (RAG) system that integrates Knowledge Graphs with Vector Search to provide highly accurate and context-aware answers. It features a hybrid search architecture, automated knowledge graph construction from documents, and interactive 2D/3D visualizations of the extracted data.

## Key Features

-   **Hybrid Search Architecture**: Intelligently routes queries between Vector Search (for semantic similarity) and Graph Search (for structural relationships) using a LangGraph-based agent.
-   **Automated Knowledge Graph Construction**: Uses Large Language Models (LLMs) to extract entities and relationships from unstructured text (PDFs and text files) and ingests them into a Neo4j database.
-   **Interactive Visualizations**: Provides dynamic 2D (PyVis) and 3D (Plotly) views of the knowledge graph, allowing users to explore connections between entities.
-   **Multi-Modal Data Ingestion**: Supports uploading and processing of both PDF and plain text documents.
-   **Modern User Interface**: Features a professional, minimal "Apple-style" web interface with dark mode, glassmorphism effects, and markdown rendering for rich text responses.
-   **Real-time Feedback**: Includes a polling mechanism to track the status of background graph extraction processes.

## Technology Stack

-   **Backend**: Flask (Python)
-   **Orchestration**: LangChain, LangGraph
-   **LLM & Embeddings**: Google Gemini (via `langchain-google-genai`)
-   **Graph Database**: Neo4j
-   **Vector Database**: PostgreSQL with `pgvector`
-   **Visualization**: NetworkX, PyVis, Plotly
-   **Frontend**: HTML5, CSS3, JavaScript (Vanilla)

## Prerequisites

Before running the application, ensure you have the following installed and configured:

1.  **Python 3.10+**
2.  **Neo4j Database**: A running instance (local or AuraDB) with APOC installed.
3.  **PostgreSQL Database**: A running instance with the `vector` extension enabled.
4.  **Google AI Studio API Key**: For Gemini models.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd GraphRAG
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
GOOGLE_API_KEY=your_google_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
POSTGRES_CONNECTION=postgresql+psycopg2://user:password@localhost:5432/dbname
```

## Usage

1.  Start the Flask application:
    ```bash
    python app.py
    ```

2.  Open your web browser and navigate to:
    ```
    http://localhost:5000
    ```

3.  **Upload Data**: Use the sidebar to select and upload a PDF or text document. The system will chunk the text, generate embeddings, and begin extracting the knowledge graph in the background.
4.  **Chat**: Once processing is complete, use the chat interface to ask questions about your documents. The agent will decide whether to use vector search or graph traversal to answer.
5.  **Visualize**: Click "View 2D Network" or "View 3D Graph" to explore the entities and relationships extracted from your data.

## Project Structure

-   `app.py`: Main Flask application server handling routes, file uploads, and background processing.
-   `agent.py`: Defines the LangGraph agent, routing logic, and database connections (Neo4j & Postgres).
-   `visualizer.py`: Contains logic for generating 2D and 3D graph visualizations using NetworkX, PyVis, and Plotly.
-   `templates/index.html`: The main frontend interface.
-   `static/style.css`: Professional styling for the application.
-   `requirements.txt`: List of Python dependencies.

## License

This project is open-source and available under the MIT License.
