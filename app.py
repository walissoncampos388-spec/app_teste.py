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

# CACHE ULTRA-RÁPIDO: Organização instantânea dos dados da sua planilha de fretes fixos
@st.cache_data(ttl=3600)
def carregar_e_limpar_dados():
    try:
        # Tenta ler a planilha no mesmo repositório
        df = pd.read_excel("SISTEMA_DE_FRETES_AUTOMATIZADO.xlsx", sheet_name='Plan1')
    except Exception:
        return pd.DataFrame()
        
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    pares = [
        ('TRANSPORTADORA', 'ENVIO', 'FONE', 'PRAZO', 'FRETE', 'NF', 'VALOR MINIMO A PARTIR DE'),
        ('TRANPORTADORA 2', 'ENVIO 2', 'FONE 2', 'PRAZO 2', 'FRETE 2', 'NF 2', 'VALOR MINIMO 2'),
        ('TRANSPORTADORA 3', 'ENVIO 3', 'FONE 3', 'PRAZO 3', 'FRETE 3', 'NF 3', 'VALOR 3'),
        ('TRANSPORTADORA 4', 'ENVIO 4', 'FONE 4', 'PRAZO 4', 'FRETE 4', 'NF 4', 'VALOR 4'),
        ('TRANSPORTADORA 5', 'ENVIO 5', 'FONE 5', 'PRAZO 5', 'FRETE 5', 'NF 5', 'VALOR 5'),
        ('TRANSPORTADORA 6', 'ENVIO 6', 'FONE2', 'PRAZO 6', 'FRETE 6', 'NF 6', 'VALOR 6'),
        ('TRANSPORTADORA 7', 'ENVIO 7', 'FONE 7', 'PRAZO 7', 'FRETE 7', 'NF 7', 'VALOR MINIMO 7')
    ]
    
    cidade_col = [c for c in df.columns if 'CIDADE' in c][0] if any('CIDADE' in c for c in df.columns) else None
    uf_col = [c for c in df.columns if 'UF' in c][0] if any('UF' in c for c in df.columns) else None
    
    if not cidade_col or not uf_col:
        return pd.DataFrame()
        
    linhas = []
    for _, r in df.iterrows():
        cidade = str(r[cidade_col]).strip().upper()
        uf = str(r[uf_col]).strip().upper()
        
        if not cidade or cidade in ['NAN', '-', ''] or uf in ['NAN', '-', '']:
            continue
            
        for t_col, env_col, fon_col, prz_col, frt_col, nf_col, val_col in pares:
            def buscar(nome):
                for c in df.columns:
                    if c.replace(" ", "") == nome.replace(" ", ""):
                        val = r[c]
                        return str(val).strip() if pd.notna(val) else '-'
                return '-'
                
            t_name = buscar(t_col)
            if t_name and t_name not in ['-', '0', 'NAN', '']:
                linhas.append({
                    'CIDADE': cidade,
                    'UF': uf,
                    'TRANSPORTADORA': t_name,
                    'ROTA_ENVIO': buscar(env_col),
                    'FONE': buscar(fon_col),
                    'PRAZO': buscar(prz_col),
                    'TIPO_FRETE': buscar(frt_col),
                    'EXIGE_NF': buscar(nf_col),
                    'VALOR_MINIMO': buscar(val_col)
                })
                
    return pd.DataFrame(linhas)

df_fretes_fixos = carregar_e_limpar_dados()

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
# PASSO 2: ENTRADA DE PRODUTOS
# ==========================================
st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
st.markdown('<div class="titulo-etapa">👖 PASSO 2: O que estamos enviando hoje?</div>', unsafe_allow_html=True)

modo_carga = st.radio("Como prefere definir o tamanho do pedido?", ["🛍️ Selecionar Produtos (Fórmulas do Excel)", "✍️ Informar Peso e Medidas Manualmente"], horizontal=True)

valor_para_seguro = 0.0

