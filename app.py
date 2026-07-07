import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import urllib.parse

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

# ==========================================
# CONFIGURAÇÕES DE CREDENCIAIS E INTEGRACAO
# ==========================================
BRASPRESS_CNPJ_CIA_DO_JEANS = "34835571000168"  # CNPJ Cia do Jeans (Tomador)
BRASPRESS_INSCRICAO_ESTADUAL = "107873130"     # Sua Inscrição Estadual de GO
CEP_ORIGEM = "76330000"                       # CEP de Jaraguá-GO

# Novo Token de Desenvolvedor do SuperFrete Atualizado
SUPERFRETE_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3ODM0MzgwMTAsInN1YiI6IkROakhlMVJiVDJWMmx2eFZvZ1NOOHRyV3VHdjIifQ.M3vXT0qnHNENR_rEGcm3-o5E_KjVLVUDhtAvQoiyhoI"

def calcular_frete_braspress(cep_destino, peso, valor_nf, cnpj_parceiro=""):
    url_api = "https://www.braspress.com.br/wscalc/calculaFrete.faw"
    cnpj_remetente_final = cnpj_parceiro.replace(".", "").replace("-", "").replace("/", "").strip()
    
    if not cnpj_remetente_final:
        cnpj_remetente_final = BRASPRESS_CNPJ_CIA_DO_JEANS
        ie_remetente_final = BRASPRESS_INSCRICAO_ESTADUAL
        cnpj_destinatario_final = "00000000000100"
    else:
        ie_remetente_final = "ISENTO"
        cnpj_destinatario_final = BRASPRESS_CNPJ_CIA_DO_JEANS

    params = {
        "cnpjRemetente": cnpj_remetente_final,
        "ieRemetente": ie_remetente_final,
        "cepOrigem": CEP_ORIGEM,
        "cepDestino": cep_destino.replace("-", "").strip(),
        "cnpjDestinatario": cnpj_destinatario_final, 
        "modal": "R", "tipoFrete": "2", "cnpjTomador": BRASPRESS_CNPJ_CIA_DO_JEANS, 
        "peso": str(peso), "valorAnf": f"{valor_nf:.2f}".replace(".", ","), "volume": "1", "cubagem": "0",
    }
    
    try:
        response = requests.get(url_api, params=params, timeout=6)
        if response.status_code == 200:
            texto_resposta = response.text.strip()
            if texto_resposta.startswith("<html") or texto_resposta.startswith("<!DOCTYPE html"):
                return {"sucesso": False, "msg": "API antiga desativada (Aguardando nova integração REST da Braspress)."}
            root = ET.fromstring(response.content)
            vlr_frete = root.find(".//vlrFrete")
            prazo = root.find(".//prazoEntrega")
            if vlr_frete is not None:
                return {"sucesso": True, "preco": float(vlr_frete.text.replace(",", ".")), "prazo": prazo.text if prazo is not None else "-"}
        elif response.status_code == 404:
            return {"sucesso": False, "msg": "API antiga desativada (Aguardando nova integração REST da Braspress)."}
    except Exception:
        pass
    return {"sucesso": False, "msg": "Serviço online indisponível. Veja os Correios ou fretes fixos regionais."}


def calcular_frete_superfrete(cep_destino, peso, comprimento, largura, altura, valor_nf):
    url_api = "https://api.superfrete.com/v1/calculator"
    
    headers = {
        "Authorization": f"Bearer {SUPERFRETE_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    payload = {
        "from": {
            "postal_code": CEP_ORIGEM
        },
        "to": {
            "postal_code": cep_destino.replace("-", "").strip()
        },
        "services": "1,2", # 1 = SEDEX, 2 = PAC
        "options": {
            "receipt": False,
            "own_hand": False,
            "insurance": True,
            "declared_value": float(valor_nf)
        },
        "package": {
            "weight": float(peso),
            "width": float(largura),
            "height": float(altura),
            "length": float(comprimento),
            "format": "box"
        }
    }
    
    try:
        response = requests.post(url_api, json=payload, headers=headers, timeout=8)
        
        if response.status_code == 200:
            texto = response.text.strip()
            if texto.startswith("<html") or texto.startswith("<!DOCTYPE html"):
                return {"sucesso": False, "msg": "O painel do SuperFrete retornou uma página de erro temporária."}
            return {"sucesso": True, "dados": response.json()}
        else:
            return {"sucesso": False, "msg": f"Erro na API SuperFrete (Status: {response.status_code}). Certifique-se de preencher CEP e produtos corretamente."}
    except Exception as e:
        return {"sucesso": False, "msg": "Instabilidade temporária na conexão do SuperFrete."}


