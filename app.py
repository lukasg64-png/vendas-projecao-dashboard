import streamlit as st
import pandas as pd
import hashlib

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="📈 Projeção de Vendas — Black Friday 2025",
    layout="wide",
)

# ============================================================
# FUNÇÃO DE LOGIN
# ============================================================

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

# Usuários permitidos
USERS = {
    "fsj": hash_password("blackfriday2025"),
    "lucas": hash_password("panvel2025")
}

def login():
    st.markdown("## 🔐 Login — Farmácias São João")
    st.markdown("### Black Friday 2025")

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar", use_container_width=True):
        if username in USERS and USERS[username] == hash_password(password):
            st.session_state["auth"] = True
            st.session_state["user"] = username
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")

    st.stop()

# Se não estiver autenticado → mostrar tela de login
if "auth" not in st.session_state:
    login()

# ============================================================
# CABEÇALHO EXECUTIVO
# ============================================================

st.markdown(
    """
    <h1 style='text-align:center; color:#0A74DA;'>
        📈 Painel Executivo — Projeção de Vendas<br>
        <span style='font-size:22px;'>Farmácias São João — Black Friday 2025</span>
    </h1>
    <br>
    """,
    unsafe_allow_html=True
)

# ============================================================
# IMPORTAÇÃO DOS DADOS
# ============================================================

df_grid = pd.read_csv("data/saida_grid.csv")
df_resumo = pd.read_csv("data/saida_resumo.csv")

resumo = df_resumo.iloc[0]

# ============================================================
# KPIS — CARDS EXECUTIVOS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

def card(col, title, value, color="#0A74DA"):
    col.markdown(
        f"""
        <div style="
            background-color:#f8f9fa;
            padding:20px;
            border-radius:12px;
            box-shadow:0 2px 6px rgba(0,0,0,0.1);
            text-align:center;
        ">
            <h3 style="color:{color}; margin-bottom:5px;">{title}</h3>
            <h2 style="font-weight:bold; margin-top:0;">{value}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

card(col1, "Meta do Dia", f"R$ {resumo['meta_dia']:,.0f}")
card(col2, "Projeção Final", f"R$ {resumo['projecao_dia']:,.0f}")
card(col3, "Venda Atual", f"R$ {resumo['venda_atual_ate_slot']:,.0f}")
card(col4, "Gap vs Meta", f"R$ {resumo['desvio_projecao']:,.0f}",
     color="#D9534F" if resumo["desvio_projecao"] < 0 else "#28A745")

# ============================================================
# GRÁFICO PRINCIPAL (DDT)
# ============================================================

st.markdown("## 📊 Curva DDT — Slot a Slot")

plot_df = df_grid.set_index("SLOT")[[
    "valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"
]]

st.line_chart(plot_df)

# ============================================================
# RESUMO EXPLICATIVO
# ============================================================

st.markdown("## 📝 Resumo Executivo")

st.write(f"📌 **Referência:** {resumo['data_referencia']}")
st.write(f"📌 **Projeção:** R$ {resumo['projecao_dia']:,.0f}")
st.write(f"📌 **Venda Atual:** R$ {resumo['venda_atual_ate_slot']:,.0f}")
st.write(f"📌 **Ritmo vs D-1:** {resumo['ritmo_vs_d1']:.2f}x")
st.write(f"📌 **Ritmo vs D-7:** {resumo['ritmo_vs_d7']:.2f}x")
st.write(f"📌 **Ritmo vs Média:** {resumo['ritmo_vs_media']:.2f}x")

st.info(resumo["explicacao_ritmo"])
st.info(resumo["explicacao_d1"])
st.info(resumo["explicacao_d7"])

# ============================================================
# TABELA COMPLETA
# ============================================================

st.markdown("## 📋 Tabela Completa — DDT")
st.dataframe(df_grid, use_container_width=True)

# ============================================================
# DOWNLOADS
# ============================================================

st.markdown("## ⬇️ Downloads")
st.download_button("Baixar DDT (Grid)", df_grid.to_csv(index=False), "saida_grid.csv")
st.download_button("Baixar Resumo", df_resumo.to_csv(index=False), "saida_resumo.csv")
