import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.termination import get_termination

class RotaProblem(Problem):

    def __init__(self, tempos, precos, conexoes,
                 tempo_ideal, orcamento, perfil_cfg):

        self.tempos = np.array(tempos, dtype=float)
        self.precos = np.array(precos, dtype=float)
        self.conexoes = np.array(conexoes, dtype=int)

        self.tempo_ideal = tempo_ideal
        self.orcamento = orcamento
        self.cfg = perfil_cfg

        super().__init__(
            n_var=1,
            n_obj=1,      # 🔑 UM objetivo (score)
            n_constr=0,   # 🔑 sem restrições duras
            xl=0,
            xu=len(tempos) - 1,
            type_var=int
        )

    def calcular_score(self, tempo, preco, conexoes,
                   tempo_ideal, orcamento, cfg):

        viol_tempo = max(0, (tempo - tempo_ideal) / tempo_ideal)
        viol_preco = max(0, (preco - orcamento) / orcamento)

        # =========================
        # PERFIL MAIS BARATO
        # =========================
        if cfg["base"] == "preco":
            score = (
                preco +
                preco * viol_tempo * cfg["peso_tempo"] +
                preco * viol_preco * cfg["peso_preco"] +
                conexoes * cfg["peso_conexoes"]
            )

        # =========================
        # PERFIL MAIS RÁPIDO
        # =========================
        else:  # base == "tempo"
            score = (
                tempo +
                tempo * viol_preco * cfg["peso_preco"] +
                conexoes * cfg["peso_conexoes"]
            )

        return score
    
    def _evaluate(self, X, out, *args, **kwargs):
        idx = X.astype(int).flatten()

        scores = []
        for i in idx:
            score = self.calcular_score(
                tempo=self.tempos[i],
                preco=self.precos[i],
                conexoes=self.conexoes[i],
                tempo_ideal=self.tempo_ideal,
                orcamento=self.orcamento,
                cfg=self.cfg
            )
            scores.append(score)

        out["F"] = np.array(scores).reshape(-1, 1)


    


def executar_nsga2(rotas, tempo_ideal, orcamento, perfil):

    tempos = [r["tempo"] for r in rotas]
    precos = [r["preco"] for r in rotas]
    conexoes = [r["conexoes"] for r in rotas]


    PERFIS = {
        "Mais barato": {
            "base": "preco",
            "peso_tempo": 0.5,
            "peso_preco": 1.0,
            "peso_conexoes": 100
        },
        "Mais rápido": {
            "base": "tempo",
            "peso_tempo": 1.0,
            "peso_preco": 0.5,
            "peso_conexoes": 2
        },
        "Equilibrado": {
            "base": "preco",
            "peso_tempo": 0.8,
            "peso_preco": 0.8,
            "peso_conexoes": 10
        }
    }

    perfil_cfg = PERFIS.get(perfil, PERFIS["Equilibrado"])

    problem = RotaProblem(
        tempos=tempos,
        precos=precos,
        conexoes=conexoes,
        tempo_ideal=tempo_ideal,
        orcamento=orcamento,
        perfil_cfg=perfil_cfg
    )

    algorithm = NSGA2(
        pop_size=min(80, len(rotas)),
        eliminate_duplicates=True
    )

    res = minimize(
        problem,
        algorithm,
        termination=get_termination("n_gen", 60),
        seed=1,
        verbose=False
    )

    return res
