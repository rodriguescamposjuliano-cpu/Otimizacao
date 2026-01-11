import streamlit as st
from datetime import date

# Inicializa session state
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
            "max_estrelas": 5,
            "carregar_hospedagem": False,
            "hospedagem": None
        }]

    if "resultados" not in st.session_state:
        st.session_state.resultados = []

# Sidebar
def render_sidebar():
    st.sidebar.header("🛠️ Controles")

    if not st.session_state.processando:
        if st.sidebar.button("Adicionar nova rota", key="btn_add"):
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
                "max_estrelas": 5,
                "carregar_hospedagem": False,
                "hospedagem": None
            })
            st.rerun()

        if st.sidebar.button("Otimizar todas as rotas", key="btn_opt"):
            st.session_state.resultados = []
            st.session_state.dados_hoteis = None
            st.session_state.indice_rota = -1
            st.session_state.processando = True
            st.rerun()
    else:
        st.sidebar.info("⏳ Otimização em andamento...")
        progress_text = st.sidebar.empty()
        progress_bar = st.sidebar.progress(0.0)
        st.session_state.progress_bar = progress_bar
        st.session_state.progress_text = progress_text

    st.sidebar.markdown("---")
    st.sidebar.write("Rotas cadastradas:", len(st.session_state.rotas))
