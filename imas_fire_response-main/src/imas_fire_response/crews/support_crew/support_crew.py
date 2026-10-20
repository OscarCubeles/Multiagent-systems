from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from imas_fire_response.tools.add_support import AddSupportTool

llm = LLM(
	model='ollama/llama3.2'
)


@CrewBase
class SupportCrew():
	"""SupportCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def support_agent(self) -> Agent:
		add_support_tool = AddSupportTool()
		return Agent(
			config=self.agents_config['support_agent'],
			tools=[add_support_tool], 
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
	def reporting_task(self) -> Task:
		return Task(
			config=self.tasks_config['support_task'],
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the SupportCrew crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)
