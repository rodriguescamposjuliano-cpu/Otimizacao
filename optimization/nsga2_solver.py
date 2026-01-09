import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.termination import get_termination


class RotaProblem(Problem):

    def __init__(self, tempos, precos, conexoes, tempo_max, orcamento):

        self.tempos = np.array(tempos, dtype=float)
        self.precos = np.array(precos, dtype=float)
        self.conexoes = np.array(conexoes, dtype=int)

        self.tempo_max = tempo_max
        self.orcamento = orcamento

        super().__init__(
            n_var=1,          # escolhe UMA rota (índice)
            n_obj=2,          # preço e conexões
            n_constr=2,       # tempo e orçamento
            xl=0,
            xu=len(tempos) - 1,
            type_var=int
        )

    def _evaluate(self, X, out, *args, **kwargs):
        idx = X.astype(int).flatten()

        tempo = self.tempos[idx]
        preco = self.precos[idx]
        conexoes = self.conexoes[idx]

        # Objetivos (minimizar)
        out["F"] = np.column_stack([
            preco,
            conexoes
        ])

        # Restrições (<= 0 é válido)
        g1 = tempo - self.tempo_max
        g2 = preco - self.orcamento

        out["G"] = np.column_stack([g1, g2])


def executar_nsga2(rotas, tempo_max, orcamento):

    tempos = [r["tempo"] for r in rotas]
    precos = [r["preco"] for r in rotas]
    conexoes = [r["conexoes"] for r in rotas]

    problem = RotaProblem(
        tempos=tempos,
        precos=precos,
        conexoes=conexoes,
        tempo_max=tempo_max,
        orcamento=orcamento
    )

    algorithm = NSGA2(
        pop_size=min(80, len(rotas)),
        eliminate_duplicates=True
    )

    res = minimize(
        problem,
        algorithm,
        termination=get_termination("n_gen", 80),
        seed=1,
        verbose=False
    )

    return res
