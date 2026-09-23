from typing import Literal

from pydantic import BaseModel, Field


class RewardInput(BaseModel):
    name: str
    price: float = Field(gt=0)
    unit_cost: float = Field(ge=0)
    shipping_cost: float = Field(ge=0)
    platform_fee_rate: float = Field(default=0.08, ge=0, lt=1)


class ResearchRequest(BaseModel):
    project_name: str = "便携式户外电源"
    target_market: str = "US / CA"
    platform: Literal["Kickstarter", "Indiegogo"] = "Kickstarter"
    evidence_count: int = Field(default=18, ge=0)
    rewards: list[RewardInput]


class AdMetric(BaseModel):
    ad_group: str
    spend: float = Field(ge=0)
    clicks: int = Field(ge=0)
    backers: int = Field(ge=0)
    revenue: float = Field(ge=0)
    previous_cpc: float = Field(gt=0)


class GrowthRequest(BaseModel):
    project_name: str = "便携式户外电源"
    metrics: list[AdMetric]


class BackerRequest(BaseModel):
    project_name: str = "便携式户外电源"
    messages: list[str] = Field(min_length=1)


class ApprovalRequest(BaseModel):
    approved_by: str = Field(min_length=1, max_length=100)


class EnrichmentRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    deterministic_result: str = Field(min_length=1, max_length=8000)


class AgentRunResponse(BaseModel):
    run_id: int
    agent_type: str
    status: str
    output: dict
