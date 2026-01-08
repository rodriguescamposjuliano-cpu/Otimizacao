import streamlit as st
import asyncio
from datetime import date
from crawler import crawler_rome2rio
from optimization.otimizador import execute_resolucao_problema

VALOR_HORA_POR_PERFIL = {
    "Mais barato": 40,
    "Equilibrado": 120,
    "Mais rápido": 300
}

# =========================================================
# ESTADOS GLOBAIS
# =========================================================
if "processando" not in st.session_state:
    st.session_state.processando = False

if "rotas" not in st.session_state:
    st.session_state.rotas = [{
        "origem": "",
        "destino": "",
        "data_partida": date.today(),
        "perfil": "Mais rápido",
        "orcamento": 6000,
        "tempo_max": 30,
        "diarias": 1
    }]

if "resultados" not in st.session_state:
    st.session_state.resultados = []

# =========================================================
# FUNÇÕES UTILITÁRIAS
# =========================================================
def horas_para_hhmm(horas: float) -> str:
    if horas is None:
        return "0h 0min"
    h = int(horas)
    m = int(round((horas - h) * 60))
    if m == 60:
        h += 1
        m = 0
    return f"{h}h {m}min"


def parse_tempo(tempo_str: str) -> float:
    if not tempo_str:
        return 0.0
    h, m = 0, 0
    if "h" in tempo_str:
        partes = tempo_str.split("h")
        h = int(partes[0])
        if "min" in partes[1]:
            m = int(partes[1].replace("min", "").strip())
    elif "min" in tempo_str:
        m = int(tempo_str.replace("min", "").strip())
    return h + m / 60


def parse_preco(preco_str: str) -> float:
    if not preco_str:
        return 0.0
    preco_str = (
        preco_str.replace("R$", "")
        .replace(".", "")
        .replace(",", "")
        .strip()
    )
    try:
        return float(preco_str)
    except ValueError:
        return 0.0


# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(page_title="Otimizador de Viagens", layout="wide")
st.title("✈️ Otimizador de Viagens")

# =========================================================
# INTERFACE – ROTAS
# =========================================================
for i, c in enumerate(st.session_state.rotas):

    st.subheader(f"Rota {i + 1}")

    col1, col2, col3 = st.columns(3)

    with col1:
        c["origem"] = st.text_input(
            "Origem", c["origem"], key=f"origem_{i}",
            disabled=st.session_state.processando
        )

    with col2:
        c["destino"] = st.text_input(
            "Destino", c["destino"], key=f"destino_{i}",
            disabled=st.session_state.processando
        )

    with col3:
        c["data_partida"] = st.date_input(
            "Data de partida",
            value=c["data_partida"],
            min_value=date.today(),
            format="DD/MM/YYYY",
            key=f"data_{i}",
            disabled=st.session_state.processando
        )

    col4, col5, col6, col7 = st.columns(4)

    with col4:
        c["perfil"] = st.selectbox(
            "Perfil",
            ["Mais barato", "Mais rápido", "Equilibrado"],
            index=["Mais barato", "Mais rápido", "Equilibrado"].index(c["perfil"]),
            key=f"perfil_{i}",
            disabled=st.session_state.processando
        )

    with col5:
        c["orcamento"] = st.number_input(
            "Orçamento (R$)",
            min_value=500,
            value=c["orcamento"],
            step=100,
            key=f"orc_{i}",
            disabled=st.session_state.processando
        )

    with col6:
        c["tempo_max"] = st.number_input(
            "Tempo máximo (h)",
            min_value=1,
            value=int(c["tempo_max"]),
            step=1,
            key=f"tempo_{i}",
            disabled=st.session_state.processando
        )

    with col7:
        c["diarias"] = st.number_input(
            "Diárias",
            min_value=1,
            value=c["diarias"],
            step=1,
            key=f"diarias_{i}",
            disabled=st.session_state.processando
        )

    if st.button("❌ Remover", key=f"rem_{i}", disabled=st.session_state.processando):
        st.session_state.rotas.pop(i)
        st.rerun()

    st.divider()

# =========================================================
# BOTÕES GLOBAIS
# =========================================================
col_a, col_b = st.columns(2)

