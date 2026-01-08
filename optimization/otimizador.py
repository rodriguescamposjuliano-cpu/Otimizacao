import pulp

def execute_resolucao_problema(
    titulo,
    numero_variaveis,
    funcao_objetivo,
    restricoes,
    execede_funcaoObjetivo=0,
    tipo='max'
):
    # -----------------------------------------
    # Criação do modelo
    # -----------------------------------------
    sentido = pulp.LpMaximize if tipo.lower() == 'max' else pulp.LpMinimize
    model = pulp.LpProblem(titulo, sense=sentido)

    # -----------------------------------------
    # Variáveis de decisão
    # -----------------------------------------
    x = pulp.LpVariable.dict(
        indices=range(1, numero_variaveis + 1),
        cat=pulp.LpBinary,
        lowBound=0,
        name='x'
    )

    # -----------------------------------------
    # Variáveis de folga / excesso
    # -----------------------------------------
    variaveis_folga_excesso = pulp.LpVariable.dict(
        indices=range(1, len(restricoes) + 1),
        cat=pulp.LpContinuous,
        lowBound=0,
        name='s'
    )

    # -----------------------------------------
    # Restrições
    # -----------------------------------------
    for indice, (coef, operacao, resultado) in enumerate(restricoes, 1):
        expr = pulp.lpSum(coef[j - 1] * x[j] for j in range(1, numero_variaveis + 1))

        if operacao == '<=':
            model += expr + variaveis_folga_excesso[indice] == resultado
        elif operacao == '>=':
            model += expr - variaveis_folga_excesso[indice] == resultado
        elif operacao == '=':
            model += expr == resultado
        else:
            raise ValueError(f"Operador inválido: {operacao}")

    # -----------------------------------------
    # Função objetivo
    # -----------------------------------------
    model += (
        pulp.lpSum(funcao_objetivo[j - 1] * x[j] for j in range(1, numero_variaveis + 1))
        + execede_funcaoObjetivo
    )

    # -----------------------------------------
    # Resolver
    # -----------------------------------------
    model.solve()

    # -----------------------------------------
    # Montagem do objeto de retorno
    # -----------------------------------------
    resultado = {
        "titulo": titulo,
        "status": pulp.LpStatus[model.status],
        "status_code": model.status,
        "valor_otimo": pulp.value(model.objective),
        "variaveis": {},
        "folgas_excessos": {},
        "variaveis_selecionadas": []
    }

    # Variáveis de decisão
    for j in range(1, numero_variaveis + 1):
        val = x[j].value() or 0.0
        resultado["variaveis"][j] = val

        if val > 0.5:
            resultado["variaveis_selecionadas"].append(j)

    # Folgas / excessos
    for i in range(1, len(restricoes) + 1):
        val = variaveis_folga_excesso[i].value() or 0.0
        resultado["folgas_excessos"][i] = val

    return resultado
