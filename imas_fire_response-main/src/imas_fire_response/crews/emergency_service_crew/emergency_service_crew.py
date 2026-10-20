from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List
from imas_fire_response.tools.fire_priorization import FirePriorizationTool
from imas_fire_response.tools.fire_segmentation import IncidentReportSegmentationTool

llm = LLM(
	model='ollama/llama3.2'
)

class ResourceAssessment(BaseModel):
    more_resources_needed: bool = Field(
        ..., description="A boolean indicating whether more resources are needed."
    )
    description: str = Field(
        ..., description="A detailed explanation of why more resources are or are not needed."
    )
    
    injured_people: int = Field(
		..., description="Integer indicating the number of injured people."
	)
    
    @classmethod
    def get_schema(cls) -> str:
        schema = '\n'
        for field_name, field_instance in cls.__fields__.items():
            schema += f'{field_name}, described as: {field_instance.description}\n'
        return schema

@CrewBase
class EmergencyServiceCrew():
	"""EmergencyServiceCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'
	

	@agent
	def emergency_call_coordinator(self) -> Agent:
		firesortingtool = FirePriorizationTool()
		return Agent(
			config=self.agents_config['emergency_call_coordinator'],
			llm=llm,
			tools=[firesortingtool], 
			verbose=True,
			max_iter=1,
			embedder={
        		"provider": "ollama",
        		"config": {
            		"model": "mxbai-embed-large"
        		}
			}
			
		)
	@task
	def prioritize_fires_task(self) -> Task:
		return Task(
			config=self.tasks_config['prioritize_fires_task'],
	)

	@agent
	def communicator_agent(self) -> Agent:
		report_segmentation_tool = IncidentReportSegmentationTool()
		return Agent(
			config=self.agents_config['communicator_agent'],
			verbose=True,
			tools=[report_segmentation_tool],
   			llm=llm,
      		max_iter=1,
			embedder={
        		"provider": "ollama",
        		"config": {
            		"model": "mxbai-embed-large"
        		}
			}
		)	
 
	@task
	def report_segmentation(self) -> Task:
		return Task(
			description=(
				"Use the 'Incident Report Segmentation' tool. "
				"Analyze the data returned by the tool to determine if more resources are needed based on "
				"the total number of fires, injured individuals, and available resources (ambulances and firetrucks). "
				"Your task is to provide a clear assessment of whether additional resources are required and explain the reasoning."
    			f"Make sure that the output matches the following structure: {ResourceAssessment.get_schema()}"
			),
			expected_output=(
				"A clear assessment indicating whether more resources are needed or not. "
				"The output must include a boolean value 'True' if more resources are needed, 'False' otherwise "
				"The integer number of injured people"
				"and a detailed explanation string of the reasoning behind the assessment with the number of fires, injured people, ambulances and firetrucks."
				
			),
			agent=self.communicator_agent(),
			output_pydantic=ResourceAssessment
		)

		
	@crew
	def crew(self) -> Crew:
		"""Creates the EmergencyServiceCrew crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)