# CACHE ULTRA-RÁPIDO: Organização dos dados da planilha de fretes fixos
@st.cache_data(ttl=3600)
def carregar_e_limpar_dados():
    try:
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
                    'CIDADE': cidade, 'UF': uf, 'TRANSPORTADORA': t_name,
                    'ROTA_ENVIO': buscar(env_col), 'FONE': buscar(fon_col),
                    'PRAZO': buscar(prz_col), 'TIPO_FRETE': buscar(frt_col),
                    'EXIGE_NF': buscar(nf_col), 'VALOR_MINIMO': buscar(val_col)
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
        st.markdown("<h2 style='text-align:center; color:#1e3a8a; font-family:sans-serif; font-weight:800; margin:0;'>⚡ CALCULADORA DE FRETE INTELIGENTE</h2>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 15px 0 25px 0; border: 0; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

# ==========================================
# PASSO 1: LOCALIZAÇÃO DO CLIENTE
# ==========================================
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

with col2: cidade_automatica = st.text_input("📍 Cidade Identificada:", value=cidade_val, placeholder="Aguardando CEP...", disabled=True)
with col3: uf_automatica = st.text_input("🏳️ UF:", value=uf_val, placeholder="EX: GO", disabled=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PASSO 2: ENTRADA DE PRODUTOS
# ==========================================
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

# Matemática de Pesos e Cubagem
peso_pecas_puro = (qtd_calcas * 0.60) + (qtd_bermudas * 0.40) + (qtd_shorts * 0.35) + (qtd_gola_o * 0.28) + (qtd_tshirt * 0.20) + (qtd_polo * 0.32)
peso_total_calculado = peso_pecas_puro + (0.4 if peso_pecas_puro > 0 else 0)
total_pecas = qtd_calcas + qtd_bermudas + qtd_shorts + qtd_gola_o + qtd_tshirt + qtd_polo

if total_pecas == 0: comprimento, largura, altura, tipo_embalagem = 0, 0, 0, "Nenhum produto"
elif total_pecas <= 15: comprimento, largura, altura, tipo_embalagem = 25, 25, 35, "Caixa Pequena"
elif total_pecas <= 30: comprimento, largura, altura, tipo_embalagem = 12.5, 44, 40, "Caixa Média"
else: comprimento, largura, altura, tipo_embalagem = 8.3, 66, 40, "Fardo Comercial"

valor_nf_meia = (qtd_calcas * 40) + (qtd_bermudas * 33) + (qtd_shorts * 33) + (qtd_gola_o * 18) + (qtd_tshirt * 19) + (qtd_polo * 25)

with c3:
    cnpj_fornecedor_parceiro = st.text_input("🏢 CNPJ do Fornecedor/Parceiro (Opcional):", placeholder="Usar padrão Cia do Jeans")
    valor_manual_nf = st.number_input("✍️ Valor Real da NF (Opcional):", min_value=0.0, value=0.0, step=50.0)
    valor_para_seguro = valor_manual_nf if valor_manual_nf > 0 else valor_nf_meia
    
    st.info(f"**📊 Resumo:** {total_pecas} un | {peso_total_calculado:.2f} kg\n* **Embalagem:** {tipo_embalagem}\n* **Seguro:** R$ {valor_para_seguro:.2f}")
st.markdown('</div>', unsafe_allow_html=True)

# DISPARADOR DE CÁLCULO
st.markdown("<br>", unsafe_allow_html=True)
btn_calcular = st.button("🚀 CALCULAR FRETE REAL EM TODOS OS MEIOS", type="primary", use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# PASSO 3: RESULTADOS
# ==========================================
if btn_calcular:
    if not cep_input or not cidade_automatica:
        st.error("❌ Por favor, digite um CEP válido no Passo 1.")
    elif total_pecas == 0:
        st.error("❌ Insira a quantidade de produtos no Passo 2 para poder calcular.")
    else:
        st.markdown("### 🏁 Opções de Envio Encontradas")
        aba_online, aba_fixa = st.tabs(["⚡ Cotações Online (APIs)", "📋 Transportadoras Fixas da Região"])
        
        opcoes_whatsapp = []
        
        with aba_online:
            # 1. CONSULTA BRASPRESS
            with st.spinner("Consultando Braspress..."):
                res_braspress = calcular_frete_braspress(cep_input, peso_total_calculado, valor_para_seguro, cnpj_fornecedor_parceiro)
            if res_braspress["sucesso"]:
                preco_bp = f"R$ {res_braspress['preco']:.2f}"
                st.markdown(f"""
                <div class="card-frete" style="border-left: 5px solid #1e3a8a;">
                    <div><strong style="font-size:16px; color:#1e3a8a;">🚚 BRASPRESS (Contrato Cia do Jeans)</strong><br><span style="font-size:13px; color:#6b7280;">Prazo: {res_braspress['prazo']} dias úteis</span></div>
                    <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">{preco_bp}</span></div>
                </div>
                """, unsafe_allow_html=True)
                opcoes_whatsapp.append(f"🚛 *BRASPRESS*\n💰 Valor: {preco_bp}\n⏱️ Prazo: {res_braspress['prazo']} dias úteis\n")
            else:
                st.info(f"ℹ️ Braspress: {res_braspress['msg']}")
                
            # 2. CONSULTA SUPERFRETE (CORREIOS PAC E SEDEX)
            with st.spinner("Consultando Correios via SuperFrete..."):
                res_sf = calcular_frete_superfrete(cep_input, peso_total_calculado, comprimento, largura, altura, valor_para_seguro)
            
            if res_sf["sucesso"]:
                dados_correios = res_sf["dados"]
                for servico in dados_correios:
                    nome_comercial = str(servico.get("name", "")).upper()
                    if servico.get("error"):
                        continue
                    
                    preco_f = float(servico.get("price", 0))
                    prazo_f = servico.get("delivery", "-")
                    
                    if "SEDEX" in nome_comercial:
                        st.markdown(f"""
                        <div class="card-frete" style="border-left: 5px solid #ffcc00;">
                            <div><strong style="font-size:16px; color:#1e3a8a;">📬 CORREIOS SEDEX (SuperFrete Desconto)</strong><br><span style="font-size:13px; color:#6b7280;">Prazo: {prazo_f} dias úteis | Entrega Expressa</span></div>
                            <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">R$ {preco_f:.2f}</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                        opcoes_whatsapp.append(f"📬 *CORREIOS SEDEX*\n💰 Valor: R$ {preco_f:.2f}\n⏱️ Prazo: {prazo_f} dias úteis\n")
                    
                    elif "PAC" in nome_comercial:
                        st.markdown(f"""
                        <div class="card-frete" style="border-left: 5px solid #0056b3;">
                            <div><strong style="font-size:16px; color:#1e3a8a;">📬 CORREIOS PAC (SuperFrete Desconto)</strong><br><span style="font-size:13px; color:#6b7280;">Prazo: {prazo_f} dias úteis | Entrega Normal</span></div>
                            <div style="text-align: right;"><span style="font-size:20px; font-weight:700; color:#111827;">R$ {preco_f:.2f}</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                        opcoes_whatsapp.append(f"📬 *CORREIOS PAC*\n💰 Valor: R$ {preco_f:.2f}\n⏱️ Prazo: {prazo_f} dias úteis\n")
            else:
                st.warning(f"⚠️ Correios (SuperFrete): {res_sf['msg']}")
            
        with aba_fixa:
            if df_fretes_fixos.empty:
                st.warning("⚠️ Planilha 'SISTEMA_DE_FRETES_AUTOMATIZADO.xlsx' não encontrada.")
            else:
                resultados_fixos = df_fretes_fixos[(df_fretes_fixos['CIDADE'] == cidade_automatica) & (df_fretes_fixos['UF'] == uf_automatica)]
                if not resultados_fixos.empty:
                    for idx, row in resultados_fixos.iterrows():
                        prazo = str(row['PRAZO'])
                        if "cotar" not in prazo.lower() and "dias" not in prazo.lower() and prazo != '-': 
                            prazo = f"{prazo} Dias"
                            
                        st.markdown(f"""
                        <div class="card-frete" style="border-left: 5px solid #4b5563;">
                            <div>
                                <strong style="font-size:16px; color:#1e3a8a;"><b>🚛 {row['TRANSPORTADORA']}</b></strong><br>
                                <span style="font-size:13px; color:#4b5563;">📍 Rota: {row['ROTA_ENVIO']} | 📞 Fone: {row['FONE']}</span><br>
                                <span style="font-size:12px; color:#6b7280;">⏱️ Prazo: {prazo} | 📄 Exige NF: {row['EXIGE_NF']}</span>
                            </div>
                            <div style="text-align: right;"><span style="font-size:13px; color:#6b7280; font-weight:600;">Mínimo</span><br><span style="font-size:18px; font-weight:700; color:#111827;">R$ {row['VALOR_MINIMO']}</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        opcoes_whatsapp.append(
                            f"🚛 *{row['TRANSPORTADORA']}*\n"
                            f"💰 Mínimo: R$ {row['VALOR_MINIMO']}\n"
                            f"⏱️ Prazo: {prazo}\n"
                            f"📞 Contato: {row['FONE']}\n"
                        )
                else: 
                    st.warning(f"Nenhuma transportadora cadastrada no Excel regional para {cidade_automatica}-{uf_automatica}.")

        # ==========================================
        # PASSO 4: GERADOR E BOTÃO DO WHATSAPP
        # ==========================================
        st.markdown("<br><hr style='border-top: 1px dashed #cbd5e1;'><br>", unsafe_allow_html=True)
        st.markdown('<div class="bloco-etapa" style="border-top: 4px solid #25d366;">', unsafe_allow_html=True)
        st.markdown('<div class="titulo-etapa" style="color: #25d366;">💬 PASSO 4: Enviar Cotação ao Cliente</div>', unsafe_allow_html=True)
        
        texto_opcoes = "\n".join(opcoes_whatsapp) if opcoes_whatsapp else "• Nenhuma opção localizada."
        
        mensagem_vendedor = (
            f"Olá! Segue a cotação de frete para o seu pedido da *Cia do Jeans*:\n\n"
            f"📍 *Destino:*\n{cidade_automatica} - {uf_automatica}\n\n"
            f"📦 *Volume estimado:*\n{total_pecas} peças ({peso_total_calculado:.2f} kg)\n\n"
            f"🛍️ *Embalagem:*\n{tipo_embalagem}\n\n"
            f"-----------------------------------------\n"
            f"🚚 *OPÇÕES DE ENVIO:*\n\n"
            f"{texto_opcoes}"
            f"-----------------------------------------\n\n"
            f"_Qual destas opções fica melhor para fazermos o despacho?_"
        )
        
        texto_editavel = st.text_area("Pré-visualização da Mensagem:", value=mensagem_vendedor, height=250)
        texto_codificado = urllib.parse.quote(texto_editavel)
        link_whatsapp = f"https://api.whatsapp.com/send?text={texto_codificado}"
        
        st.markdown(f"""
            <a href="{link_whatsapp}" target="_blank" style="text-decoration: none;">
                <div style="background-color: #25d366; color: white; text-align: center; padding: 14px; border-radius: 8px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 10px rgba(37,211,102,0.3); cursor: pointer;">
                    📲 ENVIAR COTAÇÃO PARA O WHATSAPP DO CLIENTE
                </div>
            </a>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
