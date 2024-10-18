from pydantic import BaseModel, Field
from typing import Optional, List

class Moderations(BaseModel):
    hap_input: str = 'true'
    threshold: float = 0.75
    hap_output: str = 'true'

class Parameters(BaseModel):
    decoding_method: str = "greedy"
    min_new_tokens: int = 1
    max_new_tokens: int = 500
    repetition_penalty: float = 1.1
    temperature: float = 0.7
    top_k: int = 50
    top_p: int = 1
    stop_sequences: List[str] = Field(default=['sqlgen','unknown'], title="Stop Sequence", description="List for stop sequence to terminate the generation")
    moderations: Moderations = Moderations()

class LLMParams(BaseModel):
    model_id: str = "meta-llama/llama-3-70b-instruct"
    inputs: list = []
    parameters: Parameters = Parameters()

    class Config:
        protected_namespaces = ()

class classifyRequest(BaseModel):
    question: str = Field(title="NL Question", description="Question asked by the user.")
    classifyllm_params: Optional[LLMParams] = LLMParams()
