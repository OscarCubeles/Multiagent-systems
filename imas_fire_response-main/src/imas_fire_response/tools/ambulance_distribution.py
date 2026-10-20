from pydantic import BaseModel, Field
from typing import Type, Any
from crewai_tools import BaseTool

import json

class CasualtyDistributionSchema(BaseModel):
    weight_distance: float = Field(
        0.5, description="Float importance weight assigned to the distance between the fire location and the nearest hospital. Higher values mean more importance."
    )
    weight_time: float = Field(
        0.5, description="Float importance weight assigned to the time taken for ambulances to reach hospitals. Higher values mean more importance."
    )

class AmbulanceDistributionTool(BaseTool):
    name: str = "Ambulance Distribution Tool"
    description: str = "Distributes casualties to the nearest hospitals based on distance and time, considering ambulance capacities and available hospitals."
    args_schema: Type[BaseModel] = CasualtyDistributionSchema

    def _run(self, weight_distance=0.5, weight_time=0.5, **kwargs: Any) -> Any:
        with open("medical_report_3.json", "r") as file:
            data = json.load(file)

        total_distance = 0
        total_trips = 0
        total_time = 0
        total_on_site_healing = 0
        result_msg = ""

        # Track hospital capacities across all fires
        hospital_capacities = {hospital["id"]: hospital["capacity"] for hospital in data["hospitals"]}

        for fire in data["fires"]:
            fire_result = {
                "fire_id": fire["id"],
                "location": fire["location"],
                "ambulance_details": [],
                "serious_injuries_remaining": 0,
                "minor_injuries_remaining": 0
            }

            serious = fire["injured"]["serious"]
            minor = fire["injured"]["minor"]

            transfer_ambulances = [amb for amb in fire["ambulances"] if amb["type"] == "transfer"]
            on_site_ambulances = [amb for amb in fire["ambulances"] if amb["type"] == "on-site"]

            fire_hospital_capacities = {hospital_id: {"initial": capacity, "final": capacity}
                                        for hospital_id, capacity in hospital_capacities.items()}

            # Assign serious casualties to transfer ambulances
            for ambulance in transfer_ambulances:
                ambulance["trips"] = []
                ambulance["on_site_healing"] = 0
                while serious > 0:
                    best_hospital = None
                    best_score = float("inf")
                    for hospital in data["hospitals"]:
                        hospital_id = hospital["id"]
                        if hospital_capacities[hospital_id] > 0:
                            hospital_distance = next(
                                (route["distance"] for route in fire["route_fire_to_hospitals"] if route["hospital_id"] == hospital_id),
                                float("inf")
                            )
                            hospital_time = next(
                                (route["route_time"] for route in fire["route_fire_to_hospitals"] if route["hospital_id"] == hospital_id),
                                float("inf")
                            )
                            score = weight_distance * hospital_distance + weight_time * hospital_time
                            if score < best_score:
                                best_hospital = hospital
                                best_score = score

                    if not best_hospital or serious <= 0:
                        break

                    trip_capacity = min(ambulance["capacity"], serious, hospital_capacities[best_hospital["id"]])
                    hospital_capacities[best_hospital["id"]] -= trip_capacity
                    fire_hospital_capacities[best_hospital["id"]]["final"] -= trip_capacity
                    serious -= trip_capacity

                    ambulance["trips"].append({
                        "hospital_id": best_hospital["id"],
                        "hospital_name": best_hospital["name"],
                        "serious_transported": trip_capacity,
                    })
                    total_trips += 1
                    total_distance += next(route["distance"] for route in fire["route_fire_to_hospitals"] if route["hospital_id"] == best_hospital["id"])
                    total_time += next(route["route_time"] for route in fire["route_fire_to_hospitals"] if route["hospital_id"] == best_hospital["id"])

                fire_result["ambulance_details"].append({
                    "ambulance_id": ambulance["id"],
                    "type": ambulance["type"],
                    "trips": ambulance["trips"],
                    "on_site_healing": ambulance["on_site_healing"]
                })

            # Treat or transport minor casualties
            for ambulance in on_site_ambulances:
                ambulance["trips"] = []
                ambulance["on_site_healing"] = 0

                healable = min(ambulance["capacity"], minor)
                ambulance["on_site_healing"] += healable
                minor -= healable
                total_on_site_healing += healable

                while minor > 0:
                    best_hospital = None
                    best_score = float("inf")
                    for hospital in data["hospitals"]:
                        hospital_id = hospital["id"]
                        if hospital_capacities[hospital_id] > 0:
                            hospital_distance = next(
                                (route["distance"] for route in fire["route_fire_to_hospitals"] if route["hospital_id"] == hospital_id),
                                float("inf")
                            )
                            hospital_time = next(
                                (route["route_time"] for route in fire["route_fire_to_hospitals"] if route["hospital_id"] == hospital_id),
                                float("inf")
                            )
                            score = weight_distance * hospital_distance + weight_time * hospital_time
                            if score < best_score:
                                best_hospital = hospital
                                best_score = score

                    if not best_hospital or minor <= 0:
                        break

                    trip_capacity = min(ambulance["capacity"], minor, hospital_capacities[best_hospital["id"]])
                    hospital_capacities[best_hospital["id"]] -= trip_capacity
                    fire_hospital_capacities[best_hospital["id"]]["final"] -= trip_capacity
                    minor -= trip_capacity

                    ambulance["trips"].append({
                        "hospital_id": best_hospital["id"],
                        "hospital_name": best_hospital["name"],
                        "minor_transported": trip_capacity,
                    })
                    total_trips += 1
                    total_distance += next(route["distance"] for route in fire["route_fire_to_hospitals"] if route["hospital_id"] == best_hospital["id"])
                    total_time += next(route["route_time"] for route in fire["route_fire_to_hospitals"] if route["hospital_id"] == best_hospital["id"])

                fire_result["ambulance_details"].append({
                    "ambulance_id": ambulance["id"],
                    "type": ambulance["type"],
                    "trips": ambulance["trips"],
                    "on_site_healing": ambulance["on_site_healing"]
                })

            fire_result["serious_injuries_remaining"] = serious
            fire_result["minor_injuries_remaining"] = minor

            fire_healing_time = 0
            for ambulance in transfer_ambulances:
                for trip in ambulance["trips"]:
                    hospital_time = next(
                        route["route_time"] for route in fire["route_fire_to_hospitals"] if route["hospital_id"] == trip["hospital_id"]
                    )
                    fire_healing_time += hospital_time

            for ambulance in on_site_ambulances:
                if ambulance["on_site_healing"] > 0:
                    on_site_time = max(1, (ambulance["on_site_healing"] / ambulance["capacity"]) * 3600)
                    fire_healing_time += on_site_time

            result_msg += f"\nFire ID: {fire['id']} (Location: {fire['location']['x']}, {fire['location']['y']})\n"
            result_msg += f"  Injured at fire site:\n"
            result_msg += f"    Serious: {fire['injured']['serious']}\n"
            result_msg += f"    Minor: {fire['injured']['minor']}\n"
            for ambulance_detail in fire_result["ambulance_details"]:
                result_msg += f"  Ambulance ID: {ambulance_detail['ambulance_id']}, Type: {ambulance_detail['type']}\n"
                result_msg += f"    Trips: {ambulance_detail['trips']}\n"
                result_msg += f"    On-Site Healing: {ambulance_detail['on_site_healing']}\n"
            result_msg += f"  Serious Injuries Remaining: {fire_result['serious_injuries_remaining']}\n"
            result_msg += f"  Minor Injuries Remaining: {fire_result['minor_injuries_remaining']}\n"

            result_msg += f"  Hospital Capacities:\n"
            for hospital_id, capacities in fire_hospital_capacities.items():
                result_msg += f"    Hospital ID: {hospital_id}, Initial Capacity: {capacities['initial']}, Final Capacity: {capacities['final']}\n"

            result_msg += f"  Approximate Healing Time: {(fire_healing_time / 60):.2f} minutes\n\n"

        with open("medical_report_4.json", "w") as output_file:
            json.dump(data, output_file, indent=4)

        result_msg += f"Total Distance: {total_distance:.2f} m\n"
        result_msg += f"Total Trips: {total_trips}\n"
        result_msg += f"Total Time: {(total_time / 60):.2f} minutes\n"
        result_msg += f"Total On-Site Healing: {total_on_site_healing}\n"

        with open("medical_distribution.txt", "w") as output_file:
            output_file.write(result_msg)
        
        return result_msg
