from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from imas_fire_response.tools.fire_supression import FireSuppressionPlanTool
from imas_fire_response.tools.firetruck_routing import FireRouting
from imas_fire_response.tools.truck_allocation import FireResourceAllocatorTool


# Check our tools documentations for more information on how to use them
# from crewai_tools import SerperDevTool

llm = LLM(
	model='ollama/llama3.2'
)

@CrewBase
class FireCrew():
	"""FireCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def firefighter_coordinator(self) -> Agent:
		return Agent(
			config=self.agents_config['firefighter_coordinator'],
			tools=[FireResourceAllocatorTool()], 
			verbose=True,
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
	def fire_resources_task(self) -> Task:
		return Task(
			description=("Utilize the Fire Resource Allocator tool to generate a text regarding the allocation of firetrucks. "
			"The tool output will include the summary of the allocation of firetrucks in fires."),
			expected_output=(
				"A paragraph explaining the parameters used in the Fire Resource Allocator tool,"
				"how they impacted the allocation process and the information about fires and firetrucks allocation."
			),
			agent= self.firefighter_coordinator()
		)
	
	@agent
	def firetruck_dispatcher(self) -> Agent:
		return Agent(
			config=self.agents_config['firetruck_dispatcher'],
			tools=[FireRouting()], 
			verbose=True,
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
	def fire_truck_routing_task(self) -> Task:
		return Task(
			description=(
				"Utilize the Firetucks Route Calculator Tool to calculate the shortest routes for fire trucks. "
				"The tool will determine the quickest paths from the fire station to the fire locations, ensuring timely arrival."
			),
			expected_output=(
				"A detailed routing plan for each fire truck, including the calculated shortest paths from the fire station to the assigned fire locations."
			),
			agent=self.firetruck_dispatcher()
		)
	
	@agent
	def firefighter_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['firefighter_agent'],
			tools=[FireSuppressionPlanTool()], 
			verbose=True,
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
	def fire_extinguishing_strategy_task(self) -> Task:
		return Task(
			description=(
				"Analyze the fire report and create a step-by-step action plan for extinguishing each fire by using the Fire Suppression Plan Generator. "
				"The plan should consider the type and severity of the fire."
			),
			expected_output=(
				"A comprehensive action plan for each fire, detailing the steps to extinguish it effectively, considering the fire type, severity, "
				"and potential complications such as electrical or chemical fires."
			),
			agent=self.firefighter_agent()
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the FireCrew crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
