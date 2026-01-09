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
st.title(":flight_departure: Otimizador de Viagens (NSGA-II com Restrições)")
st.markdown("Organize suas rotas, defina preferências e restrições, e otimize automaticamente.")


st.markdown(
    """
    <style>
    /* Sidebar buttons */
    section[data-testid="stSidebar"] button {
        width: 100%;
        border-radius: 10px;
        padding: 0.6rem 0.8rem;
        font-size: 15px;
        font-weight: 600;
        transition: all 0.25s ease;
        border: none;
    }

    /* Botão primário (otimizar) */
    .btn-primary {
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        color: white;
    }

    .btn-primary:hover {
        transform: scale(1.02);
        filter: brightness(1.05);
    }

    /* Botão secundário (adicionar rota) */
    .btn-secondary {
        background: #f0f2f6;
        color: #333;
        border: 1px solid #d0d3da;
    }

    .btn-secondary:hover {
        background: #e4e7ee;
        transform: scale(1.01);
    }

    /* Info de processamento */
    .processing-box {
        background: #eef2ff;
        padding: 12px;
        border-radius: 10px;
        border-left: 5px solid #6366f1;
        font-weight: 600;
        color: #1e1b4b;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR: CONTROLES GLOBAIS
# =========================================================
st.sidebar.header(":hammer_and_wrench: Controles")
if not st.session_state.processando:
    if st.sidebar.button("➕ Adicionar nova rota"):
        st.session_state.rotas.append({
            "origem": "",
            "destino": "",
            "data_partida": date.today(),
            "perfil": "Mais rápido",
            "orcamento": 6000,
            "tempo_max": 30,
            "diarias": 1,
            "num_hospedes": 2,
            "min_estrelas": 3,
            "max_estrelas": 5
        })
        st.rerun()

    if st.sidebar.button("🚀 Otimizar todas as rotas"):
        # Limpa resultados e reinicia o processamento
        st.session_state.resultados = []
        st.session_state.processando = True
        st.rerun()
else:
    st.sidebar.info("⏳ Otimização em andamento, aguarde...")

st.sidebar.markdown("---")
st.sidebar.write("Número de rotas:", len(st.session_state.rotas))

# =========================================================
# FORMULÁRIO DE ROTAS
# =========================================================
placeholders = []  # Lista para armazenar placeholders de resultados por rota


# =========================================================
# INTERFACE – ROTAS
# =========================================================
for i, c in enumerate(st.session_state.rotas):
    with st.container():
        # Cabeçalho com expander e botão remover
        col_title, col_button = st.columns([9,1])
        with col_title:
            exp = st.expander(f":round_pushpin: Rota {i + 1}: {c['origem']} → {c['destino']}", expanded=True)
        with col_button:
            if not st.session_state.processando:
                if st.button("❌", key=f"rem_{i}", help="Remover rota"):
                    st.session_state.rotas.pop(i)
                    st.rerun()
            else:
                st.button("🗑️", key=f"rem_{i}_disabled", disabled=True)

        # Placeholder para resultados dessa rota
        resultado_placeholder = exp.container()
        placeholders.append(resultado_placeholder)

        # Conteúdo do expander (inputs da rota)
        with exp:
            col1, col2, col3 = st.columns([1,1,1])
            c["origem"] = col1.text_input("Origem", c["origem"], placeholder="Cidade ou aeroporto", key=f"origem_{i}", disabled=st.session_state.processando)
            c["destino"] = col2.text_input("Destino", c["destino"], placeholder="Cidade ou aeroporto", key=f"destino_{i}", disabled=st.session_state.processando)
            c["data_partida"] = col3.date_input(
                "Data de partida",
                value=c["data_partida"],
                min_value=date.today(),
                format="DD/MM/YYYY",
                key=f"data_{i}",
                disabled=st.session_state.processando
            )

            st.markdown("---")

            col4, col5, col6 = st.columns([1,1,1])
            c["perfil"] = col4.selectbox(
                "Perfil de viagem",
                ["Mais barato", "Equilibrado", "Mais rápido"],
                index=["Mais barato", "Equilibrado", "Mais rápido"].index(c["perfil"]),
                key=f"perfil_{i}",
                disabled=st.session_state.processando
            )
            c["orcamento"] = col5.number_input(
                "Orçamento (R$)",
                min_value=500,
                value=c["orcamento"],
                step=100,
                key=f"orc_{i}",
                disabled=st.session_state.processando
            )
            c["tempo_max"] = col6.number_input(
                "Tempo máximo (h)",
                min_value=1,
                value=int(c["tempo_max"]),
                step=1,
                key=f"tempo_{i}",
                disabled=st.session_state.processando
            )

            st.markdown("---")

            col7, col8, col9 = st.columns([1,1,1])
            c["diarias"] = col7.number_input(
                "Diárias",
                min_value=1,
                value=c["diarias"],
                step=1,
                key=f"diarias_{i}",
                disabled=st.session_state.processando
            )
            c["num_hospedes"] = col8.number_input(
                "Hóspedes",
                min_value=1,
                value=int(c.get("num_hospedes", 2)),
                step=1,
                key=f"hosp_{i}",
                disabled=st.session_state.processando
            )
            estrelas_min_max = col9.slider(
                "Estrelas do hotel",
                min_value=1,
                max_value=5,
                value=(int(c.get("min_estrelas", 3)), int(c.get("max_estrelas", 5))),
                step=1,
                key=f"stars_{i}",
                disabled=st.session_state.processando
            )
            c["min_estrelas"], c["max_estrelas"] = estrelas_min_max

            st.markdown("---")

            # =========================================================
            # RESULTADOS
            # =========================================================
            if st.session_state.resultados:

                resultados_da_rota = [
                    r for r in st.session_state.resultados
                    if r["rota"] == i + 1
                ]

                for idx_r, r in enumerate(resultados_da_rota):
                    st.subheader("📊 Resultado da Otimização")

                    with st.expander(f"✅ Rota {r['rota']} | Perfil: {r['perfil']} | Valor ótimo: {r['valor']}"):

                        with st.expander(f"Gráfico froteira de pareto"):
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

                            st.plotly_chart(
                                fig,
                                use_container_width=True,
                                key=f"pareto_plot_rota_{i}_res_{idx_r}"
                            )


                        # Detalhes da viagem
                        with st.expander("Detalhes da viagem"):
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

            

            # Mensagem de processamento ou resultados
            resultados_rota = [r for r in st.session_state.resultados if r["rota"] == i + 1]

            if st.session_state.processando:
                with resultado_placeholder:
                    st.markdown(
                        """
                        <div style="display:flex; align-items:center; gap:10px;">
                            <div class="loader"></div>
                            <strong>Otimização em andamento...</strong>
                        </div>

                        <style>
                        .loader {
                            border: 4px solid #f3f3f3;
                            border-top: 4px solid #3498db;
                            border-radius: 50%;
                            width: 22px;
                            height: 22px;
                            animation: spin 1s linear infinite;
                        }

                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )

            elif not resultados_rota:
                with resultado_placeholder:
                    st.warning("❌ Nenhum resultado disponível para esta rota ainda.")
          

# =========================================================
# PROCESSAMENTO
# =========================================================
if st.session_state.processando:

    progresso = st.progress(0.0)

    for idx, c in enumerate(st.session_state.rotas):

        rotas_raw = asyncio.run(
            crawler_rome2rio.buscar_rotas(c["origem"], c["destino"], c["data_partida"].strftime("%Y-%m-%d"))
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
            tempo_ideal=c["tempo_max"],
            orcamento=c["orcamento"],
            perfil = c["perfil"]
        )
        
        if res.X is None or len(res.F) == 0:
            continue

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

