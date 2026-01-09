import streamlit as st
import asyncio
from datetime import date
import numpy as np
import plotly.express as px

from crawler import crawler_rome2rio
from optimization.nsga2_solver import executar_nsga2

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

def format_tempo_horas(tempo_h: float) -> str:
    h = int(tempo_h)
    m = int(round((tempo_h - h) * 60))
    return f"{h}h {m} min"

def parse_preco(preco_str: str) -> float:
    if not preco_str:
        return 0.0
    preco_str = preco_str.replace("R$", "").replace(".", "").replace(",", "").strip()
    try:
        return float(preco_str)
    except ValueError:
        return 0.0

def format_preco(preco: float) -> str:
    return f"R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(page_title="Otimizador de Viagens", layout="wide")
st.title("✈️ Otimizador de Viagens (NSGA-II com Restrições)")

# =========================================================
# INTERFACE – ROTAS
# =========================================================
for i, c in enumerate(st.session_state.rotas):

    st.subheader(f"Rota {i + 1}")

    col1, col2, col3 = st.columns(3)
    c["origem"] = col1.text_input("Origem", c["origem"], key=f"origem_{i}")
    c["destino"] = col2.text_input("Destino", c["destino"], key=f"destino_{i}")
    c["data_partida"] = col3.date_input(
        "Data de partida",
        value=c["data_partida"],
        min_value=date.today(),
        format="DD/MM/YYYY",
        key=f"data_{i}"
    )

    col4, col5, col6, col7 = st.columns(4)

    c["perfil"] = col4.selectbox(
        "Perfil",
        ["Mais barato", "Equilibrado", "Mais rápido"],
        index=["Mais barato", "Equilibrado", "Mais rápido"].index(c["perfil"]),
        key=f"perfil_{i}"
    )

    c["orcamento"] = col5.number_input(
        "Orçamento (R$)", min_value=500, value=c["orcamento"], step=100, key=f"orc_{i}"
    )

    c["tempo_max"] = col6.number_input(
        "Tempo máximo (h)", min_value=1, value=int(c["tempo_max"]), step=1, key=f"tempo_{i}"
    )

    c["diarias"] = col7.number_input(
        "Diárias", min_value=1, value=c["diarias"], step=1, key=f"diarias_{i}"
    )

    if st.button("❌ Remover", key=f"rem_{i}"):
        st.session_state.rotas.pop(i)
        st.rerun()

    st.divider()

# =========================================================
# BOTÕES
# =========================================================
col_a, col_b = st.columns(2)

if col_a.button("➕ Nova rota"):
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

if col_b.button("🚀 Otimizar todas as rotas"):
    st.session_state.resultados = []
    st.session_state.processando = True
    st.rerun()

# =========================================================
# PROCESSAMENTO
# =========================================================
if st.session_state.processando:

    progresso = st.progress(0.0)

    for idx, c in enumerate(st.session_state.rotas):

        rotas_raw = asyncio.run(
            crawler_rome2rio.buscar_rotas(c["origem"], c["destino"])
        )

        alternativas = []
        for r in rotas_raw:
            for d in r.get("detalhes", []):
                alternativas.append({
                    "tempo": parse_tempo(d.get("tempo_total")),
                    "preco": parse_preco(d.get("Preco")),
                    "conexoes": int(d.get("conexoes", 0)),
                    "saida": d.get("saida"),
                    "chegada": d.get("chegada"),
                    "tempo_total": d.get("tempo_total"),
                    "roteiro": d.get("roteiro", []),
                    "Preco": d.get("Preco")
                })

        if not alternativas:
            continue

        res = executar_nsga2(
            alternativas,
            tempo_max=c["tempo_max"],
            orcamento=c["orcamento"]
        )

        F_raw = res.F
        X_raw = res.X.astype(int)

        F_unique, idx_unique = np.unique(F_raw, axis=0, return_index=True)
        X_unique = X_raw[idx_unique]

        # ESCOLHA FINAL POR PERFIL
        if c["perfil"] == "Mais barato":
            idx_sol = np.argmin(F_unique[:, 0])
        elif c["perfil"] == "Mais rápido":
            tempos = np.array([alternativas[i[0]]["tempo"] for i in X_unique])
            idx_sol = np.argmin(tempos)
        else:
            F_norm = (F_unique - F_unique.min(axis=0)) / (np.ptp(F_unique, axis=0) + 1e-9)
            idx_sol = np.argmin(F_norm.sum(axis=1))

        rota = alternativas[X_unique[idx_sol, 0]]

        st.session_state.resultados.append({
            "rota": idx + 1,
            "perfil": c["perfil"],
            "valor": f"R$ {rota['preco']:.2f}",
            "detalhes": rota,
            "pareto": F_unique,
            "pareto_idx": X_unique[:, 0],
            "alternativas": alternativas,
            "tempo_max": c["tempo_max"],
            "orcamento": c["orcamento"]
        })

        progresso.progress((idx + 1) / len(st.session_state.rotas))

    st.session_state.processando = False
    st.rerun()

