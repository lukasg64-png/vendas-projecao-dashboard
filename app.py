import streamlit as st
import pandas as pd

# ======================================================
#                 CONFIGURAÇÃO DO APP
# ======================================================
st.set_page_config(
    page_title="📈 Projeção de Vendas – FSJ Black Friday",
    layout="wide",
    initial_sidebar_state="expanded"
)

PRIMARY = "#00C853"
DANGER = "#D50000"
WARNING = "#FFD600"
CARD_BG = "#1E1E1E"

# ======================================================
#                   SISTEMA DE LOGIN
# ======================================================

def load_users():
    df = pd.read_csv("data/usuarios.csv")
    df.columns = ["usuario", "senha"]
    return df

def check_login():
    st.markdown("### 🔐 Login – Farmácias São João")

    user = st.text_input("Usuário")
    pwd  = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        users = load_users()
        if ((users["usuario"] == user) & (users["senha"] == pwd)).any():
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
#                CARREGAR ARQUIVOS DO COLAB
# ======================================================

grid = pd.read_csv("data/saida_grid.csv")
resumo = pd.read_csv("data/saida_resumo.csv").iloc[0].to_dict()

# ======================================================
#                       KPIs
# ======================================================
st.title("📈 Painel Executivo – Projeção de Vendas (Site + App)")

col1, col2, col3, col4 = st.columns(4)

def kpi(title, value, color):
    st.markdown(
        f"""
        <div style='background:{CARD_BG}; 
                    padding:18px; 
                    border-radius:10px; 
                    text-align:center; 
                    border-left:6px solid {color};'>
            <h4 style='margin:0; color:white'>{title}</h4>
            <h2 style='margin:0; color:{color}'>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

kpi("Meta do Dia",       f"R$ {resumo['meta_dia']:,.0f}", PRIMARY)
kpi("Venda Atual",       f"R$ {resumo['venda_atual']:,.0f}", PRIMARY)
kpi("Projeção do Dia",   f"R$ {resumo['projecao']:,.0f}",
    PRIMARY if resumo["projecao"] >= resumo["meta_dia"] else DANGER)
kpi("Gap Projetado",     f"R$ {resumo['gap']:,.0f}",
    PRIMARY if resumo["gap"] >= 0 else DANGER)

# ======================================================
#                INSIGHTS EXECUTIVOS
# ======================================================
st.subheader("🧠 Insights Estratégicos")

insights = f"""
• Até agora vendemos **R$ {resumo['venda_atual']:,.0f}**, atingindo  
  **{resumo['frac_hist']*100:.2f}%** da curva histórica.

• A projeção indica **R$ {resumo['projecao']:,.0f}**,  
  frente à meta de **R$ {resumo['meta_dia']:,.0f}**.

• Ontem no mesmo horário: **R$ {resumo['total_d1']:,.0f}**  
  (ritmo: {resumo["ritmo_d1"]:.2f}x)

• Há 7 dias no mesmo horário: **R$ {resumo['total_d7']:,.0f}**  
  (ritmo: {resumo["ritmo_d7"]:.2f}x)
"""

st.info(insights)

# ======================================================
#                    CURVA DDT
# ======================================================
st.subheader("📊 Curva DDT – Slot a Slot")

st.line_chart(
    grid.set_index("SLOT")[["valor_hoje","valor_d1","valor_d7","valor_media_mes"]]
)

# ======================================================
#                  TABELA COMPLETA
# ======================================================
st.subheader("🧮 Tabela Completa")
st.dataframe(grid, use_container_width=True)
