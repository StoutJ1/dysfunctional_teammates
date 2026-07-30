import json
import networkx as nx
import matplotlib.pyplot as plt
import sys
def visualize_map(json_file_path):
    """
    Reads a room-based map from a JSON file and visualizes it using NetworkX and Matplotlib.
    Uses Kamada-Kawai layout for better spacing and readability.
    """
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return

    G = nx.Graph()
    
    # Parse rooms and items
    for room in data.get('rooms', []):
        room_id = room['id']
        room_name = room['name']
        items = [item['name'] for item in room.get('items', [])]
        item_str = "\n".join(items) if items else ""
        
        # Node label will be "Name\n(Items)"
        label = f"{room_name}"
        if item_str:
            label += f"\n{item_str}"
        
        G.add_node(room_id, label=label)

        # Parse connections
        for conn in room.get('connections', []):
            target_id = conn['target_room_id']
            G.add_edge(room_id, target_id)

    if not G.nodes():
        print("No rooms found in the JSON file.")
        return

    # Set up the layout
    plt.figure(figsize=(15,15))
    
    # Use Kamada-Kawai layout for better spacing and less edge crossing
    try:
        pos = nx.kamada_kawai_layout(G,scale=30)
    except Exception as e:
        print(f"Kamada-Kawai failed, falling back to spring layout: {e}")
        pos = nx.spring_layout(G, k=1.5)

    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1, edge_color='gray', alpha=0.6)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=9000, node_color='lightblue')

    # Draw labels
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_weight='bold')

    plt.title(f"Map: {data.get('metadata', {}).get('environment_name', 'Unknown')}", fontsize=15)
    plt.axis('off')
    
    output_filename = "map_visualization.png"
    
    plt.savefig(output_filename)
    print(f"Visualization saved to {output_filename}")
    map = nx.draw(G)
    plt.show()

if __name__ == "__main__":
    # Test with the sample file provided by JSON_Architect
    map = visualize_map(sys.argv[1])