# =========================================================
# RESULTADOS
# =========================================================
if st.session_state.resultados:

    st.subheader("📊 Resultado da Otimização")

    for r in st.session_state.resultados:

        st.success(
            f"✅ Rota {r['rota']} | Perfil: {r['perfil']} | Valor ótimo: {r['valor']}"
        )

        alternativas = r["alternativas"]
        pareto = r["pareto"]
        tempo_max = r["tempo_max"]
        orcamento = r["orcamento"]

        precos = np.array([a["preco"] for a in alternativas])
        tempos = np.array([a["tempo"] for a in alternativas])
        conexoes = np.array([a["conexoes"] for a in alternativas])
        viavel = (precos <= orcamento) & (tempos <= tempo_max)
        pareto_idx = r["pareto_idx"]

        # Criar tooltip com descrições completas
        tooltip_text = [
            f"Preço: {format_preco(a['preco'])}<br>"
            f"Tempo: {format_tempo_horas(a['tempo'])}<br>"
            f"Conexões: {a['conexoes']}"
            for a in alternativas
        ]

        fig = px.scatter_3d(title="Espaço de Soluções 3D × Pareto Ótimo")

        # Todas as rotas
        fig.add_scatter3d(
            x=precos,
            y=tempos,
            z=conexoes,
            mode="markers",
            name="Todas as rotas",
            marker=dict(size=4, color="lightgray"),
            text=tooltip_text,
            hovertemplate="%{text}<extra></extra>"
        )

        # Rotas inviáveis
        tooltip_inviavel = [tooltip_text[i] for i, v in enumerate(viavel) if not v]
        fig.add_scatter3d(
            x=precos[~viavel],
            y=tempos[~viavel],
            z=conexoes[~viavel],
            mode="markers",
            name="Violam restrições",
            marker=dict(size=5, color="red"),
            text=tooltip_inviavel,
            hovertemplate="%{text}<extra></extra>"
        )

        # Pareto
        tooltip_pareto = [
            f"Preço: {format_preco(alternativas[i]['preco'])}<br>"
            f"Tempo: {format_tempo_horas(alternativas[i]['tempo'])}<br>"
            f"Conexões: {alternativas[i]['conexoes']}"
            for i in pareto_idx
        ]
        fig.add_scatter3d(
            x=[alternativas[i]["preco"] for i in pareto_idx],
            y=[alternativas[i]["tempo"] for i in pareto_idx],
            z=[alternativas[i]["conexoes"] for i in pareto_idx],
            mode="markers",
            name="Pareto viável (NSGA-II)",
            marker=dict(size=7, color="green"),
            text=tooltip_pareto,
            hovertemplate="%{text}<extra></extra>"
        )

        # Solução escolhida
        detalhe = r["detalhes"]
        tooltip_escolhida = f"Preço: {format_preco(detalhe['preco'])}<br>Tempo: {format_tempo_horas(detalhe['tempo'])}<br>Conexões: {detalhe['conexoes']}"
        fig.add_scatter3d(
            x=[detalhe["preco"]],
            y=[detalhe["tempo"]],
            z=[detalhe["conexoes"]],
            mode="markers",
            name="Solução escolhida",
            marker=dict(size=10, color="gold", symbol="diamond"),
            text=[tooltip_escolhida],
            hovertemplate="%{text}<extra></extra>"
        )

        fig.update_layout(
            scene=dict(
                xaxis_title="Preço (R$)",
                yaxis_title="Tempo",
                zaxis_title="Conexões"
            ),
            legend_title="Classificação"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Detalhes da viagem
        with st.expander("🧭 Detalhes da viagem"):
            d = detalhe

            st.markdown(f"**Saída:** {d['saida']}")
            st.markdown(f"**Chegada:** {d['chegada']}")
            st.markdown(f"**Tempo total:** {d['tempo_total']}")
            st.markdown(f"**Conexões:** {d['conexoes']}")
            st.markdown(f"**Preço:** {d['Preco']}")

            st.markdown("### ✈️ Roteiro completo")
            for j, etapa in enumerate(d["roteiro"]):
                texto = etapa.get("etapa", "").replace("\n", "<br>")
                st.markdown(
                    f"**Etapa {j + 1}:**<br>{texto}",
                    unsafe_allow_html=True
                )
