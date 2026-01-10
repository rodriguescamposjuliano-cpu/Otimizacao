import streamlit as st
from datetime import date


def init_session_state():
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
            "diarias": 1,
            "num_hospedes": 2,
            "min_estrelas": 3,
            "max_estrelas": 5
        }]

    if "resultados" not in st.session_state:
        st.session_state.resultados = []


def render_sidebar():
    st.sidebar.header("🛠️ Controles")

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
            st.session_state.resultados = []
            st.session_state.processando = True
            st.rerun()
    else:
        st.sidebar.info("⏳ Otimização em andamento...")

    st.sidebar.markdown("---")
    st.sidebar.write("Rotas cadastradas:", len(st.session_state.rotas))
