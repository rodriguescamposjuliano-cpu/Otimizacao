import streamlit as st
import asyncio
from datetime import date, datetime, timedelta

from crawler import crawler_rome2rio
from optimization.otimizador import execute_resolucao_problema
from scraping.hotels_serpapi import get_top10_best_rated_total_and_stars
from scraping.cambio_serpapi import get_cambio_usd_brl_serpapi

VALOR_HORA_POR_PERFIL = {
    "Mais barato": 40,
    "Equilibrado": 120,
    "Mais rápido": 300
}

CAMBIO_USD_BRL_DEFAULT = 5.0
CAMBIO_CACHE_TTL = timedelta(hours=1)  # atualiza no máximo 1x por hora

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
        "diarias": 1,
        "num_hospedes": 2,
        "min_estrelas": 3,
        "max_estrelas": 5
    }]

if "resultados" not in st.session_state:
    st.session_state.resultados = []

# Cache do câmbio + timestamp
if "cambio_usd_brl" not in st.session_state:
    st.session_state.cambio_usd_brl = None

if "cambio_usd_brl_ts" not in st.session_state:
    st.session_state.cambio_usd_brl_ts = None

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


def get_cambio_usd_brl_cached() -> float:
    """
    Busca o câmbio USD->BRL via SerpApi no máximo 1 vez por hora.
    Usa cache em st.session_state com timestamp.
    """
    agora = datetime.utcnow()

    # Se já existe câmbio e timestamp, e ainda está dentro do TTL, reutiliza
    if st.session_state.cambio_usd_brl is not None and st.session_state.cambio_usd_brl_ts is not None:
        idade = agora - st.session_state.cambio_usd_brl_ts
        if idade < CAMBIO_CACHE_TTL:
            return float(st.session_state.cambio_usd_brl)

    # Caso contrário, tenta atualizar
    try:
        novo_cambio = float(get_cambio_usd_brl_serpapi())
        st.session_state.cambio_usd_brl = novo_cambio
        st.session_state.cambio_usd_brl_ts = agora
        return novo_cambio

    except Exception as e:
        # fallback seguro (mas agora você verá o erro real)
        st.warning(
            f"⚠️ Falha ao atualizar câmbio USD→BRL. "
            f"Usando fallback {CAMBIO_USD_BRL_DEFAULT:.2f}. Erro: {e}"
        )
        st.session_state.cambio_usd_brl = float(CAMBIO_USD_BRL_DEFAULT)
        st.session_state.cambio_usd_brl_ts = agora
        return float(CAMBIO_USD_BRL_DEFAULT)


# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(page_title="Otimizador de Viagens", layout="wide")
st.title("✈️ Otimizador de Viagens")

# Mostrar câmbio atual no topo
cambio_atual = get_cambio_usd_brl_cached()

st.caption(
    f"Câmbio automático (USD→BRL): **{cambio_atual:.4f}** "
    f"(fallback={CAMBIO_USD_BRL_DEFAULT:.2f})"
)

ts = st.session_state.get("cambio_usd_brl_ts")
if ts:
    st.caption(f"Última atualização do câmbio: {ts.strftime('%d/%m/%Y %H:%M:%S')} UTC")

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

    col4, col5, col6, col7, col8, col9 = st.columns(6)

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

    with col8:
        c["num_hospedes"] = st.number_input(
            "Hóspedes",
            min_value=1,
            value=int(c.get("num_hospedes", 2)),
            step=1,
            key=f"hosp_{i}",
            disabled=st.session_state.processando
        )

    with col9:
        estrelas_min_max = st.slider(
            "Estrelas",
            min_value=1,
            max_value=5,
            value=(
                int(c.get("min_estrelas", 3)),
                int(c.get("max_estrelas", 5))
            ),
            step=1,
            key=f"stars_{i}",
            disabled=st.session_state.processando
        )
        c["min_estrelas"], c["max_estrelas"] = estrelas_min_max

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
            "diarias": 1,
            "num_hospedes": 2,
            "min_estrelas": 3,
            "max_estrelas": 5
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

    # pega câmbio uma vez para a rodada inteira
    cambio = get_cambio_usd_brl_cached()

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
        # HOTÉIS (SerpApi) – Top 10 melhores avaliados (filtrados por estrelas)
        # -----------------------------------------------------
        hotel_totais_usd = []
        hotel_totais_brl = []
        hotel_estrelas = []
        hotel_custo_referencia_brl = 0.0

        try:
            hotel_totais_usd, hotel_estrelas = get_top10_best_rated_total_and_stars(
                destino=c["destino"],
                data_entrada=c["data_partida"].isoformat(),
                dias_estadia=int(c["diarias"]),
                min_estrelas=int(c.get("min_estrelas", 1)),
                max_estrelas=int(c.get("max_estrelas", 5)),
                num_hospedes=int(c.get("num_hospedes", 2)),
            )

            hotel_totais_brl = [float(x) * cambio for x in hotel_totais_usd]

            if hotel_totais_brl:
                hotel_custo_referencia_brl = min(hotel_totais_brl)

        except Exception as e:
            st.warning(f"⚠️ Falha ao buscar hotéis para {c['destino']}: {e}")

        # -----------------------------------------------------
        # Filtro de viabilidade
        # -----------------------------------------------------
        rotas_validas = [
            alt for alt in alternativas
            if alt["tempo"] <= c["tempo_max"]
            and (alt["preco"] + hotel_custo_referencia_brl) <= c["orcamento"]
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
            objetivo = [alt["preco"] + hotel_custo_referencia_brl for alt in rotas_validas]

        else:
            valor_hora = VALOR_HORA_POR_PERFIL[c["perfil"]]
            objetivo = [
                (alt["preco"] + hotel_custo_referencia_brl) + (alt["tempo"] * valor_hora)
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
            "detalhes": rota_escolhida,
            "cambio_usd_brl": cambio,
            "hotel_top10_totais_usd": hotel_totais_usd,
            "hotel_top10_totais_brl": hotel_totais_brl,
            "hotel_top10_estrelas": hotel_estrelas,
            "hotel_custo_referencia_brl": hotel_custo_referencia_brl
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
            st.markdown(f"**Preço (transporte):** {d['Preco']}")

            st.markdown("### ✈️ Roteiro")
            for etapa in d["roteiro"]:
                texto = etapa["etapa"].replace("\n", "<br>")
                st.markdown(f"- {texto}", unsafe_allow_html=True)

            st.markdown("### 🏨 Hotéis (Top 10 melhores avaliados)")
            if r.get("hotel_top10_totais_usd"):
                st.write("Câmbio USD → BRL:", f"{r.get('cambio_usd_brl', CAMBIO_USD_BRL_DEFAULT):.4f}")
                st.write("Totais (USD):", r["hotel_top10_totais_usd"])
                st.write("Totais (BRL):", [round(x, 2) for x in r.get("hotel_top10_totais_brl", [])])
                st.write("Estrelas:", r["hotel_top10_estrelas"])
                st.write(
                    "Custo referência (mínimo, BRL):",
                    f"R$ {r.get('hotel_custo_referencia_brl', 0.0):,.2f}"
                )
            else:
                st.write("Sem dados de hotéis para esta rota.")
