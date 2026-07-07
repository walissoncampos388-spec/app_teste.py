import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET

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

# ==========================================
# CREDENCIAIS DO SEU CONTRATO BRASPRESS
# ==========================================
# Substitua com os dados oficiais que o seu gerente da Braspress te passou:
BRASPRESS_CNPJ_REMETENTE = "00000000000000"  # CNPJ da Cia do Jeans (apenas números)
BRASPRESS_INSCRICAO_ESTADUAL = "00000000"     # Inscrição Estadual (apenas números)
CEP_ORIGEM = "76330000"                       # CEP de Jaraguá-GO

# Função oficial para calcular frete na API da Braspress
def calcular_frete_braspress(cep_destino, peso, valor_nf, comp, larg, alt):
    url_api = "https://www.braspress.com.br/wscalc/calculaFrete"
    
    # Monta os parâmetros necessários que o servidor da Braspress exige
    params = {
        "cnpjRemetente": BRASPRESS_CNPJ_REMETENTE,
        "ieRemetente": BRASPRESS_INSCRICAO_ESTADUAL,
        "cepOrigem": CEP_ORIGEM,
        "cepDestino": cep_destino,
        "cnpjDestinatario": BRASPRESS_CNPJ_REMETENTE, # Pode repetir o remetente para simulação física
        "modal": "R", # R = Rodoviário
        "tipoFrete": "1", # 1 = CIF / Pago na Origem
        "peso": str(peso),
        "valorAnf": f"{valor_nf:.2f}".replace(".", ","),
        "volume": "1",
        "cubagem": "0", # O sistema deles calcula pela dimensão se passarmos largura/altura abaixo
    }
    
    try:
        response = requests.get(url_api, params=params, timeout=8)
        if response.status_code == 200:
            # A Braspress responde em formato XML. Vamos ler a resposta:
            root = ET.fromstring(response.content)
            vlr_frete = root.find(".//vlrFrete")
            prazo = root.find(".//prazoEntrega")
            erro = root.find(".//erro")
            
            if erro is not None and erro.text != "0":
                msg_erro = root.find(".//msgErro")
                return {"sucesso": False, "msg": msg_erro.text if msg_erro is not None else "Erro na Braspress"}
                
            if vlr_frete is not None:
                return {
                    "sucesso": True, 
                    "preco": float(vlr_frete.text.replace(",", ".")), 
                    "prazo": prazo.text if prazo is not None else "-"
                }
    except Exception as e:
        return {"sucesso": False, "msg": f"Instabilidade na conexão: {str(e)}"}
    
    return {"sucesso": False, "msg": "Não foi possível obter resposta da Braspress."}

