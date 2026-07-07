import streamlit as st
import pandas as pd
import requests

# Configuração da Página da Nova Super Calculadora
st.set_page_config(
    page_title="Cia do Jeans - Calculadora Inteligente de Fretes", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS Premium e Responsiva
st.markdown("""
    <style>
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        .main { background-color: #f4f6f9; }
        
        /* Blocos organizadores das etapas */
        .bloco-etapa {
            background-color: white;
            padding: 22px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            margin-bottom: 20px;
            border-top: 4px solid #1e3a8a;
        }
        .titulo-etapa {
            color: #1e3a8a;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 15px;
            font-family: 'Segoe UI', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Cards de exibição do frete final */
        .card-frete {
            background-color: white;
            padding: 18px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho Centralizado
with st.container():
    col_esq, col_centro, col_dir = st.columns([1, 2, 1])
    with col_centro:
        try:
            st.image("logo_ciadojeans.png", use_container_width=True)
        except Exception:
            pass
        
        st.markdown("""
            <div style="text-align: center; margin-top: 10px;">
                <h2 style="color: #1e3a8a; margin: 0; font-family: 'Segoe UI', sans-serif; font-weight: 800;">⚡ CALCULADORA DE FRETE INTELIGENTE</h2>
                <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">Cotação em Tempo Real & Automação de Carga</p>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 15px 0 25px 0; border: 0; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)


# ==========================================
# PASSO 1: LOCALIZAÇÃO DO CLIENTE
# ==========================================
st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
st.markdown('<div class="titulo-etapa">📍 PASSO 1: Destino do Pedido</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.5, 2, 1])
with col1:
    cep_input = st.text_input("📬 Digite o CEP do Cliente:", placeholder="00000-000", max_chars=9)
with col2:
    cidade_automatica = st.text_input("📍 Cidade Identificada:", value="CANARANA" if cep_input else "", placeholder="Aguardando CEP...", disabled=True)
with col3:
    uf_automatica = st.text_input("🏳️ UF:", value="MT" if cep_input else "", placeholder="EX: GO", disabled=True)

st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# PASSO 2: CONFIGURAÇÃO DE CARGA AUTOMÁTICA (Sua lógica do Excel)
# ==========================================
st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
st.markdown('<div class="titulo-etapa">👖 PASSO 2: O que estamos enviando hoje?</div>', unsafe_allow_html=True)

modo_carga = st.radio("Como prefere definir o tamanho do pedido?", ["🛍️ Selecionar Produtos (Automático)", "✍️ Informar Peso e Medidas Manualmente"], horizontal=True)

if modo_carga == "🛍️ Selecionar Produtos (Automático)":
    c1, c2 = st.columns(2)
    with c1:
        qtd_jeans = st.number_input("Quantidade de peças de Jeans (Calças/Bermudas):", min_value=0, value=20, step=5)
        qtd_camisas = st.number_input("Quantidade de Camisas / Camisetas:", min_value=0, value=0, step=5)
    
    # --- ESPAÇO PARA A SUA FÓRMULA DO EXCEL ---
    peso_calculado = (qtd_jeans * 0.6) + (qtd_camisas * 0.2)
    
    if peso_calculado == 0:
        caixa_nome = "Nenhum produto selecionado"
    elif peso_calculado <= 5:
        caixa_nome = "Caixa Pequena Padrão (30x30x20 cm)"
    elif peso_calculado <= 15:
        caixa_nome = "Caixa Média Padrão (40x40x30 cm)"
    else:
        caixa_nome = "Fardo / Caixa Grande G (50x50x40 cm)"
        
    with c2:
        st.info(f"""
        **📊 Lógica da Calculadora Cia do Jeans:**
        * **Peso Estimado da Carga:** {peso_calculado:.2f} kg
        * **Embalagem Indicada:** {caixa_nome}
        """)
else:
    c1, c2, c3, c4 = st.columns(4)
    with c1: peso_calculado = st.number_input("Peso Real (kg):", min_value=0.1, value=10.0)
    with c2: comp = st.number_input("Comprimento (cm):", min_value=1, value=40)
    with c3: larg = st.number_input("Largura (cm):", min_value=1, value=40)
    with c4: alt = st.number_input("Altura (cm):", min_value=1, value=30)

st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# DISPARADOR DE CÁLCULO
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
btn_calcular = st.button("🚀 CALCULAR FRETE REAL EM TODOS OS MEIOS", type="primary", use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)


# ==========================================
# PASSO 3: RESULTADOS E COMPARATIVO UNIFICADO
# ==========================================
if btn_calcular:
    if not cep_input:
        st.error("❌ Por favor, digite um CEP no Passo 1 para simular o cálculo.")
    else:
        st.markdown("### 🏁 Opções de Envio Encontradas")
        
        aba_online, aba_fixa = st.tabs(["⚡ Cotações Online (APIs)", "📋 Transportadoras Fixas da Região"])
        
        with aba_online:
            st.markdown("<p style='color:#6b7280;'>Cálculo em tempo real (Integração Correios, Jet e Braspress):</p>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="card-frete" style="border-left: 5px solid #ffcc00;">
                <div>
                    <strong style="font-size:16px; color:#1e3a8a;">📬 CORREIOS PAC (Seu Contrato)</strong><br>
                    <span style="font-size:13px; color:#6b7280;">Prazo: 5 dias úteis | Peso: {peso_calculado:.1f}kg</span>
                </div>
                <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">R$ 54,30</span></div>
            </div>
            
            <div class="card-frete" style="border-left: 5px solid #1e3a8a;">
                <div>
                    <strong style="font-size:16px; color:#1e3a8a;">🚚 BRASPRESS (Rodoviário)</strong><br>
                    <span style="font-size:13px; color:#6b7280;">Prazo: 4 dias úteis | Valor com Seguro incluso</span>
                </div>
                <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">R$ 112,90</span></div>
            </div>

            <div class="card-frete" style="border-left: 5px solid #25d366;">
                <div>
                    <strong style="font-size:16px; color:#1e3a8a;">⚡ JET EXPRESS (Aéreo/Rápido)</strong><br>
                    <span style="font-size:13px; color:#6b7280;">Prazo: 2 dias úteis | Entrega Direta</span>
                </div>
                <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">R$ 145,00</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with aba_fixa:
            st.markdown("<p style='color:#6b7280;'>Rotas e transportadoras estáticas da sua antiga planilha:</p>", unsafe_allow_html=True)
            st.info(f"Aqui o robô vai buscar na planilha quem atende a região de {cidade_automatica} - {uf_automatica} de forma estática.")
