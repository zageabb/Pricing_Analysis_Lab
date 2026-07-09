from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pricing_analysis_lab.schemas import AnalysisPlan, AnalysisRequest
from pricing_analysis_lab.services.spreadsheet_loader import SpreadsheetData


@dataclass(slots=True)
class AnalysisContext:
    request: AnalysisRequest
    dataset: SpreadsheetData
    dataset_profile: dict[str, Any]


class AnalysisFunction(ABC):
    name: str
    description: str
    supported_tasks: tuple[str, ...]
    required_inputs: tuple[str, ...]
    output_schema: dict[str, Any]

    @abstractmethod
    def validate(self, context: AnalysisContext, plan: AnalysisPlan) -> None:
        raise NotImplementedError

    @abstractmethod
    def run(self, context: AnalysisContext, plan: AnalysisPlan) -> dict[str, Any]:
        raise NotImplementedError
