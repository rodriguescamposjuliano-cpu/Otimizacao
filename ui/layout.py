import streamlit as st


def setup_page():
    st.set_page_config(
        page_title="Otimizador de Viagens",
        layout="wide",
        page_icon=":airplane:"
    )

    st.title(":flight_departure: Seu Voo Ideal: Escolha Inteligente de Rotas")
    st.markdown(
        "Organize suas rotas, defina preferências e restrições, e otimize automaticamente."
    )


def inject_css():
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] button {
            width: 100%;
            border-radius: 10px;
            padding: 0.6rem 0.8rem;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.25s ease;
            border: none;
        }

        .btn-primary {
            background: linear-gradient(135deg, #6a11cb, #2575fc);
            color: white;
        }

        .btn-primary:hover {
            transform: scale(1.02);
        }

        .processing-box {
            background: #eef2ff;
            padding: 12px;
            border-radius: 10px;
            border-left: 5px solid #6366f1;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
