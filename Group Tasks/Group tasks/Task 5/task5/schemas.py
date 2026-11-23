from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Query(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(default="default", min_length=1, max_length=128)


class ReportStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    font: Literal["sans", "serif", "mono"] = "sans"
    body_size: float = Field(default=10, ge=8, le=14)
    heading_size: float = Field(default=19, ge=14, le=28)
    color: str = Field(default="#174A75", pattern=r"^#[0-9a-fA-F]{6}$")
    page_size: Literal["A4", "Letter"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margin: float = Field(default=42, ge=28, le=72)
    spacing: float = Field(default=7, ge=3, le=16)
    line_height: float = Field(default=1.4, ge=1.15, le=1.8)
    emphasis: Literal["bold", "plain"] = "bold"


class ReportRequest(BaseModel):
    response_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    session_id: str = Field(default="default", min_length=1, max_length=128)
    title: str = Field(default="Document Intelligence Report", min_length=1, max_length=120)
    design_brief: str = Field(default="Professional blue report", max_length=1000)
    style: ReportStyle | None = None
