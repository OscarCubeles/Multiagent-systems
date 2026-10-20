#!/usr/bin/env python
from random import randint
from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, start
from .flows.flows import FireFlow 
from imas_fire_response.fire_generator import generate_input_json

def kickoff():
    poem_flow = FireFlow()
    poem_flow.kickoff()
    
    

def plot():
    poem_flow = FireFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
