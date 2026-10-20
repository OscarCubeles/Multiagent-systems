from pydantic import BaseModel, Field
from typing import List

class FlowState(BaseModel):
    injured_people: int = 1
    text: str = ""
    injured_people: int = 1
    n_ambulances: int = 0
    n_fires: int = 2
    n_firetrucks: int = 1
    more_resources_needed: bool = False
    
    @classmethod
    def get_schema(cls) -> str:
        schema = '\n'
        for field_name, field_instance in cls.__fields__.items():
            schema += f'{field_name}, described as: {field_instance.description}\n'
        return schema
