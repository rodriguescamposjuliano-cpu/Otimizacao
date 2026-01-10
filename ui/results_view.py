import streamlit as st
import numpy as np
import plotly.graph_objects as go
from domain.parsers import format_preco, format_tempo_horas

# =========================================================
# APRESENTA OS RESULTADOS
# =========================================================
def render_resultado_rota(rota_idx: int):
    """
    Renderiza o resultado da otimização de uma rota
    Respeita 100% os dataclasses ResultadoOtimizacao e Alternativa
    """

    resultados = [
        r for r in st.session_state.resultados
        if r.rota_idx == rota_idx
    ]

    if not resultados:
        st.warning("⚠️ Nenhum resultado de otimização disponível para esta rota.")
        return

    for r in resultados:

        with st.expander(
            f"📊 Resultado da Otimização | Perfil: {r.perfil}",
            expanded=True
        ):

            # =====================================================
            # SEM ALTERNATIVAS
            # =====================================================
            if not r.alternativas:
                st.error("❌ Nenhuma alternativa encontrada para esta rota.")
                st.markdown(
                    f"""
                    **Restrições aplicadas**
                    - ⏱ Tempo máximo: {format_tempo_horas(r.tempo_max)}
                    - 💰 Orçamento máximo: {format_preco(r.orcamento)}
                    """
                )
                continue

            # =====================================================
            # MELHOR SOLUÇÃO
            # =====================================================
            a = r.alternativa_escolhida

            st.markdown("### 🏆 Melhor Alternativa Selecionada")

            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Preço", format_preco(a.preco))
            col2.metric("⏱ Tempo", format_tempo_horas(a.tempo))
            col3.metric("🔁 Conexões", a.conexoes)

            with st.expander(
                "📈 Espaço de Soluções & Fronteira de Pareto",
                expanded=False
            ):

                # =====================================================
                # DADOS
                # =====================================================
                alternativas = r.alternativas
                pareto_idx = r.pareto_idx
                tempo_max = r.tempo_max
                orcamento = r.orcamento
                a = r.alternativa_escolhida

                precos = np.array([alt.preco for alt in alternativas])
                tempos = np.array([alt.tempo for alt in alternativas])
                conexoes = np.array([alt.conexoes for alt in alternativas])

                viavel = (precos <= orcamento) & (tempos <= tempo_max)

                # =====================================================
                # TOOLTIP
                # =====================================================
                tooltip = [
                    f"Preço: {format_preco(alt.preco)}<br>"
                    f"Tempo: {format_tempo_horas(alt.tempo)}<br>"
                    f"Conexões: {alt.conexoes}"
                    for alt in alternativas
                ]

                fig = go.Figure()

                # =====================================================
                # TODAS AS ALTERNATIVAS
                # =====================================================
                fig.add_trace(go.Scatter3d(
                    x=precos,
                    y=tempos,
                    z=conexoes,
                    mode="markers",
                    name="Todas as alternativas",
                    marker=dict(size=4, color="lightgray"),
                    text=tooltip,
                    hovertemplate="%{text}<extra></extra>"
                ))

                # =====================================================
                # INVIÁVEIS (VIOLAM RESTRIÇÕES)
                # =====================================================
                if (~viavel).any():
                    fig.add_trace(go.Scatter3d(
                        x=precos[~viavel],
                        y=tempos[~viavel],
                        z=conexoes[~viavel],
                        mode="markers",
                        name="Violam restrições",
                        marker=dict(size=5, color="red"),
                        text=[tooltip[i] for i, v in enumerate(viavel) if not v],
                        hovertemplate="%{text}<extra></extra>"
                    ))

                # =====================================================
                # PARETO
                # =====================================================
                if pareto_idx:
                    fig.add_trace(go.Scatter3d(
                        x=[precos[i] for i in pareto_idx],
                        y=[tempos[i] for i in pareto_idx],
                        z=[conexoes[i] for i in pareto_idx],
                        mode="markers",
                        name="Pareto viável (NSGA-II)",
                        marker=dict(size=7, color="green"),
                        text=[tooltip[i] for i in pareto_idx],
                        hovertemplate="%{text}<extra></extra>"
                    ))

                # =====================================================
                # SOLUÇÃO ESCOLHIDA
                # =====================================================
                fig.add_trace(go.Scatter3d(
                    x=[a.preco],
                    y=[a.tempo],
                    z=[a.conexoes],
                    mode="markers",
                    name="Solução escolhida",
                    marker=dict(size=10, color="gold", symbol="diamond"),
                    text=[
                        f"Preço: {format_preco(a.preco)}<br>"
                        f"Tempo: {format_tempo_horas(a.tempo)}<br>"
                        f"Conexões: {a.conexoes}"
                    ],
                    hovertemplate="%{text}<extra></extra>"
                ))

                # =====================================================
                # LAYOUT
                # =====================================================
                fig.update_layout(
                    height=600,
                    scene=dict(
                        xaxis_title="Preço (R$)",
                        yaxis_title="Tempo (h)",
                        zaxis_title="Conexões"
                    ),
                    legend_title="Classificação"
                )

                st.plotly_chart(fig, width='content')


            # =====================================================
            # ROTEIRO DO VOO
            # =====================================================

            with st.expander(
                f"### 🗺️ Roteiro Completo",
                expanded=False
            ):
                if a.roteiro:
                    for i, etapa in enumerate(a.roteiro):
                        texto = etapa.get("etapa", "").replace("\n", "<br>")
                        st.markdown(
                            f"**Etapa {i + 1}:**<br>{texto}",
                            unsafe_allow_html=True
                        )
