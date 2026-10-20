from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from imas_fire_response.tools.ambulance_allocation import AmbulanceResourceAllocatorTool
from imas_fire_response.tools.ambulance_routing import MedicalRouting
from imas_fire_response.tools.ambulance_distribution import AmbulanceDistributionTool

# Check our tools documentations for more information on how to use them
# from crewai_tools import SerperDevTool

llm = LLM(
	model='ollama/llama3.2'
)


@CrewBase
class MedicalCrew():
	"""MedicalCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'
	
	@agent
	def medical_service_coordinator(self) -> Agent:
		return Agent(
			config=self.agents_config['medical_service_coordinator'],
			tools=[AmbulanceResourceAllocatorTool()], 
			verbose=True,
   			llm=llm
		)
	
	@task
	def resource_distribution_task(self) -> Task:
		return Task(
			description=("Utilize the Ambulance Resource Allocator tool to generate a text regarding the allocation of ambulances. "
    		"The tool output will include the summary of the allocation of ambulances in fires."),
			expected_output=(
				"A paragraph explaining the parameters used in the Ambulance Resource Allocator tool,"
    			"how they impacted the allocation process and the information about fires and injured allocation."
			),
			agent= self.medical_service_coordinator()
		)
 	
	@agent 
	def ambulance_dispatcher(self) -> Agent:
		distance_tool = MedicalRouting()
		return Agent(
			config=self.agents_config['ambulance_dispatcher'],
			tools=[distance_tool],
   			llm=llm,
			verbose=True
		)

	@task
	def ambulances_routing_task(self) -> Task:
		return Task(
			config=self.tasks_config['ambulances_routing_task'],
		)
 	
	@agent
	def ambulance_causality_distributor(self) -> Agent:
		ambulance_distribution_tool = AmbulanceDistributionTool()
		return Agent(
			config=self.agents_config['ambulance_causality_distributor'],
			tools = [ambulance_distribution_tool],
			llm=llm,
			verbose=True
		)
  
	@task
	def ambulance_causality_distribution(self) -> Task:
		return Task(
			config=self.tasks_config['ambulance_causality_distribution']
		)
  
	@crew
	def crew(self) -> Crew:
		"""Creates the MedicalCrew crew"""
		return Crew(
			agents=[self.medical_service_coordinator(), self.ambulance_dispatcher(),  self.ambulance_causality_distributor()],
			tasks=[self.resource_distribution_task(), self.ambulances_routing_task() ,self.ambulance_causality_distribution()], 
			process=Process.sequential,
			verbose=True,
		)
