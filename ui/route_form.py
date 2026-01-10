import streamlit as st
from datetime import date


def render_rotas():
    placeholders = []

    for i, c in enumerate(st.session_state.rotas):

        col_title, col_btn = st.columns([9, 1])

        with col_title:
            exp = st.expander(
                f"📍 Rota {i + 1}: {c['origem']} → {c['destino']}",
                expanded=True
            )

        with col_btn:
            if not st.session_state.processando:
                if st.button("❌", key=f"rem_{i}"):
                    st.session_state.rotas.pop(i)

                    # LIMPA RESULTADOS
                    st.session_state.resultados = []

                    st.rerun()
            else:
                st.button("🗑️", disabled=True, key=f"rem_dis_{i}")


        # ================= EXPANDER =================
        with exp:
            col1, col2, col3 = st.columns(3)

            c["origem"] = col1.text_input(
                "Origem", c["origem"],
                key=f"origem_{i}",
                disabled=st.session_state.processando
            )

            c["destino"] = col2.text_input(
                "Destino", c["destino"],
                key=f"destino_{i}",
                disabled=st.session_state.processando
            )

            c["data_partida"] = col3.date_input(
                "Data de partida",
                c["data_partida"],
                min_value=date.today(),
                format="DD/MM/YYYY",
                key=f"data_{i}",
                disabled=st.session_state.processando
            )

            st.markdown("---")

            col4, col5, col6 = st.columns(3)

            c["perfil"] = col4.selectbox(
                "Perfil",
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
                key=f"tempo_{i}",
                disabled=st.session_state.processando
            )

            st.markdown("---")

            col7, col8, col9 = st.columns(3)

            c["diarias"] = col7.number_input(
                "Diárias",
                min_value=1,
                value=c["diarias"],
                key=f"diarias_{i}",
                disabled=st.session_state.processando
            )

            c["num_hospedes"] = col8.number_input(
                "Hóspedes",
                min_value=1,
                value=c["num_hospedes"],
                key=f"hosp_{i}",
                disabled=st.session_state.processando
            )

            c["min_estrelas"], c["max_estrelas"] = col9.slider(
                "Estrelas do hotel",
                1, 5,
                (c["min_estrelas"], c["max_estrelas"]),
                key=f"stars_{i}",
                disabled=st.session_state.processando
            )

            st.markdown("---")

            # PLACEHOLDER PARA ADICIONAR OS RESULTADOS.
            resultado_placeholder = st.empty()
            placeholders.append(resultado_placeholder)

    return placeholders
