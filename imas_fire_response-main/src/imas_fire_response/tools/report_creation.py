import json
import os
from crewai_tools import BaseTool
from pydantic import BaseModel
from typing import Type, Any

class DataReaderInput(BaseModel):
    pass

class DataReaderTool(BaseTool):
    name: str = "Data reader tool"
    description: str = "Reads all the necessary data for the fire response simulation that will be used to generate the final report."
    args_schema: Type[BaseModel] = DataReaderInput

    def _run(self, **kwargs: Any) -> Any:
        try:
            # Load the fire medical report
            with open("fire_medical_report.json", "r") as file:
                fire_medical_report = json.load(file)

            # Initialize results
            results = "\n Initial Status \n"
            results += f"\n There are {len(fire_medical_report['fire_section']['fires'])} fires in the area. \n"
            for fire in fire_medical_report['fire_section']['fires']:
                results += f"Fire {fire['id']} is located at {fire['location']}. It is a/an {fire['type']} fire, and it is of {fire['severity']} severity, with {len(fire['injured'])} injured. \n"
                results += f"There are {fire['injured']['minor']} persons with minor injuries and {fire['injured']['serious']} with serious injuries. \n"

            results += f"\n There are {len(fire_medical_report['medical_section']['ambulances'])} ambulances available.\n"
            for ambulance in fire_medical_report['medical_section']['ambulances']:
                results += f"Ambulance {ambulance['id']} is a {ambulance['type']} ambulance and its available status is {ambulance['available']}. It has capacity for {ambulance['capacity']} people and is located in {ambulance['location']} \n"

            results += f"\n There are {len(fire_medical_report['fire_section']['firetrucks'])} available fire trucks. \n"
            for truck in fire_medical_report['fire_section']['firetrucks']:
                results += f"Truck {truck['id']} is a {truck['type']} fire truck and is located in {truck['location']} \n"

            results += f"\n There are {len(fire_medical_report['medical_section']['hospitals'])} hospitals. \n"
            for hospital in fire_medical_report['medical_section']['hospitals']:
                results += f"Hospital {hospital['id']}, {hospital['name']}, is located in {hospital['location']} and has capacity for {hospital['capacity']} people. \n"

            # Check for the medical report file
            results_medical = results
            if os.path.exists("medical_report_4.json"):
                with open("medical_report_4.json", "r") as file:
                    medical_report = json.load(file)

                results_medical += f"\n \n Medical Report \n"
                for fire in medical_report['fires']:
                    results_medical += f"\n In fire number {fire['id']}, {len(fire['ambulances'])} ambulances attend the site. \n"
                    for ambulance in fire['ambulances']:
                        results_medical += f"Ambulance number {ambulance['id']} travels a distance of {ambulance['route_to_fire']['distance']}m to reach the fire in {ambulance['route_to_fire']['route_time']} seconds. \n"
                        results_medical += f"It takes the following route: {ambulance['route_to_fire']['nodes']}. \n"
                        if ambulance['type'] == 'transfer':
                            results_medical += f"It is a {ambulance['type']} ambulance, and makes {len(ambulance['trips'])} trips. \n"
                            for number, trip in enumerate(ambulance['trips'], 1):
                                results_medical += f"On trip number {number} it transports {trip['serious_transported']} injured to hospital {trip['hospital_name']}. \n"
                                results_medical += f"The trip from the fire to the hospital takes {fire['route_fire_to_hospitals'][trip['hospital_id']-1]['route_time']} seconds with a traveled distance of {fire['route_fire_to_hospitals'][trip['hospital_id']-1]['distance']} meters. \n"
                                results_medical += f"The route is {fire['route_fire_to_hospitals'][trip['hospital_id']-1]['nodes']}. \n"
                                medical_report['hospitals'][trip['hospital_id']-1]['capacity'] -= trip['serious_transported']
                                results_medical += f"The hospital {trip['hospital_name']} now has a capacity of {medical_report['hospitals'][trip['hospital_id']-1]['capacity']} people. \n"
                        elif ambulance['type'] == 'on-site':
                            results_medical += f"It is an {ambulance['type']} ambulance, heals {ambulance['on_site_healing']} injured on the location of the fire. \n"
            else:
                results_medical += "\n No medical report file found.\n"

            # Check for the fire report file
            result_fires = results_medical
            if os.path.exists("fire_report_4.json"):
                with open("fire_report_4.json", "r") as file:
                    fire_report = json.load(file)

                result_fires += f"\n \n Fire Report \n"
                for fire in fire_report['fires']:
                    result_fires += f"\n To put out fire number {fire['id']} ({fire['type']}, {fire['severity']} severity), {len(fire['firetrucks'])} trucks attend the site.\n"
                    for truck in fire['firetrucks']:
                        result_fires += f"Fire truck number {truck['id']} reaches the site in {truck['route_to_fire']['route_time']} seconds, with a distance of {truck['route_to_fire']['distance']} meters. \n"
                        result_fires += f"It follows the next route to reach the fire: {truck['route_to_fire']['nodes']} \n"
                    result_fires += f"To put out the fire, several steps are taken: \n"
                    for step in fire['suppression_steps']:
                        result_fires += f"- {step} \n"
            else:
                result_fires += "\n No fire report file found.\n"

            # Write the final report to a file
            with open("report.txt", "w") as output_file:
                output_file.write(result_fires)

            # Return the report content
            return {"Report": result_fires}

        except Exception as e:
            return f"Error while reading data: {e}"


