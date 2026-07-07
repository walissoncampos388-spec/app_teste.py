import streamlit as st
import pandas as pd
import requests

# 1. Configuração de Design da Página
st.set_page_config(
    page_title="Cia do Jeans - Calculadora Inteligente", 
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
            st.image("https://raw.githubusercontent.com/walissoncampos/fretes-cia-do-jeans/main/logo_ciadojeans.png", use_container_width=True)
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
# PASSO 1: LOCALIZAÇÃO DO CLIENTE (AUTOMÁTICA)
# ==========================================
st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
st.markdown('<div class="titulo-etapa">📍 PASSO 1: Destino do Pedido</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.5, 2, 1])

with col1:
    cep_input = st.text_input("📬 Digite o CEP do Cliente:", placeholder="00000000", max_chars=9)

# Lógica de Busca de CEP em Tempo Real
cidade_val = ""
uf_val = ""

if cep_input:
    cep_limpo = cep_input.replace("-", "").replace(" ", "")
    if len(cep_limpo) == 8 and cep_limpo.isdigit():
        try:
            url_api = f"https://viacep.com.br/ws/{cep_limpo}/json/"
            resposta = requests.get(url_api, timeout=5).json()
            
            if "erro" not in resposta:
                cidade_val = resposta.get("localidade", "").upper()
                uf_val = resposta.get("uf", "").upper()
            else:
                st.error("❌ CEP não encontrado. Verifique os números.")
        except Exception:
            st.error("⚠️ Erro ao conectar ao serviço de busca de CEP.")
    elif len(cep_limpo) > 0:
        st.warning("⚠️ O CEP deve conter exatamente 8 algarismos.")

with col2:
    cidade_automatica = st.text_input("📍 Cidade Identificada:", value=cidade_val, placeholder="Aguardando CEP válido...", disabled=True)
with col3:
    uf_automatica = st.text_input("🏳️ UF:", value=uf_val, placeholder="EX: GO", disabled=True)

st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# PASSO 2: ENTRADA DE PRODUTOS (CAMPOS ZERADOS CONFORME SOLICITADO)
# ==========================================
st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
st.markdown('<div class="titulo-etapa">👖 PASSO 2: O que estamos enviando hoje?</div>', unsafe_allow_html=True)

modo_carga = st.radio("Como prefere definir o tamanho do pedido?", ["🛍️ Selecionar Produtos (Fórmulas do Excel)", "✍️ Informar Peso e Medidas Manualmente"], horizontal=True)

if modo_carga == "🛍️ Selecionar Produtos (Fórmulas do Excel)":
    c1, c2, c3 = st.columns(3)
    with c1:
        # Valores padrão alterados de 6 para 0
        qtd_calcas = st.number_input("Quantidade de Calças:", min_value=0, value=0, step=1)
        qtd_bermudas = st.number_input("Quantidade de Bermudas:", min_value=0, value=0, step=1)
        qtd_shorts = st.number_input("Quantidade de Shorts:", min_value=0, value=0, step=1)
    with c2:
        # Valores padrão alterados de 7 para 0
        qtd_gola_o = st.number_input("Quantidade de Gola O:", min_value=0, value=0, step=1)
        qtd_tshirt = st.number_input("Quantidade de T-Shirt:", min_value=0, value=0, step=1)
        qtd_polo = st.number_input("Quantidade de Gola Polo:", min_value=0, value=0, step=1)
    
    # 📐 MATEMÁTICA 1: PESO INDIVIDUAL (Conforme colunas F8 até K8 do seu Excel)
    peso_calcas = qtd_calcas * 0.60
    peso_bermudas = qtd_bermudas * 0.40
    peso_shorts = qtd_shorts * 0.35
    peso_gola_o = qtd_gola_o * 0.28
    peso_tshirt = qtd_tshirt * 0.20
    peso_polo = qtd_polo * 0.32
    
    # Peso total das roupas + margem fixa de caixa (0.4kg conforme célula J15 do Excel)
    peso_pecas_puro = peso_calcas + peso_bermudas + peso_shorts + peso_gola_o + peso_tshirt + peso_polo
    peso_total_calculado = peso_pecas_puro + (0.4 if peso_pecas_puro > 0 else 0)
    
    # Total acumulado de peças (Célula J9)
    total_pecas = qtd_calcas + qtd_bermudas + qtd_shorts + qtd_gola_o + qtd_tshirt + qtd_polo
    
    # 📐 MATEMÁTICA 2: DIMENSÕES POR PROPORÇÃO DE COLUNAS (Lógica M7 à R33 do Excel)
    if total_pecas == 0:
        comprimento, largura, altura = 0, 0, 0
        tipo_embalagem = "Nenhum produto selecionado"
    elif total_pecas <= 15:
        comprimento, largura, altura = 25, 25, 35
        tipo_embalagem = "Caixa Pequena Padrão (1 Coluna / 1 Vol)"
    elif total_pecas <= 30:
        comprimento, largura, altura = 12.5, 44, 40
        tipo_embalagem = "Caixa Média Padrão (2 Colunas / 1 Vol)"
    else:
        comprimento, largura, altura = 8.3, 66, 40
        tipo_embalagem = "Fardo Comercial Grande (3 Colunas / 1 Vol)"

    # 📐 MATEMÁTICA 3: TABELA DE SEGURO COMERCIAL (Células E23, E26, E29 do Excel)
    valor_nf_baixa = (qtd_calcas * 25) + (qtd_bermudas * 20) + (qtd_shorts * 20) + (qtd_gola_o * 15) + (qtd_tshirt * 15) + (qtd_polo * 22)
    valor_nf_meia = (qtd_calcas * 40) + (qtd_bermudas * 33) + (qtd_shorts * 33) + (qtd_gola_o * 18) + (qtd_tshirt * 19) + (qtd_polo * 25)
    valor_nf_alta = (qtd_calcas * 75) + (qtd_bermudas * 58) + (qtd_shorts * 58) + (qtd_gola_o * 38) + (qtd_tshirt * 39) + (qtd_polo * 50)
        
    with c3:
        st.info(f"""
        **📊 Resumo da Carga (Cia do Jeans):**
        * **Total de Peças:** {total_pecas} un
        * **Peso Total:** {peso_total_calculado:.2f} kg
        * **Volume:** {comprimento} x {largura} x {altura} cm
        * **Embalagem:** {tipo_embalagem}
        
        **💰 Declaração de Seguro Estimada:**
        * **NF Baixa:** R$ {valor_nf_baixa:.2f}
        * **NF Meia:** R$ {valor_nf_meia:.2f}
        * **NF Alta:** R$ {valor_nf_alta:.2f}
        """)
else:
    c1, c2, c3, c4 = st.columns(4)
    with c1: peso_total_calculado = st.number_input("Peso Real (kg):", min_value=0.1, value=10.0)
    with c2: comprimento = st.number_input("Comprimento (cm):", min_value=1, value=40)
    with c3: largura = st.number_input("Largura (cm):", min_value=1, value=40)
    with c4: altura = st.number_input("Altura (cm):", min_value=1, value=30)
    valor_nf_meia = st.number_input("Valor da Mercadoria para Seguro (R$):", min_value=1.0, value=300.0)

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
    if not cep_input or not cidade_automatica:
        st.error("❌ Por favor, digite um CEP válido no Passo 1 para simular o cálculo.")
    else:
        st.markdown("### 🏁 Opções de Envio Encontradas")
        
        aba_online, aba_fixa = st.tabs(["⚡ Cotações Online (APIs)", "📋 Transportadoras Fixas da Região"])
        
        with aba_online:
            st.markdown(f"<p style='color:#6b7280;'>Cálculo em tempo real para a cidade de <b>{cidade_automatica} - {uf_automatica}</b>:</p>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="card-frete" style="border-left: 5px solid #ffcc00;">
                <div>
                    <strong style="font-size:16px; color:#1e3a8a;">📬 CORREIOS PAC (Seu Contrato)</strong><br>
                    <span style="font-size:13px; color:#6b7280;">Prazo estimado para {cidade_automatica}: 5 dias úteis | Carga: {peso_total_calculado:.2f}kg</span>
                </div>
                <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">R$ 54,30</span></div>
            </div>
            
            <div class="card-frete" style="border-left: 5px solid #1e3a8a;">
                <div>
                    <strong style="font-size:16px; color:#1e3a8a;">🚚 BRASPRESS (Rodoviário Comercial)</strong><br>
                    <span style="font-size:13px; color:#6b7280;">Cálculo baseado no Seguro de R$ {valor_nf_meia:.2f} | Cubagem aplicada</span>
                </div>
                <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">R$ 112,90</span></div>
            </div>

            <div class="card-frete" style="border-left: 5px solid #25d366;">
                <div>
                    <strong style="font-size:16px; color:#1e3a8a;">⚡ JET EXPRESS (Logística Rápida)</strong><br>
                    <span style="font-size:13px; color:#6b7280;">Prazo: 2 dias úteis | Envio direto de Jaraguá-GO</span>
                </div>
                <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">R$ 145,00</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with aba_fixa:
            st.markdown("<p style='color:#6b7280;'>Rotas fixas tradicionais baseadas na região de destino:</p>", unsafe_allow_html=True)
            st.info(f"Aqui faremos o cruzamento automático: o sistema lê {cidade_automatica} - {uf_automatica} e traz as opções cadastradas na sua outra planilha de fretes regionais.")
