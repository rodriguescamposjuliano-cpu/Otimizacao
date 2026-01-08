import streamlit as st
import asyncio
from crawler import crawler_rome2rio
from optimization.otimizador import execute_resolucao_problema

# ----------------------
# Funções utilitárias
# ----------------------
def parse_tempo(tempo_str):
    """
    Converte strings como '25h 6min' em horas decimais.
    """
    h, m = 0, 0
    if 'h' in tempo_str:
        h = int(tempo_str.split('h')[0])
        m_part = tempo_str.split('h')[1]
        if 'min' in m_part:
            m = int(m_part.replace('min','').strip())
    elif 'min' in tempo_str:
        m = int(tempo_str.replace('min','').strip())
    return h + m/60

def parse_preco(preco_str):
    """
    Converte string 'R$8,659' em float 8659.0
    """
    preco_str = preco_str.replace('R$', '').replace('.', '').replace(',', '').strip()
    try:
        return float(preco_str)
    except:
        return 0.0
    
st.title("Otimização de Rotas")

# ----------------------
# Inputs do usuário
# ----------------------
origem = st.text_input("Origem")
destino = st.text_input("Destino")

perfil = st.selectbox(
    "Perfil de otimização",
    ["Mais barato", "Mais rápido", "Equilibrado"]
)

orcamento = st.number_input("Orçamento máximo (R$)", value=6000)
tempo_max = st.number_input("Tempo máximo (horas)", value=30)

# ----------------------
# Botão de otimização
# ----------------------
if st.button("Otimizar rota"):

    # Busca rotas Rome2Rio
    rotas = asyncio.run(
        crawler_rome2rio.buscar_rotas(origem, destino)
    )

    if not rotas:
        st.warning("Nenhuma rota encontrada.")
    else:
        # Parse de tempo e preço
        # Pegando tempo_total e preco do primeiro schedule de cada rota
        # Para cada rota, pegar o detalhe com menor tempo_total
        tempos = []
        custos = []

        for r in rotas:
            detalhes = r.get('detalhes', [])
            for d in detalhes:
                tempos.append(parse_tempo(d['tempo_total']))
                custos.append(parse_preco(d['Preco']))

        print("Tempos (h):", tempos)
        print("Custos (R$):", custos)    

        # Restrição: escolher apenas 1 rota
        restricoes = [
            ([1]*len(tempos), '=', 1)
        ]

        # Função objetivo: minimiza horas
        funcao_objetivo = tempos
        tipo = 'min'

        # Chamada do otimizador
        execute_resolucao_problema(
            titulo="Otimização de Viagem (Cenário Real Rome2Rio)",
            numero_variaveis=len(tempos),
            funcao_objetivo=funcao_objetivo,
            restricoes=restricoes,
            tipo=tipo
        )

        st.success(f"Perfil selecionado: {perfil}")
        st.write(rotas)  # opcional: mostra rotas encontradas


