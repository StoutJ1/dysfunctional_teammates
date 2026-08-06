import json
import networkx as nx
import matplotlib.pyplot as plt
import sys
import math
from collections import defaultdict

def visualize_map(json_file_path):
    """
    Reads a room-based map from a JSON file and visualizes it using NetworkX and Matplotlib.
    """
    

    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return

    G = nx.MultiDiGraph() 
    
    default_type_to_color = {
        'exterior': 'lightgray',
        'hallway': 'skyblue',
        'laboratory': 'salmon',
        'office': 'lightgreen',
        'residential': 'wheat',
        'kitchen': 'orange',
        'storage': 'peru',
        'other': 'orchid'
    }
    
    metadata = data.get('metadata', {})
    schema_colors = metadata.get('room_type_colors', {})
    type_to_color = {**default_type_to_color, **schema_colors}
    agent_names = metadata.get('agents_present',[])
    print(f"DEBUG: Processing agent_names: {agent_names}")

    rooms = data.get('rooms', [])
    if not rooms:
        print("No rooms found in the JSON file.")
        return

    for room in rooms:
        room_id = room.get('id')
        if not room_id:
            continue
            
        room_name = room.get('name', 'Unknown Room')
        room_type = room.get('type', 'other')
        
        items = room.get('items', [])
        item_names = []
        for item in items:
            if isinstance(item, str):
                name = item
            elif isinstance(item, dict):
                name = item.get('name', 'Unknown Item')
            else:
                name = str(item)
            
            # Prefix agent names with "Agent: "
            if name in agent_names:
                name = f"Agent: {name}"
            
            item_names.append(name)
        
        items_str = "\n".join(item_names) if item_names else ""
        label = f"{room_name}"
        if items_str:
            label += f"\n{items_str}"
        
        G.add_node(room_id, label=label, type=room_type)

        connections = room.get('connections', [])
        for conn in connections:
            target_id = conn.get('target_room_id')
            conn_type = conn.get('type', 'connection')
            if target_id:
                G.add_edge(room_id, target_id, type=conn_type)

    node_list = list(G.nodes())
    node_labels = nx.get_node_attributes(G, 'label')
    node_types = nx.get_node_attributes(G, 'type')
    
    colors = []
    for node in node_list:
        rtype = node_types.get(node, 'other')
        colors.append(type_to_color.get(rtype, type_to_color.get('other', 'orchid')))

    edges = list(G.edges(data=True))
    edge_colors = []
    conn_type_colors = {
        'path': 'gray',
        'door': 'brown',
        'staircase': 'blue',
        'hallway': 'green',
        'elevator': 'purple'
    }

    for u, v, d in edges:
        ctype = d.get('type', 'connection')
        edge_colors.append(conn_type_colors.get(ctype, 'black'))

    plt.figure(figsize=(20, 20))
    
    try:
        pos = nx.kamada_kawai_layout(G, scale=30)
    except Exception as e:
        pos = nx.spring_layout(G, k=2.0)

    nx.draw_networkx_edges(G, pos, width=2, edge_color=edge_colors, arrowsize=20)

    simple_G = nx.Graph(G)
    edge_labels_simple = {}
    for u, v, d in edges:
        if (u, v) not in edge_labels_simple and (v, u) not in edge_labels_simple:
             edge_labels_simple[(u, v)] = d.get('type', 'connection')
        elif (v, u) in edge_labels_simple:
             edge_labels_simple[(v, u)] = d.get('type', 'connection')
    nx.draw_networkx_edge_labels(simple_G, pos, edge_labels=edge_labels_simple, font_size=7)

    x_nodes = [pos[n][0] for n in node_list]
    y_nodes = [pos[n][1] for n in node_list]
    plt.scatter(x_nodes, y_nodes, s=15000, c=colors, alpha=0.9, edgecolors='none', zorder=1)
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=9, font_weight='bold')

    env_name = metadata.get('environment_name', 'Unknown Environment')
    plt.title(f"Map Visualization: {env_name}\nType: {metadata.get('environment_type', 'N/A')}", fontsize=20)
    plt.axis('off')
    
    from matplotlib.lines import Line2D
    legend_elements = []
    legend_elements += [Line2D([0], [0], color=c, lw=2, label=t) 
                        for t, c in conn_type_colors.items() if t in [d.get('type') for _, _, d in edges]]

    if legend_elements:
        plt.legend(handles=legend_elements, loc='upper right', title="Legend", fontsize=12)

    output_filename = "map_visualization_improved.png"
    plt.savefig(output_filename, bbox_inches='tight')
    print(f"Visualization saved to {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg_map = sys.argv[1]
        arg_agents = sys.argv[2] if len(sys.argv) > 2 else None
        visualize_map(arg_map)
    else:
        print("Usage: python visualizer.py <path_to_json_map>")

