import numpy as np
from optimization.nsga2_solver import executar_nsga2
from domain.models import ResultadoOtimizacao

class OptimizationService:

    @staticmethod
    def otimizar(alternativas, perfil, tempo_max, orcamento, rota_idx):

        res = executar_nsga2(
            [a.__dict__ for a in alternativas],
            tempo_ideal=tempo_max,
            orcamento=orcamento,
            perfil=perfil
        )


        if res.X is None or len(res.F) == 0:
            return None

        F = res.F
        X = np.asarray(res.X, dtype=int).ravel()

        F_unique, idx_unique = np.unique(F, axis=0, return_index=True)
        X_unique = X[idx_unique]

        if perfil == "Mais barato":
            idx_sol = np.argmin(F_unique[:, 0])

        elif perfil == "Mais rápido":
            tempos = [alternativas[i].tempo for i in X_unique]
            idx_sol = np.argmin(tempos)

        else:
            F_norm = (F_unique - F_unique.min(axis=0)) / (np.ptp(F_unique, axis=0) + 1e-9)
            idx_sol = np.argmin(F_norm.sum(axis=1))

        escolhida = alternativas[X_unique[idx_sol]]


        return ResultadoOtimizacao(
            rota_idx=rota_idx,
            perfil=perfil,
            alternativa_escolhida=escolhida,
            alternativas=alternativas,
            pareto=F_unique,
            pareto_idx=X_unique.tolist(),
            tempo_max=tempo_max,
            orcamento=orcamento
        )
    
    
    @staticmethod
    def resultado_sem_alternativas(rota_idx, perfil, tempo_max, orcamento):
        return ResultadoOtimizacao(
            rota_idx=rota_idx,
            perfil=perfil,
            alternativa_escolhida=None,
            alternativas=[],
            pareto=None,
            pareto_idx=None,
            tempo_max=tempo_max,
            orcamento=orcamento,
            mensagem=":warning: Nenhuma alternativa encontrada para esta rota. Verifique a data de partida informada."
        )