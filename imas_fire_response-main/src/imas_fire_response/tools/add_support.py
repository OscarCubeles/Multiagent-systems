import json
import random  
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any, List

class AddSupportToolInput(BaseModel):
    num_firetrucks_added: int = Field(..., description="Positive Integer Number of firetrucks to add.")
    type_firetrucks_added: List[str] = Field(..., description="Types of firetrucks to add. This should be ['ordinary', 'electrical', or 'gas'].")
    num_ambulances_added: int = Field(..., description="Positive Integer Number of ambulances to add.")

class AddSupportTool(BaseTool):
    name: str = "Add Support Tool"
    description: str = (
        "Adds more support resources by adding the specified number of ambulances and firetrucks. "
        "Ensures firetrucks and ambulances types are compatible with fire types. Reports mismatches between fire types and available firetrucks."
    )
    args_schema: Type[BaseModel] = AddSupportToolInput

    def _run(self, num_firetrucks_added: int = 0, type_firetrucks_added: List[str] = [], num_ambulances_added: int = 0, **kwargs: Any) -> Any:
        try:
            # Load the fire and medical report
            with open("fire_medical_report.json", "r") as file:
                data = json.load(file)

            # Get the location of the first hospital in the medical section
            hospital_location = data["medical_section"]["hospitals"][0]["location"]

            # Add the specified number of ambulances with random types to the medical section
            for i in range(num_ambulances_added):
                ambulance_type = random.choice(["on-site", "transfer"])
                data["medical_section"]["ambulances"].append({
                    "id": len(data["medical_section"]["ambulances"]) + 1,
                    "capacity": 3,
                    "location": hospital_location,
                    "type": ambulance_type,
                    "available": True
                })

            # Add the specified number of firetrucks with their types to the fire section
            for i in range(num_firetrucks_added):
                firetruck_type = type_firetrucks_added[i % len(type_firetrucks_added)]
                data["fire_section"]["firetrucks"].append({
                    "id": len(data["fire_section"]["firetrucks"]) + 1,
                    "type": firetruck_type,
                    "location": hospital_location,
                    "available": True
                })

            # Check for mismatches between fire types and firetrucks in the fire section
            fire_types = [fire["type"] for fire in data["fire_section"]["fires"]]
            firetruck_types = [truck["type"] for truck in data["fire_section"]["firetrucks"]]

            all_types = set(fire_types) | set(firetruck_types)  # Union of all fire and firetruck types

            type_summary = []
            for fire_type in all_types:
                fire_count = fire_types.count(fire_type)
                truck_count = firetruck_types.count(fire_type)
                type_summary.append(
                    f"For fires of type '{fire_type}': {fire_count} fires and {truck_count} firetrucks available."
                )

            # Calculate the total number of injured individuals from all fires in the medical section
            total_injured = sum(
                fire["injured"]["minor"] +
                fire["injured"]["serious"]
                for fire in data["medical_section"]["fires"]
            )

            # Get the total number of fires, ambulances, and firetrucks
            total_fires = len(data["fire_section"]["fires"])
            total_ambulances = len(data["medical_section"]["ambulances"])
            total_firetrucks = len(data["fire_section"]["firetrucks"])

            # Calculate ratios
            ambulances_per_fire = total_ambulances / total_fires if total_fires > 0 else 0
            ambulances_per_injured = total_ambulances / total_injured if total_injured > 0 else 0
            firetrucks_per_fire = total_firetrucks / total_fires if total_fires > 0 else 0

            # Save the updated report
            with open("fire_medical_report.json", "w") as file:
                json.dump(data, file, indent=2)

             # Write the fire section to a separate file
            with open("fire_report.json", "w") as fire_file:
                json.dump(data["fire_section"], fire_file, indent=2)

            # Write the medical section to a separate file
            with open("medical_report.json", "w") as medical_file:
                json.dump(data["medical_section"], medical_file, indent=2)

            # Return the outcome and summary
            result_message = (
                f"Support has been added successfully. {num_ambulances_added} ambulances and {num_firetrucks_added} firetrucks have been added.\n"
            )
            
            result_message += (
                f"There are {total_firetrucks} firetrucks to handle {total_fires} fires.\n"
            )
            
            result_message += (
                f"There are {total_ambulances} ambulances to handle {total_fires} fires.\n"
            )
            
            result_message += (
                f"There are {total_ambulances} ambulances to heal {total_injured} injured people.\n"
            )

            # Add the ratios
            result_message += (
                f"\nRatios:\n"
                f"There are {ambulances_per_fire:.2f} ambulances per fire. A good strictly ratio must be greater than 1, but not much grater. Can't be 0.\n"
                f"There are {ambulances_per_injured:.2f} ambulances per injured individual. A good ratio should be greater than 0.25 but not much grater.\n"
                f"There are {firetrucks_per_fire:.2f} firetrucks per fire. A good ratio strictly must be greater than 1, but not much grater. Can't be 0.\n"
            )
            


            type_summary_message = "\nType summary:\n" + "\n".join(type_summary)
            #result_message += type_summary_message

            return result_message

        except Exception as e:
            return f"Failed to modify the fire_medical_report.json file. Error: {e}"
