from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from imas_fire_response.tools.report_creation import DataReaderTool

# Check our tools documentations for more information on how to use them
# from crewai_tools import SerperDevTool

llm = LLM(
	model='ollama/llama3.2'
)
    
def save_markdown(task_output):
    filename = 'Plan.md'
    with open(filename, 'w') as file:
        file.write(task_output.raw)
    print(f'Articles saved as {filename}')
    
   
@CrewBase
class ReportingCrew():
	"""ReportingCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def reporting_analyst(self) -> Agent:
		data_reader = DataReaderTool()
		return Agent(
			config=self.agents_config['reporting_analyst'],
			llm = llm,
			tools=[data_reader],
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
	def reporting_task(self) -> Task:
		return Task(
			config=self.tasks_config['reporting_task'],
			callback=save_markdown,
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the ReportingCrew crew"""
		return Crew(
			agents=self.agents, 
			tasks=self.tasks, 
			process=Process.sequential,
			verbose=True,
		)
