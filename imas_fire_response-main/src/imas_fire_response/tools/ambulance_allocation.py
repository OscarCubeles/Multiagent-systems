import json
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any

# Define the schema for dynamic allocation parameters
class AmbulanceResourceAllocatorSchema(BaseModel):
    minor_injury_multiplier: float = Field(
        1.0, description="Multiplier for the number of ambulances allocated based on minor injuries."
    )
    serious_injury_multiplier: float = Field(
        2.0, description="Multiplier for the number of ambulances allocated based on serious injuries."
    )

class AmbulanceResourceAllocatorTool(BaseTool):
    name: str = "Ambulance Resource Allocator tool"
    description: str = (
        "Allocates ambulances to each fire based on the number of injuries and fire severity. "
        "Ensures that at least one ambulance is assigned to each fire, and remaining ambulances are allocated based on injuries."
    )
    args_schema: Type[BaseModel] = AmbulanceResourceAllocatorSchema

    def _run(self, minor_injury_multiplier=1.0, serious_injury_multiplier=2.0, **kwargs: Any) -> Any:
        try:
            # Load the medical report
            with open("medical_report.json", "r") as file:
                data = json.load(file)

            # Ensure at least one ambulance is assigned to each fire
            remaining_ambulances = [ambulance for ambulance in data['ambulances'] if ambulance['available']]
            for fire in data['fires']:
                if not remaining_ambulances:
                    break  # Stop if no ambulances are left

                # Assign one ambulance to the fire
                assigned_ambulance = remaining_ambulances.pop(0)
                assigned_ambulance['available'] = False

                # Initialize ambulances key for the fire
                fire["ambulances"] = []

                # Add the assigned ambulance to the fire
                fire["ambulances"].append(assigned_ambulance)

            # Calculate ambulance resource_necessity and sort fires
            for fire in data['fires']:
                injured = fire['injured']  # Dictionary of injury severities: minor, serious

                # Ambulance needs based on injury severity and multipliers
                minor_injuries = injured['minor']
                serious_injuries = injured['serious']

                # Calculate resource_necessity: weighted sum of injuries
                fire["resource_necessity"] = (minor_injuries * minor_injury_multiplier) + (serious_injuries * serious_injury_multiplier)

            # Sort fires by their resource_necessity (descending order)
            data['fires'] = sorted(data['fires'], key=lambda x: x['resource_necessity'], reverse=True)

            # Allocate remaining ambulances based on sorted resource_necessity
            for fire in data['fires']:
                injured = fire['injured']  # Dictionary of injury severities: minor, serious

                minor_injuries = injured['minor']
                serious_injuries = injured['serious']

                # Total injured in this fire
                total_injured = minor_injuries + serious_injuries

                # Total capacity of ambulances already assigned to this fire
                total_assigned_capacity = len(fire['ambulances'])

                # Total needed = total injured - total capacity already allocated
                total_needed = max(0, total_injured - total_assigned_capacity)

                # Allocate ambulances based on sorted resource_necessity
                if total_needed > 0:
                    remaining_ambulances = [ambulance for ambulance in remaining_ambulances if ambulance['available']]

                    for ambulance in remaining_ambulances[:total_needed]:
                        ambulance['available'] = False
                        fire["ambulances"].append(ambulance)

                    # Update the remaining ambulances after allocation
                    remaining_ambulances = [ambulance for ambulance in remaining_ambulances if ambulance['available']]

            # Save the updated data back to the file
            with open("medical_report_2.json", "w") as file:
                json.dump(data, file, indent=2)

            # Construct the result message to show the allocation details
            result_message = "Ambulance resource allocation completed successfully.\n"
            for fire in data["fires"]:
                total_injured = fire['injured']['minor'] + fire['injured']['serious']

                # Calculate the total capacity of assigned ambulances
                total_capacity = sum(ambulance['capacity'] for ambulance in fire['ambulances'])

                # Count ambulances by type
                transfer_count = sum(1 for ambulance in fire['ambulances'] if ambulance['type'] == 'transfer')
                on_site_count = sum(1 for ambulance in fire['ambulances'] if ambulance['type'] == 'on-site')

                result_message += (
                    f"Fire ID: {fire['id']}, Fire Severity: {fire['severity']}\n"
                    f"Total Injured people: {total_injured}, Minor: {fire['injured']['minor']}, Serious: {fire['injured']['serious']}\n"
                    f"Total Ambulances Assigned: {len(fire['ambulances'])}, Total Capacity: {total_capacity}\n"
                    f"Transfer Ambulances: {transfer_count}, On-site Ambulances: {on_site_count}\n\n"
                )


            return result_message

        except Exception as e:
            return f"Failed to allocate ambulance resources. Error: {e}"
