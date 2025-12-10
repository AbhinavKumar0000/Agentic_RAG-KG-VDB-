import os
import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network
from neo4j import GraphDatabase

# Configuration
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

COLOR_MAP = {
    "Person": "#00FFFF", "Organization": "#FF00FF", "Document": "#00FF00", 
    "Concept": "#FFFF00", "Location": "#FF4500", "User": "#FFFFFF", "DEFAULT": "#FFFFFF"
}

def get_graph_data(user_id):
    """Helper to fetch data from Neo4j"""
    driver = GraphDatabase.driver(URI, auth=AUTH)
    G = nx.DiGraph()

    # Query: Fetch ANY node connected to the user, or created by the user
    # We look for nodes tagged with user_id OR connected to the User node
    query = """
    MATCH (n)-[r]->(m) 
    WHERE n.user_id = $uid OR m.user_id = $uid
    RETURN n, r, m 
    LIMIT 200
    """

    with driver.session() as session:
        result = session.run(query, uid=user_id)
        for record in result:
            source = record['n']
            target = record['m']
            
            s_id = source.element_id
            t_id = target.element_id
            
            s_label = list(source.labels)[0] if source.labels else "Node"
            t_label = list(target.labels)[0] if target.labels else "Node"
            
            # Use 'name' or 'id' property, fallback to label
            s_text = source.get('name') or source.get('id') or s_label
            t_text = target.get('name') or target.get('id') or t_label

            G.add_node(s_id, group=s_label, text=s_text)
            G.add_node(t_id, group=t_label, text=t_text)
            G.add_edge(s_id, t_id, label=record['r'].type)

    driver.close()
    return G

def generate_3d_graph(user_id):
    G = get_graph_data(user_id)
    if G.number_of_nodes() == 0: return None

    pos = nx.spring_layout(G, dim=3, seed=42, k=0.8)

    edge_x, edge_y, edge_z = [], [], []
    for edge in G.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z, mode='lines',
        line=dict(color='rgba(100, 200, 255, 0.3)', width=1), hoverinfo='none'
    )

    node_x, node_y, node_z, node_colors, node_texts = [], [], [], [], []
    for node in G.nodes():
        x, y, z = pos[node]
        node_x.append(x); node_y.append(y); node_z.append(z)
        group = G.nodes[node]['group']
        node_colors.append(COLOR_MAP.get(group, "#AAAAAA"))
        node_texts.append(G.nodes[node]['text'])

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z, mode='markers+text',
        marker=dict(size=6, color=node_colors, opacity=0.9),
        text=node_texts, textposition="top center",
        textfont=dict(color="rgba(255,255,255,0.8)", size=10)
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        paper_bgcolor='rgb(10, 10, 10)',
        scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
        showlegend=False, margin=dict(t=0, l=0, r=0, b=0)
    )

    filename = f"graph_3d_{user_id}.html"
    fig.write_html(os.path.join("static", filename))
    return filename

def generate_2d_graph(user_id):
    G = get_graph_data(user_id)
    if G.number_of_nodes() == 0: return None

    net = Network(height="700px", width="100%", bgcolor="#222222", font_color="white", cdn_resources='remote')
    
    # Convert NetworkX to PyVis
    for node, attrs in G.nodes(data=True):
        group = attrs.get('group', 'DEFAULT')
        color = COLOR_MAP.get(group, "#ffffff")
        net.add_node(node, label=attrs.get('text', 'Node'), title=group, color=color)

    for source, target, attrs in G.edges(data=True):
        net.add_edge(source, target, color="#555555")

    # Physics for cool effect
    net.force_atlas_2based()
    
    filename = f"graph_2d_{user_id}.html"
    output_path = os.path.join("static", filename)
    net.save_graph(output_path)
    return filename