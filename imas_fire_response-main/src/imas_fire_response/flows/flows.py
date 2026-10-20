from typing import List
from crewai.flow.flow import Flow, listen, start, router, or_
from imas_fire_response.schemas.schemas import FlowState
from imas_fire_response.crews.emergency_service_crew.emergency_service_crew import EmergencyServiceCrew
from imas_fire_response.crews.medical_crew.medical_crew import MedicalCrew
from imas_fire_response.crews.fire_crew.fire_crew import FireCrew
from imas_fire_response.crews.support_crew.support_crew import SupportCrew
from imas_fire_response.crews.reporting_crew.reporting_crew import ReportingCrew

class FireFlow(Flow[FlowState]):
    @start()
    def start_fire(self):
        #generate_input_json()
        print("Input fire generated")


    @listen(start_fire)
    def kickoff_emergency_services(self):
        result = None
        result = EmergencyServiceCrew().crew().kickoff()
        try:
            print(f"More resources needed: {result.tasks_output[1].pydantic.more_resources_needed}")
            self.state.more_resources_needed = result.tasks_output[1].pydantic.more_resources_needed
            self.state.injured_people = result.tasks_output[1].pydantic.injured_people
        except Exception as e:
           # Assume that if not defined by the agent, more resources are needed 
           # and at least there is an injured person to activate the med crew just in case
           self.state.more_resources_needed = True
           self.state.injured_people = 1
        

    @router(kickoff_emergency_services)
    def check_resources(self):
        if self.state.more_resources_needed:
            return "support"
        else:
            return "update_rsc"
        
    @listen("support")
    def support_add_resources(self):
        print("kickoff support to add resources")
        SupportCrew().crew().kickoff()
    
    @listen(or_("update_rsc",support_add_resources))
    def update_resources(self):
        print("update rsc")


    @router(update_resources)
    def check_injured_people(self):
        if self.state.injured_people > 0:
            return "kickoff_medical"
        
        return "kickoff_fire_crews"

    @listen("kickoff_medical")
    def kickoff_medical_crew(self):
        print("Kickoff medical crew")
        MedicalCrew().crew().kickoff()

        return "kickoff_fire_crews"
    
        

    @listen(or_("kickoff_fire_crews", kickoff_medical_crew))
    def kickoff_fire_crew(self):
        print("Kickoff fire crew")
        FireCrew().crew().kickoff()



    @listen(kickoff_medical_crew)
    def reporting_crew_generate_plan(self):
        ReportingCrew().crew().kickoff()
        print("reporting crew write")