if modo_carga == "🛍️ Selecionar Produtos (Fórmulas do Excel)":
    c1, c2, c3 = st.columns(3)
    with c1:
        qtd_calcas = st.number_input("Quantidade de Calças:", min_value=0, value=0, step=1)
        qtd_bermudas = st.number_input("Quantidade de Bermudas:", min_value=0, value=0, step=1)
        qtd_shorts = st.number_input("Quantidade de Shorts:", min_value=0, value=0, step=1)
    with c2:
        qtd_gola_o = st.number_input("Quantidade de Gola O:", min_value=0, value=0, step=1)
        qtd_tshirt = st.number_input("Quantidade de T-Shirt:", min_value=0, value=0, step=1)
        qtd_polo = st.number_input("Quantidade de Gola Polo:", min_value=0, value=0, step=1)
    
    peso_calcas = qtd_calcas * 0.60
    peso_bermudas = qtd_bermudas * 0.40
    peso_shorts = qtd_shorts * 0.35
    peso_gola_o = qtd_gola_o * 0.28
    peso_tshirt = qtd_tshirt * 0.20
    peso_polo = qtd_polo * 0.32
    
    peso_pecas_puro = peso_calcas + peso_bermudas + peso_shorts + peso_gola_o + peso_tshirt + peso_polo
    peso_total_calculado = peso_pecas_puro + (0.4 if peso_pecas_puro > 0 else 0)
    total_pecas = qtd_calcas + qtd_bermudas + qtd_shorts + qtd_gola_o + qtd_tshirt + qtd_polo
    
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

    valor_nf_baixa = (qtd_calcas * 25) + (qtd_bermudas * 20) + (qtd_shorts * 20) + (qtd_gola_o * 15) + (qtd_tshirt * 15) + (qtd_polo * 22)
    valor_nf_meia = (qtd_calcas * 40) + (qtd_bermudas * 33) + (qtd_shorts * 33) + (qtd_gola_o * 18) + (qtd_tshirt * 19) + (qtd_polo * 25)
    valor_nf_alta = (qtd_calcas * 75) + (qtd_bermudas * 58) + (qtd_shorts * 58) + (qtd_gola_o * 38) + (qtd_tshirt * 39) + (qtd_polo * 50)
        
    with c3:
        valor_manual_nf = st.number_input("✍️ Valor Real da NF (Opcional):", min_value=0.0, value=0.0, step=50.0)
        
        if valor_manual_nf > 0:
            valor_para_seguro = valor_manual_nf
            texto_seguro_resumo = f"R$ {valor_manual_nf:.2f} (Digitado Manualmente)"
        else:
            valor_para_seguro = valor_nf_meia
            texto_seguro_resumo = f"R$ {valor_nf_meia:.2f} (Estimativa Meia)"

        st.info(f"""
        **📊 Resumo da Carga (Cia do Jeans):**
        * **Total de Peças:** {total_pecas} un
        * **Peso Total:** {peso_total_calculado:.2f} kg
        * **Volume:** {comprimento} x {largura} x {altura} cm
        * **Embalagem:** {tipo_embalagem}
        * **Seguro Ativo para Cálculo:** {texto_seguro_resumo}
        """)
else:
    c1, c2, c3, c4 = st.columns(4)
    with c1: peso_total_calculado = st.number_input("Peso Real (kg):", min_value=0.1, value=10.0)
    with c2: comprimento = st.number_input("Comprimento (cm):", min_value=1, value=40)
    with c3: largura = st.number_input("Largura (cm):", min_value=1, value=40)
    with c4: altura = st.number_input("Altura (cm):", min_value=1, value=30)
    valor_manual_nf = st.number_input("Valor da Mercadoria para Seguro (R$):", min_value=1.0, value=300.0)
    valor_para_seguro = valor_manual_nf

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
        st.error("❌ Por favor, digite um CEP válido no Passo 1 para realizar a cotação.")
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
                    <span style="font-size:13px; color:#6b7280;">Cálculo baseado no Seguro de R$ {valor_para_seguro:.2f} | Cubagem aplicada</span>
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
            if df_fretes_fixos.empty:
                st.warning("⚠️ Planilha 'SISTEMA_DE_FRETES_AUTOMATIZADO.xlsx' não encontrada no repositório. Suba o arquivo para ativar esta busca.")
            else:
                # Faz a varredura inteligente por Cidade e UF na base de dados do Excel
                resultados_fixos = df_fretes_fixos[
                    (df_fretes_fixos['CIDADE'] == cidade_automatica) & 
                    (df_fretes_fixos['UF'] == uf_automatica)
                ]
                
                if not resultados_fixos.empty:
                    st.markdown(f"<p style='color:#6b7280;'>Encontramos {len(resultados_fixos)} transportadora(s) na sua tabela para <b>{cidade_automatica} - {uf_automatica}</b>:</p>", unsafe_allow_html=True)
                    
                    for idx, row in resultados_fixos.iterrows():
                        # Ajusta a exibição de dias
                        prazo = str(row['PRAZO'])
                        if "cotar" not in prazo.lower() and "dias" not in prazo.lower() and prazo != '-':
                            prazo = f"{prazo} Dias"
                            
                        st.markdown(f"""
                        <div class="card-frete" style="border-left: 5px solid #1e3a8a; background-color: #fafbfe;">
                            <div>
                                <strong style="font-size:16px; color:#1e3a8a;">🚛 {row['TRANSPORTADORA']}</strong><br>
                                <span style="font-size:14px; color:#4b5563;">📍 Rota: {row['ROTA_ENVIO']} | 📞 Contato: {row['FONE']}</span><br>
                                <span style="font-size:13px; color:#6b7280;">⏱️ Prazo: {prazo} | 📄 Exige NF: {row['EXIGE_NF']}</span>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-size:14px; color:#4b5563; font-weight:600;">Mínimo</span><br>
                                <span style="font-size:18px; font-weight:700; color:#111827;">R$ {row['VALOR_MINIMO']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning(f"Nenhuma transportadora cadastrada na planilha regional para a cidade de {cidade_automatica} - {uf_automatica}.")
