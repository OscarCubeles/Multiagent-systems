import osmnx as ox
import random
import json
import os

def random_location(min_x, min_y, max_x, max_y):
    return {
        "x": random.uniform(min_x, max_x),
        "y": random.uniform(min_y, max_y)
}

def generate_input_json(output_file="input.json"):
    # Define constants and fixed variables
    graph_file = "olot.graphml"
    place_name = "Olot, Catalonia, Spain"
    query = "hospital"
    fire_types = ["ordinary", "electrical", "gas"]
    severities = ["low", "medium", "high"]
    ambulances_types = ["on-site", "transfer"]

    # Check if the graphml file exists
    if os.path.exists(graph_file):
        print(f"Graph file '{graph_file}' found. Loading map from file.")
        mapp = ox.load_graphml(graph_file)
    else:
        print(f"Graph file '{graph_file}' not found. Downloading map data.")
        # Load the city bounds for Olot, Catalonia
        mapp = ox.graph_from_place(place_name, network_type="drive")
        # Save the map to a file for future use
        ox.save_graphml(mapp, filepath=graph_file)

    # Convert the map to GeoDataFrames for nodes and edges
    nodes, _ = ox.graph_to_gdfs(mapp, nodes=True, edges=True)
    # Get the bounding box of the city
    min_x = nodes['x'].min()
    max_x = nodes['x'].max()
    min_y = nodes['y'].min()
    max_y = nodes['y'].max()

    # Generate random counts for fires, fire trucks, and ambulances
    num_fires = random.randint(1, 3)
    num_fire_trucks = random.randint(0, 5)
    num_ambulances = random.randint(1, 7)

    # Generate fires
    fires = []
    for i in range(1, num_fires + 1):
        fires.append({
            "id": i,
            "location": random_location(min_x, min_y, max_x, max_y),
            "type": random.choice(fire_types),
            "severity": random.choice(severities),
            "injured": {
                "minor": random.randint(0, 10),
                "serious": random.randint(0, 5)
            },
            "completed": False
        })

    # Generate fire trucks at random locations
    firetrucks = []
    for i in range(1, num_fire_trucks + 1):
        firetrucks.append({
            "id": i,
            "type": random.choice(fire_types),
            "location": random_location(min_x, min_y, max_x, max_y),
            "available": True
        })

    # Generate hospitals dynamically with name and capacity
    pois = ox.features_from_place(place_name, tags={"amenity": query})
    hospitals = []
    if not pois.empty:
        for idx, row in pois.iterrows():
            centroid = row.geometry.centroid
            hospital_name = row.get("name", "Unnamed Hospital")  # Extract the name or use "Unnamed Hospital" if not found
            hospitals.append({
                "id": len(hospitals) + 1,
                "name": hospital_name,
                "capacity": random.randint(1, 100),  # Random capacity
                "location": {"x": centroid.x, "y": centroid.y}
            })
    else:
        print("No hospitals found in Olot.")

    # Distribute ambulances among hospitals
    ambulances = []
    # Calculate how many ambulances will go to each hospital
    ambulances_per_hospital = num_ambulances // len(hospitals) if len(hospitals) > 0 else 0
    remaining_ambulances = num_ambulances % len(hospitals) if len(hospitals) > 0 else 0

    for i, hospital in enumerate(hospitals):
        # Assign ambulances to each hospital
        ambulances_for_hospital = ambulances_per_hospital + (1 if i < remaining_ambulances else 0)
        for j in range(ambulances_for_hospital):
            ambulances.append({
                "id": len(ambulances) + 1,
                "capacity": random.randint(2, 8),
                "location": hospital["location"],
                "available": True,
                "type": random.choice(ambulances_types)
            })

    # Combine all data into the JSON structure
    data = {
        "fires": fires,
        "firetrucks": firetrucks,
        "ambulances": ambulances,
        "hospitals": hospitals
    }

    # Write the data to a JSON file
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Generated input file saved to {output_file}")