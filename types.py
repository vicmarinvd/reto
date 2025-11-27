"""
Definiciones de tipos de datos para la aplicación de análisis de riesgo de sucursales
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Sucursal:
    """Representa los datos de una sucursal"""
    id: str
    Sucursal: str
    Región: str
    Cluster_KM: str
    Nivel_Riesgo: str
    Score_Riesgo: float
    FPD_Neto_Actual: float
    ICV_Actual: float
    Tasa_Morosidad: float
    Capital_Dispersado_Actual: float
    Saldo_Insoluto_Total_Actual: float
    Saldo_Insoluto_Vencido_Actual: float
    Saldo_30_89_Actual: float
    Castigos_Actual: float
    Quitas_Actual: float
    lat: float
    lon: float


@dataclass
class BranchAnalysis:
    """Análisis generado por IA para una sucursal"""
    causes: List[str]
    suggestions: List[str]
    riskFactor: str


@dataclass
class ChatMessage:
    """Mensaje en el chat con DigiBot"""
    id: str
    role: str  # 'user' o 'model'
    text: str
    timestamp: datetime