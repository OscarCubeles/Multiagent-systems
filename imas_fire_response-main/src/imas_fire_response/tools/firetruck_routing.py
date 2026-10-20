import json
import osmnx as ox
import os

from crewai_tools import BaseTool
from pydantic import BaseModel
from typing import Type, Any


class DistanceCalculatorSchema(BaseModel):
    pass

class FireRouting(BaseTool):
    name: str = "Firetucks Route Calculator Tool"
    description: str = (
        "Calculates the distance from firetrucks to the fire location and adds the routing parameter for each firetruck."
    )
    args_schema: Type[BaseModel] = DistanceCalculatorSchema

    def _run(self, **kwargs: Any) -> Any:
        try:
            # Load the medical report
            with open("fire_report_2.json", "r") as file:
                data = json.load(file)

            if "firetrucks" in data:
                del data["firetrucks"]

            # Define constants and load the map data
            graph_file = "olot.graphml"
            place_name = "Olot, Catalonia, Spain"
            # Check if the graphml file exists
            if os.path.exists(graph_file):
                mapp = ox.load_graphml(graph_file)
            else:
                # Load the city bounds for Olot, Catalonia
                mapp = ox.graph_from_place(place_name, network_type="drive")
                # Save the map to a file for future use
                ox.save_graphml(mapp, filepath=graph_file)
                
            # Add speeds and travel times to the graph
            mapp = ox.routing.add_edge_speeds(mapp, fallback=50.0)
            mapp = ox.routing.add_edge_travel_times(mapp)        

            # Variable to store the formatted message
            response_message = ""  # This will store the formatted message for all routes

            # Compute shortest paths for fires
            for fire in data["fires"]:
                fire_id = fire["id"]  # Extract fire ID
                x_destination = fire["location"]["x"]
                y_destination = fire["location"]["y"]
                
                response_message += f"Routes for Fire {fire_id} with location: ({x_destination}, {y_destination})\n"

                for firetruck in fire["firetrucks"]:
                    firetruck_id = firetruck["id"]  # Extract ambulance ID
                    firetruck["available"] = True
                    x_origin = firetruck["location"]["x"]
                    y_origin = firetruck["location"]["y"]
                    
                    # Find the nearest nodes to the origin and destination coordinates
                    origin_node = ox.distance.nearest_nodes(mapp, X=x_origin, Y=y_origin)
                    destination_node = ox.distance.nearest_nodes(mapp, X=x_destination, Y=y_destination)
                    
                    # Find the shortest path based on travel time
                    route = ox.shortest_path(mapp, origin_node, destination_node, weight='travel_time')
                    
                    # Extract route information
                    route_gdf = ox.routing.route_to_gdf(mapp, route)
                    total_time = sum(route_gdf['travel_time'])
                    total_distance = sum(route_gdf['length'])
                    streets = route_gdf['name'].fillna("NaN").tolist()

                    # Remove duplicates from the streets list while handling NaN values
                    cleaned_streets = [street for street in streets if isinstance(street, str) and street != "NaN"]
                    unique_streets = list(dict.fromkeys(cleaned_streets))  # Removes duplicates while maintaining order

                    # Update ambulance information for fire
                    firetruck["route_to_fire"] = {
                        "nodes": unique_streets,
                        "route_time": round(total_time, 2),  # Total travel time in seconds
                        "distance": round(total_distance, 2)  # Total distance in meters
                    }

                    # Add this ambulance's route to the response message
                    response_message += f"  Firetruck {firetruck_id} - Route to fire {fire_id}: \n"
                    response_message += "    Streets: " + " -> ".join(unique_streets) + "\n"
                    response_message += f"    Total Time: {round(total_time, 2)} seconds\n"
                    response_message += f"    Total Distance: {round(total_distance, 2)} meters\n\n"

            # Write updated data to a new JSON file
            with open("fire_report_3.json", "w") as output_file:
                json.dump(data, output_file, indent=4)
                
            with open("fire_routing.txt", "w") as output_file:
                output_file.write(response_message)

            # Return the formatted message with all routes, times, and distances
            return response_message
        
        except Exception as e:
            return f"Failed to generate fire suppression plans. Error: {e}"