from pydantic import BaseModel, Field
from typing import Type, Any
from crewai_tools import BaseTool

import json

class FireSuppressionPlanSchema(BaseModel):
    severity_step_multiplier: int = Field(
        3, description="Multiplier to adjust the number of steps based on fire severity."
    )
    truck_efficiency_factor: int = Field(
        2, description="Factor to adjust steps based on the efficiency of allocated firetrucks."
    )

class FireSuppressionPlanTool(BaseTool):
    name: str = "Fire Suppression Plan Generator"
    description: str = (
        "Generates a detailed report for each fire incident, including the steps needed to suppress the fire. "
        "The steps depend on the fire's severity, type, and allocated firetrucks."
    )
    args_schema: Type[BaseModel] = FireSuppressionPlanSchema

    def _run(self, severity_step_multiplier=3, truck_efficiency_factor=2, **kwargs: Any) -> Any:
        try:
            # Load the fire report
            with open("fire_report_3.json", "r") as file:
                data = json.load(file)
            
            # Add suppression steps for each fire
            for fire in data['fires']:
                severity = fire['severity']  # Severity levels: low, medium, high
                fire_type = fire['type']  # Fire types: electrical, gas, ordinary
                allocated_trucks = fire.get('firetrucks', [])
                truck_count = len(allocated_trucks)
                
                # Determine steps based on fire type
                if fire_type == "electrical":
                    suppression_steps = [
                        "Cut off the power supply", 
                        "Use a Class C fire extinguisher",
                        "Monitor for potential re-ignition after cooling"
                    ]
                elif fire_type == "ordinary":
                    suppression_steps = suppression_steps = [
                        "Douse the fire with water to extinguish the flames",
                        "Use foam or wet chemical agents if needed for deeper penetration", 
                        "Inspect for remaining embers and ensure no hotspots are present"
                    ]
                elif fire_type == "gas":
                    suppression_steps = [
                        "Shut off the gas supply at the main valve",
                        "Use a dry chemical extinguisher designed for Class B or C fires",
                        "Ventilate the area to disperse any residual gas",
                        "Monitor for leaks or flare-ups after extinguishing"
                    ]
                else:
                    suppression_steps = [
                        "Use water or foam depending on the situation",
                        "Ensure thorough inspection post-extinguishing"
                    ]
                
                # Adjust steps based on severity and truck count
                if severity == "high":
                    suppression_steps += ["Monitor for re-ignition"] * severity_step_multiplier
                elif severity == "medium":
                    suppression_steps += ["Ensure thorough inspection"] * (severity_step_multiplier // 2)
                elif fire["severity"] == "low":
                    suppression_steps += ["Confirm fire is fully extinguished"] * (severity_step_multiplier // 3)

                # Efficiency boost based on truck count
                if truck_count > 0:
                    suppression_steps += ["Coordinate efforts among firetrucks"] * truck_efficiency_factor

                # Add suppression steps to the fire report
                fire['suppression_steps'] = suppression_steps

            # Save the updated fire report
            with open("fire_report_4.json", "w") as file:
                json.dump(data, file, indent=2)

            return "Fire suppression plans added successfully."

        except Exception as e:
            return f"Failed to generate fire suppression plans. Error: {e}"