from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Alternativa:
    tempo: float
    preco: float
    conexoes: int
    saida: str
    chegada: str
    tempo_total: str
    roteiro: List[dict]
    preco_str: str


@dataclass
class ResultadoOtimizacao:
    rota_idx: int
    perfil: str
    alternativa_escolhida: Alternativa
    alternativas: List[Alternativa]
    pareto: list
    pareto_idx: list
    tempo_max: float
    orcamento: float


@dataclass
class ResultadoOtimizacao:
    rota_idx: int
    perfil: str
    alternativa_escolhida: Optional[object]
    alternativas: List[object]
    pareto: Optional[list]
    pareto_idx: Optional[list]
    tempo_max: float
    orcamento: float
    mensagem: Optional[str] = None   # 👈 NOVO