import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.termination import get_termination

class RotaProblem(Problem):
    """
    Classe que define o problema de otimização para escolher o melhor voo 
    baseado em um perfil de usuário. 

    Esta classe herda da classe Problem do PyMOO, que é utilizada
    para problemas de otimização multiobjetivo.

    Cada rota possui atributos fixos: tempo, preço e conexões. 
    O algoritmo irá escolher o índice da rota que minimiza o score calculado
    de acordo com o perfil do usuário (Mais rápido, Mais barato ou Equilibrado).
    """

    def __init__(self, tempos, precos, conexoes,
                 tempo_ideal, orcamento, perfil_cfg):
        """
        Inicializa o problema com os dados das rotas e perfil do usuário.

        Parâmetros:
        - tempos (list[float]): tempo total de cada rota
        - precos (list[float]): preço de cada rota
        - conexoes (list[int]): número de conexões de cada rota
        - tempo_ideal (float): tempo máximo desejado pelo usuário
        - orcamento (float): valor máximo desejado pelo usuário
        - perfil_cfg (dict): configuração do perfil com pesos
        """
        self.tempos = np.array(tempos, dtype=float)
        self.precos = np.array(precos, dtype=float)
        self.conexoes = np.array(conexoes, dtype=int)

        self.tempo_ideal = tempo_ideal
        self.orcamento = orcamento
        self.cfg = perfil_cfg

        # Chama o construtor da classe base Problem
        # n_var=1 → cada indivíduo representa o índice da rota
        # n_obj=1 → objetivo único: minimizar o score
        # n_constr=0 → não há restrições pesadas
        super().__init__(
            n_var=1,
            n_obj=1,
            n_constr=0,
            xl=0,
            xu=len(tempos) - 1,
            type_var=int
        )
    
    
    def calcular_score(self, tempo, preco, conexoes,
                   tempo_ideal, orcamento, cfg):
        """
        Calcula o score de uma rota com base no perfil do usuário.

        Quanto menor o score, melhor a rota para aquele perfil.

        Penalizações:
        - viol_tempo → quanto o tempo da rota ultrapassa o tempo ideal
        - viol_preco → quanto o preço da rota ultrapassa o orçamento
        - conexoes → penaliza o número de conexões de acordo com o peso do perfil

        Perfis:
        - base = "preco": foca em preço (Mais barato)
        - base = "tempo": foca em tempo (Mais rápido)
        - base equilibrado: combina todos os fatores e para fins acadêmicos, definimos 300 o valor hora.
        """

        viol_tempo = max(0, tempo - tempo_ideal)
        viol_preco = max(0, preco - orcamento)

        # ===================
        # PERFIL MAIS BARATO
        # ===================
        if cfg["base"] == "preco":
            score = (
                preco +
                preco * (viol_tempo / tempo_ideal) * cfg["peso_tempo"] +
                preco * (viol_preco / orcamento) * cfg["peso_preco"] +
                conexoes * cfg["peso_conexoes"]
            )

        # ===================
        # PERFIL MAIS RÁPIDO
        # ===================
        elif cfg["base"] == "tempo":
            score = (
                tempo +
                tempo * (viol_preco / orcamento) * cfg["peso_preco"] +
                conexoes * cfg["peso_conexoes"]
            )

        # ===================
        # PERFIL EQUILIBRADO
        # ===================
        else:
            custo_tempo = tempo * cfg["valor_hora"]

            score = (
                preco +
                custo_tempo +
                viol_tempo * cfg["valor_hora"] * cfg["peso_tempo"] +
                viol_preco * cfg["peso_preco"] +
                conexoes * cfg["peso_conexoes"]
            )

        return score


    def _evaluate(self, X, out, *args, **kwargs):
        """
        Método obrigatório do PyMOO.
        Recebe a população X (índices das rotas) e calcula o score para cada indivíduo.
        """
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

        # Define o array de objetivos para o PyMOO
        out["F"] = np.array(scores).reshape(-1, 1)


def executar_nsga2(rotas, tempo_ideal, orcamento, perfil):
    """
    Executa o algoritmo NSGA2 para encontrar a melhor rota
    entre as alternativas fornecidas.

    Parâmetros:
    - rotas (list[dict]): lista de rotas, cada uma com tempo, preco e conexoes
    - tempo_ideal (float): tempo máximo desejado
    - orcamento (float): valor máximo desejado
    - perfil (str): perfil do usuário ("Mais barato", "Mais rápido", "Equilibrado")

    Retorna:
    - res: objeto retornado pelo PyMOO contendo o melhor indivíduo e o Pareto
    """

    # Extrai listas de tempos, preços e conexões das rotas
    tempos = [r["tempo"] for r in rotas]
    precos = [r["preco"] for r in rotas]
    conexoes = [r["conexoes"] for r in rotas]

    # Configuração dos perfis
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
            "base": "equilibrado",
            "valor_hora": 300,          # R$/hora (ajustável)
            "peso_tempo": 1.0,
            "peso_preco": 1.0,
            "peso_conexoes": 10
        }
    }

    perfil_cfg = PERFIS.get(perfil, PERFIS["Equilibrado"])

    # Cria instância do problema
    problem = RotaProblem(
        tempos=tempos,
        precos=precos,
        conexoes=conexoes,
        tempo_ideal=tempo_ideal,
        orcamento=orcamento,
        perfil_cfg=perfil_cfg
    )

    # Configuração do algoritmo NSGA2
    algorithm = NSGA2(
        pop_size=min(80, len(rotas)),  # tamanho da população
        eliminate_duplicates=True      # evita soluções duplicadas
    )

    # Executa a otimização
    res = minimize(
        problem,
        algorithm,
        termination=get_termination("n_gen", 60),  # número de gerações
        seed=1,
        verbose=False
    )

    return res
