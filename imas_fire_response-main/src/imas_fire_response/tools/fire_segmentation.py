import json
from crewai_tools import BaseTool
from pydantic import BaseModel
from typing import Type, Any


class IncidentReportSegmentationInput(BaseModel):
    pass

class IncidentReportSegmentationTool(BaseTool):
    name: str = "Incident Report Segmentation"
    description: str = "Generates segmented fire report, containing fire and medical sections. Also returns the number of fires, injured people, ambulances and medical people. This tool does not require any input"
    args_schema: Type[BaseModel] = IncidentReportSegmentationInput

    def _run(self, **kwargs: Any) -> Any:
        try:
            # Load the prioritized fire report
            with open("prioritized_fire_report.json", "r") as file:
                data = json.load(file)

            # Calculate total number of fires
            total_fires = len(data["fires"])

            # Calculate total number of injured people across all fires
            total_injured = sum(
                fire["injured"]["minor"] +
                fire["injured"]["serious"]
                for fire in data["fires"]
            )

            # Count the number of ambulances and firetrucks
            num_ambulances = len(data["ambulances"])
            num_firetrucks = len(data["firetrucks"])

            # Create the fire_medical_report structure
            fire_medical_report = {
                "fire_section": {
                    "fires": data["fires"],
                    "firetrucks": data["firetrucks"]
                },
                "medical_section": {
                    "fires": data["fires"],
                    "ambulances": data["ambulances"],
                    "hospitals": data["hospitals"]
                }
            }

            # Write the fire_medical_report to the output file
            with open("fire_medical_report.json", "w") as output_file:
                json.dump(fire_medical_report, output_file, indent=2)

            # Write the fire section to a separate file
            with open("fire_report.json", "w") as fire_file:
                json.dump(fire_medical_report["fire_section"], fire_file, indent=2)

            # Write the medical section to a separate file
            with open("medical_report.json", "w") as medical_file:
                json.dump(fire_medical_report["medical_section"], medical_file, indent=2)

            ratio_ambulances =  num_ambulances / total_fires
            ratio_firetrucks = num_firetrucks / total_fires
            
            # Return summary statistics
            return (
                f"There are a total number of fires of: {total_fires}. \n"
                f"Total injured people across all fires: {total_injured}. \n"
                f"Number of ambulances: {num_ambulances}. \n"
                f"Number of firetrucks: {num_firetrucks}. \n"
                f"The ratio of firetrucks per fire without considering types is {ratio_firetrucks}\n"
                f"The ratio of ambulances per fire is {ratio_ambulances}\n"
            )
        except Exception as e:
            return f"Failed to generate the fire_medical_report. Error: {e}"
