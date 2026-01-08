import pulp

def execute_resolucao_problema(titulo, numero_variaveis, funcao_objetivo, restricoes, execede_funcaoObjetivo = 0, tipo='max'):

    # Criação do modelo, dependendo se é para maximizar ou minimizar
    sentido = pulp.LpMaximize if tipo.lower() == 'max' else pulp.LpMinimize
    model = pulp.LpProblem(titulo, sense=sentido)

    # Adiciona as variáveis de decisão
    x = pulp.LpVariable.dict(indices=range(1, numero_variaveis + 1), cat=pulp.LpBinary, lowBound=0, name='x')

    # Adiciona as variáveis de folga conforme o número de restrições
    variaveis_folga_excesso = pulp.LpVariable.dict(indices=range(1, len(restricoes) + 1), cat=pulp.LpContinuous, lowBound=0, name='s')

    # Adiciona as restrições do problema
    for indice, (coef, operacao, resultado_equacao) in enumerate(restricoes, 1):
        restricao = pulp.lpSum(coef[j - 1] * x[j] for j in range(1, numero_variaveis + 1))

        if operacao == '<=':
            model.addConstraint(restricao + variaveis_folga_excesso[indice] == resultado_equacao, name=f"Restrição_{indice}")
        elif operacao == '>=':
            model.addConstraint(restricao - variaveis_folga_excesso[indice] == resultado_equacao, name=f"Restrição_{indice}")
        elif operacao == '=':
            model.addConstraint(restricao == resultado_equacao, name=f"Restrição_{indice}")
        else:
            raise ValueError(f"Operador inválido: {operacao}")

    # Função objetivo
    model.setObjective(pulp.lpSum(funcao_objetivo[j - 1] * x[j] for j in range(1, numero_variaveis + 1)) + execede_funcaoObjetivo)

    # Resolver o modelo
    model.solve()

    # Exibir resultado
    print(f"Resultado: {titulo}", pulp.LpStatus[model.status])
    for j in range(1, numero_variaveis + 1):
        val = x[j].value()
        print(f"x{j} = {val:.2f}" if val is not None else f"x{j} = 0.00")

    for i in range(1, len(restricoes) + 1):
        val = variaveis_folga_excesso[i].value()
        print(f"s{i} (folga/excesso) = {val:.2f}" if val is not None else f"s{i} (folga/excesso) = 0.00")

    print(f"Valor ótimo: {pulp.value(model.objective):.2f}")





