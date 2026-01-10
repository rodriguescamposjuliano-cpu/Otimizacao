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
   st.markdown("""
    <style>
    /* ===============================
    Botões "Adicionar" e "Otimizar" - azul degradê
    =============================== */
    div.st-key-btn_add button[kind="secondary"],
    div.st-key-btn_opt button[kind="secondary"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 16px;
        font-weight: 600;
        padding: 12px 32px;
        border-radius: 12px;
        border: none;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        width: 220px;
        height: 55px;
        cursor: pointer;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #4A90E2, #357ABD);
        color: #ffffff;
        text-align: center;
        display: inline-block;
    }

    div.st-key-btn_add button[kind="secondary"]:hover,
    div.st-key-btn_opt button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #5AA0F2, #4A80D0);
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }

    /* ===============================
    Botão "Remover" - vermelho degradê
    =============================== */
    div.st-key-btn_del button[kind="secondary"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 16px;
        font-weight: 600;
        padding: 12px 32px;
        border-radius: 12px;
        border: none;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        width: 220px;
        height: 55px;
        cursor: pointer;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #FF5F6D, #FF3A3A);
        color: #ffffff;
        text-align: center;
        display: inline-block;
    }

    /* ===============================
   Botões de remoção de rota (vários)
   =============================== */
    div[class*="st-key-rem_"] button[kind="secondary"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 18px;
        font-weight: 700;
        padding: 0;                      /* Padding interno zero para ícone centralizado */
        border-radius: 50%;               /* Botão circular */
        border: none;
        width: 40px;                      /* Tamanho uniforme */
        height: 40px;
        cursor: pointer;
        background: linear-gradient(135deg, #FF5F6D, #FF3A3A); /* Gradiente vermelho */
        color: #ffffff;                   /* ❌ em branco */
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Botões de remoção de rota (vários) */
    div[class*="st-key-rem_"] button[kind="secondary"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 18px;
        font-weight: 700;
        padding: 0;                     
        border-radius: 50%;              
        border: none;
        width: 40px;                     
        height: 40px;
        cursor: pointer;
        background: linear-gradient(135deg, #FF5F6D, #FF3A3A); 
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Força todo texto dentro do botão de remover para branco */
    div[class*="st-key-rem_"] button[kind="secondary"] * {
        color: #ffffff !important;
    }

    /* Hover do botão de remover */
    div[class*="st-key-rem_"] button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #FF6F7A, #FF1A1A);
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.2);
    }

    /* Botões de remover desabilitados */
    div[class*="st-key-rem_"] button:disabled {
        background: #C0C0C0 !important;
        color: #f5f5f5 !important;
        cursor: not-allowed;
        box-shadow: none !important;
    }


    /* ===============================
    Botões desabilitados
    =============================== */
    div.stButton button:disabled {
        background: #C0C0C0 !important;
        color: #f5f5f5 !important;
        cursor: not-allowed;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)