with col_a:
    if st.button("➕ Nova rota", disabled=st.session_state.processando):
        st.session_state.rotas.append({
            "origem": "",
            "destino": "",
            "data_partida": date.today(),
            "perfil": "Mais rápido",
            "orcamento": 6000,
            "tempo_max": 30,
            "diarias": 1
        })
        st.rerun()

with col_b:
    if st.button("🚀 Otimizar todas as rotas", disabled=st.session_state.processando):
        st.session_state.resultados = []
        st.session_state.processando = True
        st.rerun()

# =========================================================
# PROCESSAMENTO
# =========================================================
if st.session_state.processando:

    total = len(st.session_state.rotas)
    progresso = st.progress(0)
    status = st.empty()

    for idx, c in enumerate(st.session_state.rotas):

        status.markdown(f"### 🔄 Processando rota {idx + 1} de {total}")

        if not c["origem"] or not c["destino"]:
            continue

        rotas_raw = asyncio.run(
            crawler_rome2rio.buscar_rotas(c["origem"], c["destino"])
        )

        # -----------------------------------------------------
        # Construção das alternativas completas
        # -----------------------------------------------------
        alternativas = []

        for r in rotas_raw:
            for d in r.get("detalhes", []):
                alternativas.append({
                    "tempo": parse_tempo(d.get("tempo_total")),
                    "preco": parse_preco(d.get("Preco")),
                    "saida": d.get("saida"),
                    "chegada": d.get("chegada"),
                    "tempo_total": d.get("tempo_total"),
                    "conexoes": d.get("conexoes"),
                    "roteiro": d.get("roteiro"),
                    "Preco": d.get("Preco")
                })

        # -----------------------------------------------------
        # Filtro de viabilidade
        # -----------------------------------------------------
        rotas_validas = [
            alt for alt in alternativas
            if alt["tempo"] <= c["tempo_max"]
            and alt["preco"] <= c["orcamento"]
        ]

        if not rotas_validas:
            st.warning(f"⚠️ Nenhuma rota viável para a rota {idx + 1}")
            continue

        # -----------------------------------------------------
        # Função objetivo
        # -----------------------------------------------------
        if c["perfil"] == "Mais rápido":
            objetivo = [alt["tempo"] for alt in rotas_validas]

        elif c["perfil"] == "Mais barato":
            objetivo = [alt["preco"] for alt in rotas_validas]

        else:
            valor_hora = VALOR_HORA_POR_PERFIL[c["perfil"]]
            objetivo = [
                alt["preco"] + (alt["tempo"] * valor_hora)
                for alt in rotas_validas
            ]

        restricoes = [
            ([1] * len(objetivo), "=", 1)
        ]

        res = execute_resolucao_problema(
            titulo=f"Otimização – Rota {idx + 1}",
            numero_variaveis=len(objetivo),
            funcao_objetivo=objetivo,
            restricoes=restricoes,
            tipo="min"
        )

        indice = next(
            k
            for k, v in res["variaveis"].items()
            if v == 1
        )


        rota_escolhida = rotas_validas[indice - 1]

        valor = (
            horas_para_hhmm(res["valor_otimo"])
            if c["perfil"] == "Mais rápido"
            else f"R$ {res['valor_otimo']:.2f}"
        )

        st.session_state.resultados.append({
            "rota": idx + 1,
            "perfil": c["perfil"],
            "valor": valor,
            "detalhes": rota_escolhida
        })

        progresso.progress((idx + 1) / total)

    st.session_state.processando = False
    st.rerun()

# =========================================================
# RESULTADOS
# =========================================================
if st.session_state.resultados:

    st.subheader("📊 Resultados da Otimização")

    for r in st.session_state.resultados:

        st.success(
            f"✅ Rota {r['rota']} | "
            f"Perfil: {r['perfil']} | "
            f"Valor ótimo: {r['valor']}"
        )

        with st.expander("🧭 Detalhes da viagem"):
            d = r["detalhes"]

            st.markdown(f"**Saída:** {d['saida']}")
            st.markdown(f"**Chegada:** {d['chegada']}")
            st.markdown(f"**Tempo total:** {d['tempo_total']}")
            st.markdown(f"**Conexões:** {d['conexoes']}")
            st.markdown(f"**Preço:** {d['Preco']}")

            st.markdown("### ✈️ Roteiro")
            for etapa in d["roteiro"]:
                texto = etapa["etapa"].replace("\n", "<br>")
                st.markdown(f"- {texto}", unsafe_allow_html=True)
