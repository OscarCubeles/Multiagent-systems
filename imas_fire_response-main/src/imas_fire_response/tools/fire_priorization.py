import json
import math
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any

def calculate_distance(loc1, loc2):
    """
    Calculate Euclidean distance between two points.
    loc1, loc2: Dictionaries containing 'x' and 'y' coordinates.
    """
    return math.sqrt((loc1['x'] - loc2['x']) ** 2 + (loc1['y'] - loc2['y']) ** 2)

class FireSorterSchema(BaseModel):
    distance_weight: float = Field(
        1.0, description="Float importance weight assigned to the distance between the fire location and the nearest hospital. Higher values means more importance."
    )
    severity_weight: float = Field(
        1.0, description="Float importance weight assigned to the severity of the fire. Higher values means more importance."
    )
    type_weight: float = Field(
        1.0, description="Float importance weight assigned to the type of fire. Higher values means more importance."
    )
    injured_weight: float = Field(
        1.0, description="Float importance weight to the number of injured individuals at the fire location. Higher values means more importance."
    )

class FirePriorizationTool(BaseTool):
    name: str = "Fire Priorization"
    description: str = "Prioritizes fires from the incident report according to their importance, using weighted criteria such as distance to hospitals, severity, type, and the number of injured."
    args_schema: Type[BaseModel] = FireSorterSchema

    def _run(self, distance_weight=1.0, severity_weight=1.0, type_weight=1.0, injured_weight=1.0, **kwargs: Any) -> Any:
        try:
            # Load the input file
            with open("input.json", "r") as file:
                data = json.load(file)

            # Fire type and severity weights
            type_weights = {"ordinary": 0.5, "electrical": 0.7, "gas": 0.9}
            severity_weights = {"low": 0.3, "medium": 0.5, "high": 0.9}

            # Calculate the prioritization score for each fire
            for fire in data['fires']:
                # Find the nearest hospital
                nearest_hospital_distance = min(
                    calculate_distance(fire['location'], hospital['location'])
                    for hospital in data['hospitals']
                )

                # Compute individual contributions to the score
                distance_contrib = 1 / (1 + nearest_hospital_distance) * distance_weight
                severity_contrib = severity_weights[fire['severity']] * severity_weight
                type_contrib = type_weights[fire['type']] * type_weight
                injured_contrib = (
                    fire['injured']['minor']
                ) * injured_weight

                # Calculate total prioritization score
                fire['prioritization_score'] = (
                    distance_contrib + severity_contrib + type_contrib + injured_contrib
                )
                
                fire['nearest_hospital_distance'] = nearest_hospital_distance

            # Sort the fires in descending order of prioritization score
            data['fires'] = sorted(data['fires'], key=lambda fire: fire['prioritization_score'], reverse=True)



             # Collect the IDs of the fires in their prioritized order
            fire_ids = [fire['id'] for fire in data['fires']]

            # Collect the IDs of the fires in their prioritized order and include injured people and distances
            fire_details = [
                {
                    "id": fire['id'],
                    "total_injured": fire['injured']['minor'] + fire['injured']['serious'],
                    "nearest_hospital_distance": fire['nearest_hospital_distance'],
                    "type": fire['type'],
                    "severity":fire['severity']
                    
                }
                for fire in data['fires']
            ]

            # Construct the output message
            result_message = (
                f"The tool has been successfully used to prioritize fires from the fire incident report. "
                f"Weights used: distance_weight={distance_weight}, severity_weight={severity_weight}, "
                f"type_weight={type_weight}, injured_weight={injured_weight}.\n"
                f"Order of priorization of fires by IDs: {fire_ids}."
                f"Prioritized fire details:\n"
            )

            for detail in fire_details:
                result_message += (
                    f"Fire ID: {detail['id']}, Injured: {detail['total_injured']}, Type: {detail['type']}, Severity: {detail['severity']}"
                    f" Distance to nearest hospital: {detail['nearest_hospital_distance']:.2f}\n"
                )

            result_message += f"Number of fires: {len(fire_details)}"

                        # Remove the 'prioritization_score' field after sorting (optional)
            for fire in data['fires']:
                del fire['prioritization_score']
                del fire['nearest_hospital_distance']

            # Write the sorted data to the output file
            with open("prioritized_fire_report.json", "w") as output_file:
                json.dump(data, output_file, indent=2)

            return result_message

        except Exception as e:
            return f"Failed to process the file. Error: {e}"
