# IMAS Fire Response Multi Agent System

## Team 09
- Elena Blanco Lopez
- Clàudia Boixader Garcia
- Óscar Cubeles Ollé
- Aina Llaneras

## Requirements

- Ollama 3.2
- Git
- Anaconda


# Set Up Environment

To set up the environment for our script, follow these steps:

```plaintext
#1. Create a new Conda environment with Python 3.12 and activate it:
   conda create -n mas python=3.12
   conda activate mas
```

```plaintext
#2. Install the required Python packages:
   pip install crewai[tools]==0.79.4
   pip install ollama duckduckgo-search transformers torch
   pip install poetry
   conda install -c conda-forge osmnx
```
```plaintext
#3. Change to the project directory (same as where the `pyproject.toml` file is located):
   cd /path/to/IMAS/project
```
```plaintext
#4. Install CrewAI dependencies and start the flow:
   crewai install
   crewai flow kickoff
```

# Overview  

This MAS code is designed to coordinate emergency responses efficiently in the city of Olot. It consists of five specialized crews working collaboratively:  

1. **Emergency Services Crew**  
2. **Medical Crew**  
3. **Support Crew**  
4. **Fire Crew**  
5. **Reporting Crew**  

# Code Structure  

The project is organized into the following main directories and files:  

## 1. **Crews**  
- **Folder:** `crews/`  
- Each crew has its own folder containing:  
  - **Configuration files**: Defines crew-specific settings.  
  - **Python scripts**: Implements the crewAI and behavior logic.  

## 2. **Flows**  
- **Folder:** `flows/`  
- Contains `flow.py`, which orchestrates the interactions between the crews and defines the overall system workflow.  

## 3. **Custom Tools**  
- **Folder:** `custom_tools/`  
- Contains one file per custom tool, defining the tools used by the agents for specialized tasks.  

## 4. **Schemas**  
- **Folder:** `schemas/`  
- Contains one file per schema, defining data formats.  

### 5. **Other Files**  
- **`input.json`**: Describes the details of the fire scenario.  
- **Intermediate reports**: Generated  by agents during the flow.  
- **`fire_generator.py`**: A script to simulate random fire scenarios in Olot and output them in the `input.json` format.  
- **`report.txt`**: Final report made by the DataReaderTool used by the reporting crew to generate the final plan. Contains all the information.
- **`plan.md`**: Final Response plan made by the Reporting Crew. May not contain all the information from the report.txt.
  

## How It Works  

1. **Input**  
   - The system starts with `input.json`, containing fire details for a specific scenario.  
   - Alternatively, `fire_generator.py` can be used to generate a random fire scenario.  

2. **Flow**  
   - `flow.py` coordinates the actions of the five crews based on the input data.  
   - Each crew uses its configuration and custom tools to perform specialized tasks.  

3. **Intermediary Reports**  
   - Throughout the workflow, agents generate intermediate JSON and Txt reports that summarize their findings or actions.  
   - These reports are stored for reference of further agents/crews.  

4. **Final Plan Generation**  
   - The final plan will be the `plan.md` which contains the well-written information from the `report.txt` made by the reporting crew.




