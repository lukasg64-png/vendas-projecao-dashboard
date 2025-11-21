import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ======================================================
#                 CONFIGURAÇÃO DO APP
# ======================================================
st.set_page_config(
    page_title="📈 Projeção de Vendas – FSJ Black Friday",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema de cores
PRIMARY = "#00C853"   # Verde
DANGER = "#D50000"    # Vermelho
WARNING = "#FFD600"   # Amarelo
CARD_BG = "#1E1E1E"

# ======================================================
#                   SISTEMA DE LOGIN
# ======================================================

def check_login():
    st.markdown("### 🔐 Login – Farmácias São João")

    user = st.text_input("Usuário")
    pwd  = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user == "farmacias_sao_joao" and pwd == "blackfriday2025":
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    check_login()
    st.stop()

# ======================================================
#                    FUNÇÕES AUXILIARES
# ======================================================
def meta_do_dia(metas_df, data_ref):
    dia = pd.to_datetime(data_ref).day
    row = metas_df[metas_df["dia"] == dia]
    return float(row["total"].values[0]) if not row.empty else 0.0


def montar_projecao(df_slots, meta_dia, data_ref=None):
    df = df_slots.copy()

    if data_ref is None:
        data_ref = df["DATA"].max()

    data_ref = pd.to_datetime(data_ref).date()
    data_d1 = data_ref - timedelta(days=1)
    data_d7 = data_ref - timedelta(days=7)

    def curva(data_alvo):
        cur = df[df["DATA"] == data_alvo]
        if cur.empty:
            return pd.DataFrame({"SLOT": [], "VALOR_TOTAL_15M": []})
        return (
            cur.groupby("SLOT")["VALOR_TOTAL_15M"]
            .sum()
            .reset_index()
            .sort_values("SLOT")
        )

    curva_hoje = curva(data_ref)
    curva_d1   = curva(data_d1)
    curva_d7   = curva(data_d7)

    mes = pd.to_datetime(data_ref).month
    ano = pd.to_datetime(data_ref).year
    base_mes = df[(pd.to_datetime(df["DATA"]).dt.month == mes) &
                  (pd.to_datetime(df["DATA"]).dt.year == ano)]

    curva_media = base_mes.groupby("SLOT")["VALOR_TOTAL_15M"].mean().reset_index()

    grid = curva_hoje[["SLOT"]].copy()
    grid = grid.merge(curva_hoje.rename(columns={"VALOR_TOTAL_15M": "valor_hoje"}), on="SLOT")
    grid = grid.merge(curva_d1.rename(columns={"VALOR_TOTAL_15M": "valor_d1"}), on="SLOT", how="left")
    grid = grid.merge(curva_d7.rename(columns={"VALOR_TOTAL_15M": "valor_d7"}), on="SLOT", how="left")
    grid = grid.merge(curva_media.rename(columns={"VALOR_TOTAL_15M": "valor_media_mes"}), on="SLOT", how="left")

    grid = grid.fillna(0)

    grid["acum_hoje"]      = grid["valor_hoje"].cumsum()
    grid["acum_d1"]        = grid["valor_d1"].cumsum()
    grid["acum_d7"]        = grid["valor_d7"].cumsum()
    grid["acum_media_mes"] = grid["valor_media_mes"].cumsum()

    grid["frac_hist"] = grid["acum_media_mes"] / grid["acum_media_mes"].max()

    ultimo = grid.index.max()
    venda_atual = grid.loc[ultimo, "acum_hoje"]

    ritmo_d1 = venda_atual / grid.loc[ultimo, "acum_d1"] if grid.loc[ultimo, "acum_d1"] > 0 else 0
    ritmo_d7 = venda_atual / grid.loc[ultimo, "acum_d7"] if grid.loc[ultimo, "acum_d7"] > 0 else 0
    ritmo_media = venda_atual / grid.loc[ultimo, "acum_media_mes"] if grid.loc[ultimo, "acum_media_mes"] > 0 else 0

    frac_hist_atual = grid.loc[ultimo, "frac_hist"]
    projecao = venda_atual / frac_hist_atual if frac_hist_atual > 0 else venda_atual

    total_d1 = grid["acum_d1"].max()
    total_d7 = grid["acum_d7"].max()

    resumo = {
        "meta_dia": meta_dia,
        "venda_atual": venda_atual,
        "projecao": projecao,
        "gap": projecao - meta_dia,
        "ritmo_d1": ritmo_d1,
        "ritmo_d7": ritmo_d7,
        "ritmo_media": ritmo_media,
        "total_d1": total_d1,
        "total_d7": total_d7,
        "frac_hist": frac_hist_atual,
        "data": str(data_ref),
    }

    return grid, resumo

# ======================================================
#                  CARREGAR BASES
# ======================================================

df = pd.read_csv("data/ultima_base.csv")
df["DATA"] = pd.to_datetime(df["DATA"]).dt.date

metas = pd.read_excel("data/metas_novembro.xlsx").rename(columns={
    "Dia": "dia",
    "App": "app",
    "Site": "site",
    "site + APP": "total"
})

meta_dia = meta_do_dia(metas, df["DATA"].max())

# Executar modelo
grid, resumo = montar_projecao(df, meta_dia)

# ======================================================
#             DASHBOARD EXECUTIVO: KPIs
# ======================================================
st.title("📈 Painel Executivo – Projeção de Vendas (Site + App)")

col1, col2, col3, col4 = st.columns(4)

def kpi(card_title, value, color):
    st.markdown(
        f"""
        <div style='background:{CARD_BG}; padding:18px; border-radius:10px; text-align:center; border-left:6px solid {color};'>
            <h4 style='margin:0; color:#FFF'>{card_title}</h4>
            <h2 style='margin:0; color:{color}'>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

kpi("Meta do Dia", f"R$ {resumo['meta_dia']:,.0f}", PRIMARY)
kpi("Venda Atual", f"R$ {resumo['venda_atual']:,.0f}", PRIMARY)
kpi("Projeção do Dia", f"R$ {resumo['projecao']:,.0f}",
    PRIMARY if resumo["projecao"] >= resumo["meta_dia"] else DANGER)
kpi("Gap Projetado", f"R$ {resumo['gap']:,.0f}",
    PRIMARY if resumo["gap"] >= 0 else DANGER)

# ======================================================
#                  INSIGHTS EXECUTIVOS
# ======================================================

st.subheader("🧠 Insights Estratégicos")

ins = f"""
• Até agora vendemos **R$ {resumo['venda_atual']:,.0f}**, equivalente a **{resumo['frac_hist']*100:.2f}%** da curva histórica.  
• A projeção indica **R$ {resumo['projecao']:,.0f}**, contra meta de **R$ {resumo['meta_dia']:,.0f}**.  
• Comparação com ontem (D-1): **R$ {resumo['total_d1']:,.0f}** no mesmo horário.  
• Comparação com semana passada (D-7): **R$ {resumo['total_d7']:,.0f}** no mesmo horário.  
• Ritmo atual vs D-1: **{resumo['ritmo_d1']:.2f}x**  
• Ritmo atual vs D-7: **{resumo['ritmo_d7']:.2f}x**
"""

st.info(ins)

# ======================================================
#                    CURVA DDT
# ======================================================

st.subheader("📊 Curva DDT – Slot a Slot")

st.line_chart(
    grid.set_index("SLOT")[["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"]]
)

# ======================================================
#                TABELA DETALHADA
# ======================================================
st.subheader("🧮 Tabela Completa")

st.dataframe(grid, use_container_width=True)
