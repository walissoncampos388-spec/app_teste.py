import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Streamlit - Cia do Jeans - Calculadora Inteligente",
    layout="wide",
)

# Estilização CSS para ajustar o layout exatamente como no print
st.markdown(
    """
    <style>
    /* Estilo do Banner Principal */
    .header-banner {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 40%, #1d4ed8 100%);
        padding: 40px 20px;
        border-radius: 16px;
        text-align: center;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Logo aumentada */
    .header-logo {
        height: 130px; /* Logo maior para se destacar */
        width: auto;
        margin-bottom: 12px;
        object-fit: contain;
    }

    .header-title {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 1.5px;
        margin: 10px 0 5px 0;
        color: #ffffff;
    }

    .header-subtitle {
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #60a5fa;
        text-transform: uppercase;
        margin: 0;
    }

    /* Estilo dos Botões Principais */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 48px;
        font-weight: 600;
        background-color: #ffffff;
        color: #1e293b;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    div.stButton > button:hover {
        border-color: #2563eb;
        color: #2563eb;
        background-color: #f8fafc;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# CABEÇALHO (BANNER AZUL) COM A LOGO MAIOR
# -----------------------------------------------------------------------------
# Substitua a URL abaixo pelo caminho local da sua logo se preferir (ex: "logo.png")
LOGO_URL = "https://via.placeholder.com/150/000000/FFFFFF/?text=LOGO"

st.markdown(
    f"""
    <div class="header-banner">
        <img src="{LOGO_URL}" class="header-logo" alt="Logo Cia do Jeans">
        <div class="header-title">CIA DO JEANS</div>
        <div class="header-subtitle">⚡ LOGÍSTICA & COTAÇÃO INTELIGENTE</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# BOTÕES DE NAVEGAÇÃO
# -----------------------------------------------------------------------------
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    st.button("📊 COTAR NOVO FRETE", use_container_width=True)

with col_btn2:
    st.button("📦 RASTREAR ENCOMENDA", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# -----------------------------------------------------------------------------
# PASSO 1: DESTINO DO PEDIDO
# -----------------------------------------------------------------------------
st.subheader("📍 PASSO 1: DESTINO DO PEDIDO")

col_cep, col_cidade, col_uf = st.columns([2, 3, 1])

with col_cep:
    cep = st.text_input(
        "📍 Digite o CEP do Cliente:", placeholder="00000000", max_chars=8
    )

with col_cidade:
    cidade = st.text_input(
        "📍 Cidade Identificada:", placeholder="Digite a Cidade se não buscar..."
    )

with col_uf:
    uf = st.text_input("🏳️ UF:", placeholder="EX: GO", max_chars=2)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# -----------------------------------------------------------------------------
# PASSO 2: O QUE ESTAMOS ENVIANDO HOJE?
# -----------------------------------------------------------------------------
st.subheader("👖 PASSO 2: O QUE ESTAMOS ENVIANDO HOJE?")

col_calcas, col_gola, col_nf = st.columns([2, 2, 2])

with col_calcas:
    qtd_calcas = st.number_input("Quantidade de Calças:", min_value=0, step=1)

with col_gola:
    qtd_gola = st.number_input("Quantidade de Gola O:", min_value=0, step=1)

with col_nf:
    valor_nf = st.text_input(
        "💰 Valor Real da NF (Opcional):", placeholder="Ex: 1250,00"
    )
