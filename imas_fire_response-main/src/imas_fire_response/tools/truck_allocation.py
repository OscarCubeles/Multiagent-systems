import json
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any

class FireResourceAllocatorSchema(BaseModel):
    high_severity_multiplier: float = Field(
        1.0, description="Multiplier for the number of firetrucks allocated based on high severity fires."
    )
    medium_severity_multiplier: float = Field(
        2.0, description="Multiplier for the number of firetrucks allocated based on medium severity fires."
    )
    low_severity_multiplier: float = Field(
        3.0, description="Multiplier for the number of firetrucks allocated based on low severity fires."
    )

class FireResourceAllocatorTool(BaseTool):
    name: str = "Fire Resource Allocator"
    description: str = (
        "Allocates fire trucks to each fire incident based on the type and severity of the fire. "
        "Ensures that the type of fire truck matches the fire type and at least one fire truck is allocated per fire."
    )
    args_schema: Type[BaseModel] = FireResourceAllocatorSchema

    def _run(self, high_severity_multiplier, medium_severity_multiplier, low_severity_multiplier, **kwargs: Any) -> Any:
        try:
            # Load the fire report
            with open("fire_report.json", "r") as file:
                data = json.load(file)

            # Filter fire trucks matching the fire type
            remaining_firetrucks = [truck for truck in data['firetrucks'] if truck['available']]
            fires_missing_firetrucks = []

            # Ensure at least one ambulance is assigned to each fire
            for i, fire in enumerate(data['fires']):
                if not remaining_firetrucks:
                    break  # Stop if no firetrucks are left
                # Initialize firetrucks key for the fire
                fire["firetrucks"] = []
                assigned = False
                # Assign one firetruck to the fire
                for truck in remaining_firetrucks:
                    if truck['type'] == fire['type']:
                        assigned_firetruck = truck
                        assigned = True                    
                
                if not assigned:
                    fires_missing_firetrucks.append(i)
                else:
                    # Add the assigned firetruck to the fire
                    fire["firetrucks"].append(assigned_firetruck)
                    assigned_firetruck['available'] = False

            for i in fires_missing_firetrucks:
                fire = data['fires'][i]
                remaining_firetrucks = [truck for truck in data['firetrucks'] if truck['available']]
                if not remaining_firetrucks:
                    break # Stop if no firetrucks are left
                assigned_firetruck = remaining_firetrucks[0]
                assigned_firetruck['available'] = False
                fire["firetrucks"].append(assigned_firetruck)

            # Update list of remaining firetrucks
            remaining_firetrucks = [truck for truck in remaining_firetrucks if truck['available']]

            # Mark as completed, low fires which have already assigned one firetruck
            for fire in data['fires']:
                if fire['severity'] == "low":
                    fire['completed'] = True

            # Calculate firetruck resource_necessity and sort fires
            for fire in data['fires']:
                severity = fire['severity']

                # Firetruck needs based on fire severity and multipliers
                if severity == "low":
                    low_severities = 1 
                    medium_severities = 0
                    high_severities = 0
                elif severity == "medium":
                    low_severities = 0
                    medium_severities = 1
                    high_severities = 0
                elif severity == "high":
                    low_severities = 0
                    medium_severities = 0
                    high_severities = 1
                else:
                    # Handle case where severity is not recognized
                    low_severities = 0
                    medium_severities = 0
                    high_severities = 0

                # Calculate resource_necessity: weighted sum of severities
                fire["resource_necessity"] = (low_severities * low_severity_multiplier) + (medium_severities * medium_severity_multiplier) + (high_severities * high_severity_multiplier)

             # Sort fires by their resource_necessity (descending order)
            data['fires'] = sorted(data['fires'], key=lambda x: x['resource_necessity'], reverse=True)

            incomplete_fires = [fire for fire in data['fires'] if not fire['completed']]
            # Allocate remaining firetrucks based on sorted resource_necessity
            i = 0
            while len(incomplete_fires) > 0:
                if not remaining_firetrucks:
                    break  # Stop if no firetrucks are left

                fire = incomplete_fires[i]
                severity = fire['severity']

                if severity == "low":
                    low_severities = 1
                    medium_severities = 0
                    high_severities = 0
                elif severity == "medium":
                    low_severities = 0
                    medium_severities = 1
                    high_severities = 0
                elif severity == "high":
                    low_severities = 0
                    medium_severities = 0
                    high_severities = 1
                else:
                    # Handle case where severity is not recognized
                    low_severities = 0
                    medium_severities = 0
                    high_severities = 0

                # Total firetrucks needed in this fire
                total_firetrucks_needed = low_severities * low_severity_multiplier + medium_severities * medium_severity_multiplier + high_severities * high_severity_multiplier

                # Total firetrucks already assigned to this fire
                total_firetrucks_assigned = len(fire['firetrucks'])

                # Total needed = total injured - total capacity already allocated
                total_needed = max(0, total_firetrucks_needed - total_firetrucks_assigned)

                type_available_firetrucks = [truck for truck in remaining_firetrucks if truck['type'] == fire['type']]
                other_available_firetrucks = [truck for truck in remaining_firetrucks if truck['type'] != fire['type']]
                # Allocate ambulances based on sorted resource_necessity
                if total_needed > 0 and len(type_available_firetrucks) > 0:
                    firetruck = type_available_firetrucks[0]
                    firetruck['available'] = False
                    fire["firetrucks"].append(firetruck)
                    if total_needed - 1 == 0:
                        fire['completed'] = True
                        i += 1

                elif total_needed > 0 and other_available_firetrucks:
                    firetruck = other_available_firetrucks[0]
                    firetruck['available'] = False
                    fire["firetrucks"].append(firetruck)
                    if total_needed - 1 == 0:
                        fire['completed'] = True
                        i += 1
                
                # Update the remaining firetrucks after allocation
                remaining_firetrucks = [truck for truck in remaining_firetrucks if truck['available']]
                
                if i >= len(incomplete_fires):  # Prevent out-of-range errors
                    break

            # Save the updated data
            with open("fire_report_2.json", "w") as file:
                json.dump(data, file, indent=2)

            # Construct the result message
            result_message = "Fire resource allocation completed successfully.\n"
            
            for fire in data["fires"]:
                total_firetrucks = fire['firetrucks']

                result_message += (
                    f"Fire ID: {fire['id']}, Fire Severity: {fire['severity']}\n"
                    f"Firetrucks Assigned: {total_firetrucks}\n"
                )

        except Exception as e:
            return f"Failed to allocate fire resources. Error: {e}"