# Cabeçalho Centralizado
with st.container():
    col_esq, col_centro, col_dir = st.columns([1, 2, 1])
    with col_centro:
        try:
            st.image("https://raw.githubusercontent.com/walissoncampos/fretes-cia-do-jeans/main/logo_ciadojeans.png", use_container_width=True)
        except Exception:
            pass
        st.markdown("<div style='text-align: center; margin-top: 10px;'><h2 style='color: #1e3a8a; margin: 0; font-family: sans-serif; font-weight: 800;'>⚡ CALCULADORA DE FRETE INTELIGENTE</h2></div>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 15px 0 25px 0; border: 0; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

# PASSO 1: LOCALIZAÇÃO DO CLIENTE (AUTOMÁTICA)
st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
st.markdown('<div class="titulo-etapa">📍 PASSO 1: Destino do Pedido</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.5, 2, 1])
with col1:
    cep_input = st.text_input("📬 Digite o CEP do Cliente:", placeholder="00000000", max_chars=9)

cidade_val, uf_val = "", ""
if cep_input:
    cep_limpo = cep_input.replace("-", "").replace(" ", "")
    if len(cep_limpo) == 8 and cep_limpo.isdigit():
        try:
            resposta = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5).json()
            if "erro" not in resposta:
                cidade_val = resposta.get("localidade", "").upper()
                uf_val = resposta.get("uf", "").upper()
            else:
                st.error("❌ CEP não encontrado.")
        except Exception:
            pass

with col2: cidade_automatica = st.text_input("📍 Cidade Identificada:", value=cidade_val, disabled=True)
with col3: uf_automatica = st.text_input("🏳️ UF:", value=uf_val, disabled=True)
st.markdown('</div>', unsafe_allow_html=True)

# PASSO 2: ENTRADA DE PRODUTOS
st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
st.markdown('<div class="titulo-etapa">👖 PASSO 2: O que estamos enviando hoje?</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    qtd_calcas = st.number_input("Quantidade de Calças:", min_value=0, value=0, step=1)
    qtd_bermudas = st.number_input("Quantidade de Bermudas:", min_value=0, value=0, step=1)
    qtd_shorts = st.number_input("Quantidade de Shorts:", min_value=0, value=0, step=1)
with c2:
    qtd_gola_o = st.number_input("Quantidade de Gola O:", min_value=0, value=0, step=1)
    qtd_tshirt = st.number_input("Quantidade de T-Shirt:", min_value=0, value=0, step=1)
    qtd_polo = st.number_input("Quantidade de Gola Polo:", min_value=0, value=0, step=1)

# Matemática do seu Excel
peso_total_calculado = (qtd_calcas * 0.60) + (qtd_bermudas * 0.40) + (qtd_shorts * 0.35) + (qtd_gola_o * 0.28) + (qtd_tshirt * 0.20) + (qtd_polo * 0.32)
if peso_total_calculado > 0: peso_total_calculado += 0.4

total_pecas = qtd_calcas + qtd_bermudas + qtd_shorts + qtd_gola_o + qtd_tshirt + qtd_polo
if total_pecas == 0: comprimento, largura, altura, tipo_embalagem = 0, 0, 0, "Vazio"
elif total_pecas <= 15: comprimento, largura, altura, tipo_embalagem = 25, 25, 35, "Caixa P"
elif total_pecas <= 30: comprimento, largura, altura, tipo_embalagem = 12.5, 44, 40, "Caixa M"
else: comprimento, largura, altura, tipo_embalagem = 8.3, 66, 40, "Fardo G"

valor_nf_meia = (qtd_calcas * 40) + (qtd_bermudas * 33) + (qtd_shorts * 33) + (qtd_gola_o * 18) + (qtd_tshirt * 19) + (qtd_polo * 25)

with c3:
    valor_manual_nf = st.number_input("✍️ Valor Real da NF (Opcional):", min_value=0.0, value=0.0, step=50.0)
    valor_para_seguro = valor_manual_nf if valor_manual_nf > 0 else valor_nf_meia
    
    st.info(f"** Resumo:** {total_pecas} peças | {peso_total_calculado:.2f} kg | Seguro: R$ {valor_para_seguro:.2f}")
st.markdown('</div>', unsafe_allow_html=True)

# DISPARADOR
btn_calcular = st.button("🚀 CALCULAR FRETE REAL EM TODOS OS MEIOS", type="primary", use_container_width=True)

# PASSO 3: RESULTADOS
if btn_calcular:
    if not cep_input or not cidade_automatica:
        st.error("❌ Digite um CEP válido.")
    else:
        st.markdown("### 🏁 Opções de Envio Encontradas")
        aba_online, aba_fixa = st.tabs(["⚡ Cotações Online (APIs)", "📋 Transportadoras Fixas da Região"])
        
        with aba_online:
            cep_limpo = cep_input.replace("-", "").replace(" ", "")
            
            with st.spinner("Consultando tabela contratual na Braspress..."):
                # EXECUTA A CHAMADA REAL DA API DA BRASPRESS
                res_braspress = calcular_frete_braspress(cep_limpo, peso_total_calculado, valor_para_seguro, comprimento, largura, altura)
            
            # 1. Card Físico da Braspress (Dinâmico)
            if res_braspress["sucesso"]:
                st.markdown(f"""
                <div class="card-frete" style="border-left: 5px solid #1e3a8a;">
                    <div>
                        <strong style="font-size:16px; color:#1e3a8a;">🚚 BRASPRESS (Seu Contrato Oficial)</strong><br>
                        <span style="font-size:13px; color:#6b7280;">Prazo de entrega: {res_braspress['prazo']} dias úteis | Rodoviário Comercial</span>
                    </div>
                    <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">R$ {res_braspress['preco']:.2f}</span></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"❌ Braspress: {res_braspress['msg']} (Verifique se o CNPJ/IE remetente estão preenchidos corretamente no código).")
            
            # Outros meios (Simulados até integrarmos os tokens deles)
            st.markdown(f"""
            <div class="card-frete" style="border-left: 5px solid #ffcc00;">
                <div><strong style="font-size:16px; color:#1e3a8a;">📬 CORREIOS PAC</strong><br><span style="font-size:13px; color:#6b7280;">Aguardando credenciais do contrato</span></div>
                <div style="text-align: right;"><span style="font-size:16px; color:#6b7280;">Em breve</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with aba_fixa:
            st.info("Segunda aba integrada à planilha regional.")
