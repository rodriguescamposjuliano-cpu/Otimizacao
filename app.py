import streamlit as st

from ui.layout import setup_page, inject_css
from ui.sidebar import init_session_state, render_sidebar
from ui.route_form import render_rotas
from ui.results_view import render_resultado_rota

from services.route_service import RouteService
from services.optimization_service import OptimizationService

setup_page()
inject_css()
init_session_state()
render_sidebar()

placeholders = render_rotas()

# ================= PROCESSAMENTO =================
if st.session_state.processando:

    progress = st.progress(0.0)

    for idx, rota in enumerate(st.session_state.rotas):

        alternativas = RouteService.buscar_alternativas(
            rota["origem"],
            rota["destino"],
            rota["data_partida"].strftime("%Y-%m-%d")
        )

        if not alternativas:
            resultado_vazio = OptimizationService.resultado_sem_alternativas(
                rota_idx=idx + 1,
                perfil=rota["perfil"],
                tempo_max=rota["tempo_max"],
                orcamento=rota["orcamento"]
            )
            st.session_state.resultados.append(resultado_vazio)
            progress.progress((idx + 1) / len(st.session_state.rotas))
            continue

        resultado = OptimizationService.otimizar(
            alternativas,
            rota["perfil"],
            rota["tempo_max"],
            rota["orcamento"],
            idx + 1
        )

        if resultado:
            st.session_state.resultados.append(resultado)

        progress.progress((idx + 1) / len(st.session_state.rotas))

    st.session_state.processando = False
    st.rerun()

# ================= APRESENTA OS RESULTADOS =================
for i, placeholder in enumerate(placeholders):
    with placeholder.container():
        render_resultado_rota(i + 1)
