import streamlit as st
import pandas as pd
import requests
import urllib.parse
import base64

# 1. Configuração de Design da Página
st.set_page_config(
    page_title="Cia do Jeans - Calculadora Inteligente", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CONTROLE DE NAVEGAÇÃO À PROVA DE REFRESH (SESSION STATE) - Inicializado no topo
if "tela_ativa" not in st.session_state:
    st.session_state.tela_ativa = "cotacao"
if "cidade_input_fiel" not in st.session_state:
    st.session_state["cidade_input_fiel"] = ""
if "uf_input_fiel" not in st.session_state:
    st.session_state["uf_input_fiel"] = ""
if "rastreio_gerado" not in st.session_state:
    st.session_state["rastreio_gerado"] = False

# Funções de clique rápido para limpar o delay do double-click
def mudar_para_cotacao():
    st.session_state.tela_ativa = "cotacao"

def mudar_para_rastreio():
    st.session_state.tela_ativa = "rastreio"

# Estilização CSS baseada no Padrão UniLog (Paleta: #2c3e50, #3498db, #27ae60, #f0f2f5)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700;800&display=swap');
        
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f0f2f5 !important;
            font-family: 'Segoe UI', Roboto, sans-serif !important;
            color: #333333;
        }
        
        /* Blocos organizadores das etapas (Estilo Card UniLog) */
        .bloco-etapa {
            background-color: #ffffff;
            padding: 24px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.06);
            margin-bottom: 24px;
            border-top: 4px solid #3498db;
        }
        .titulo-etapa {
            color: #2c3e50;
            font-size: 17px;
            font-weight: 700;
            margin-bottom: 18px;
            font-family: 'Segoe UI', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Cards de exibição do frete final */
        .card-frete {
            background-color: #ffffff;
            padding: 18px 22px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.04);
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #f0f0f0;
        }
        
        /* Estilização das Abas Superiores */
        div.stButton > button[key="aba_cot_btn"] {
            background-color: """ + ("#2c3e50" if st.session_state.tela_ativa == "cotacao" else "#ffffff") + """ !important;
            color: """ + ("#ffffff" if st.session_state.tela_ativa == "cotacao" else "#7f8c8d") + """ !important;
            font-weight: 700 !important;
            border: """ + ("none" if st.session_state.tela_ativa == "cotacao" else "1px solid #e0e0e0") + """ !important;
            padding: 14px !important;
            border-radius: 50px !important;
            width: 100% !important;
            box-shadow: """ + ("0 4px 15px rgba(44,62,80,0.2)" if st.session_state.tela_ativa == "cotacao" else "none") + """ !important;
            transition: all 0.3s ease !important;
        }
        div.stButton > button[key="aba_ras_btn"] {
            background-color: """ + ("#2c3e50" if st.session_state.tela_ativa == "rastreio" else "#ffffff") + """ !important;
            color: """ + ("#ffffff" if st.session_state.tela_ativa == "rastreio" else "#7f8c8d") + """ !important;
            font-weight: 700 !important;
            border: """ + ("none" if st.session_state.tela_ativa == "rastreio" else "1px solid #e0e0e0") + """ !important;
            padding: 14px !important;
            border-radius: 50px !important;
            width: 100% !important;
            box-shadow: """ + ("0 4px 15px rgba(44,62,80,0.2)" if st.session_state.tela_ativa == "rastreio" else "none") + """ !important;
            transition: all 0.3s ease !important;
        }
        
        /* Botões Principais de Ação (Aparência UniLog - Verde Verde de Ação) */
        div.stButton > button[key="trigger_calculo"], div.stButton > button[key="action_processar_rastreio"] {
            background-color: #27ae60 !important;
            color: white !important;
            font-weight: bold !important;
            font-size: 16px !important;
            padding: 14px !important;
            border-radius: 50px !important;
            border: none !important;
            box-shadow: 0 8px 20px rgba(39,174,96,0.25) !important;
            transition: 0.3s !important;
        }
        div.stButton > button[key="trigger_calculo"]:hover, div.stButton > button[key="action_processar_rastreio"]:hover {
            background-color: #219150 !important;
            box-shadow: 0 10px 25px rgba(39,174,96,0.35) !important;
        }

        /* Estilização para o botão de COPIAR (Azul UniLog) */
        div.stButton > button[key="btn_pure_copy_frete"], div.stButton > button[key="btn_pure_copy_rastreio"] {
            background-color: #3498db !important;
            color: white !important;
            font-weight: bold !important;
            font-size: 15px !important;
            padding: 14px !important;
            border-radius: 8px !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(52,152,219,0.25) !important;
            cursor: pointer !important;
            width: 100% !important;
            margin-top: 5px !important;
            transition: 0.3s !important;
        }
        div.stButton > button[key="btn_pure_copy_frete"]:hover, div.stButton > button[key="btn_pure_copy_rastreio"]:hover {
            background-color: #2980b9 !important;
        }
    </style>
""", unsafe_allow_html=True)


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

# Cabeçalho Centralizado Seguro para Mobile e Desktop (Estilo Hero UniLog)
def arrumar_imagem_local(caminho):
    try:
        with open(caminho, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return ""

img_base64 = arrumar_imagem_local("logo_ciadojeans.PNG")

st.markdown(
    f"""
    <div style='background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); padding: 35px 20px; border-radius: 18px; text-align: center; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.15);'>
        <div style='margin-bottom: 12px;'>
            <img src="data:image/png;base64,{img_base64}" width="110" style="display: block; margin: 0 auto; filter: drop-shadow(0px 4px 8px rgba(0,0,0,0.2));">
        </div>
        <h1 style='color: #ffffff; font-weight: 800; margin: 0; font-size: 2.0rem; letter-spacing: -0.5px; font-family: "Segoe UI", sans-serif;'>
            ⚡ CIA DO JEANS
        </h1>
        <p style='color: #ffffff; opacity: 0.9; margin: 5px 0 0 0; font-size: 1.0rem; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;'>
            Logística Inteligente
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Criamos duas colunas para simular abas perfeitas com gatilho instantâneo (on_click)
col_aba1, col_aba2 = st.columns(2)

with col_aba1:
    st.button("📊 COTAR NOVO FRETE", use_container_width=True, key="aba_cot_btn", on_click=mudar_para_cotacao)

with col_aba2:
    st.button("📦 RASTREAR ENCOMENDA", use_container_width=True, key="aba_ras_btn", on_click=mudar_para_rastreio)

st.markdown("<br>", unsafe_allow_html=True)


# --- EXIBIÇÃO DA TELA: COTAÇÃO ---
if st.session_state.tela_ativa == "cotacao":
    
    # PASSO 1: LOCALIZAÇÃO DO CLIENTE
    st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
    st.markdown('<div class="titulo-etapa">📍 PASSO 1: Destino do Pedido</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.5, 2, 1])

    with col1:
        cep_input = st.text_input("📬 Digite o CEP do Cliente:", placeholder="00000000", max_chars=9, key="cep_input_fiel")

    desabilitar_campos = False  # Destravado por padrão caso a rede ou API falhem

    if cep_input:
        cep_limpo = cep_input.replace("-", "").replace(" ", "")
        if len(cep_limpo) == 8 and cep_limpo.isdigit():
            try:
                url_api = f"https://opencep.com/v1/{cep_limpo}"
                resposta = requests.get(url_api, timeout=3).json()
                if "localidade" in resposta and resposta.get("localidade"):
                    # Força a gravação direta na memória do Streamlit para funcionar na hora
                    st.session_state["cidade_input_fiel"] = resposta.get("localidade", "").upper()
                    st.session_state["uf_input_fiel"] = resposta.get("uf", "").upper()
                    desabilitar_campos = True  # Só bloqueia se encontrar automaticamente
                else:
                    desabilitar_campos = False
            except Exception:
                desabilitar_campos = False

    with col2: 
        cidade_automatica = st.text_input("📍 Cidade Identificada:", placeholder="Digite a Cidade se não buscar...", disabled=desabilitar_campos, key="cidade_input_fiel")
            
    with col3: 
        uf_automatica = st.text_input("🏳️ UF:", placeholder="EX: GO", disabled=desabilitar_campos, key="uf_input_fiel")
            
    st.markdown('</div>', unsafe_allow_html=True)

    # PASSO 2: ENTRADA DE PRODUTOS
    st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
    st.markdown('<div class="titulo-etapa">👖 PASSO 2: O que estamos enviando hoje?</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        qtd_calcas = st.number_input("Quantidade de Calças:", min_value=0, value=0, step=1, key="calc_un")
        qtd_bermudas = st.number_input("Quantidade de Bermudas:", min_value=0, value=0, step=1, key="berm_un")
        qtd_shorts = st.number_input("Quantidade de Shorts:", min_value=0, value=0, step=1, key="shor_un")
        qtd_camisas = st.number_input("Quantidade de Camisas:", min_value=0, value=0, step=1, key="cam_un")
        qtd_saias = st.number_input("Quantidade de Saias:", min_value=0, value=0, step=1, key="saia_un")
        # Campo Croppeds movido para debaixo de saias
        qtd_croppeds = st.number_input("Quantidade de Croppeds:", min_value=0, value=0, step=1, key="crop_un")
        
    with c2:
        qtd_gola_o = st.number_input("Quantidade de Gola O:", min_value=0, value=0, step=1, key="gola_un")
        qtd_tshirt = st.number_input("Quantidade de T-Shirt:", min_value=0, value=0, step=1, key="tsh_un")
        qtd_polo = st.number_input("Quantidade de Gola Polo:", min_value=0, value=0, step=1, key="polo_un")
        qtd_vestidos = st.number_input("Quantidade de Vestidos:", min_value=0, value=0, step=1, key="vest_un")
        qtd_conjuntos = st.number_input("Quantidade de Conjuntos:", min_value=0, value=0, step=1, key="conj_un")
        qtd_bones = st.number_input("Quantidade de Bonés:", min_value=0, value=0, step=1, key="bone_un")

    # Matemática de Pesos e Embalagem (Vestido=0.55kg, Conjunto=0.50kg, Camisa=0.25kg, Saia=0.30kg, Cropped=0.15kg, Boné=0.10kg)
    peso_pecas_puro = (
        (qtd_calcas * 0.60) + (qtd_bermudas * 0.40) + (qtd_shorts * 0.35) + 
        (qtd_gola_o * 0.28) + (qtd_tshirt * 0.20) + (qtd_polo * 0.32) +
        (qtd_vestidos * 0.55) + (qtd_conjuntos * 0.50) + (qtd_bones * 0.10) +
        (qtd_camisas * 0.25) + (qtd_saias * 0.30) + (qtd_croppeds * 0.15)
    )
    peso_total_calculado = peso_pecas_puro + (0.4 if peso_pecas_puro > 0 else 0)
    total_pecas = (
        qtd_calcas + qtd_bermudas + qtd_shorts + qtd_gola_o + qtd_tshirt + 
        qtd_polo + qtd_vestidos + qtd_conjuntos + qtd_bones + qtd_camisas + 
        qtd_saias + qtd_croppeds
    )

    with c3:
        valor_manual_nf_txt = st.text_input("✍️ Valor Real da NF (Opcional):", placeholder="Ex: 1250,00", key="nf_manual_txt").strip()
        
        valor_manual_nf = 0.0
        if valor_manual_nf_txt:
            try:
                valor_manual_nf = float(valor_manual_nf_txt.replace(".", "").replace(",", "."))
            except ValueError:
                st.error("⚠️ Digite um valor numérico válido para a NF.")
                
        # Opção seletora de meio de envio / regra de divisão
        meio_envio_selecionado = st.selectbox(
            "📦 Regra de Divisão do Fardo:",
            ["Padrão (Dividir acima de 50 kg)", "Correios / J&T / Azul Cargo (Dividir acima de 30 kg)", "Não Dividir fardo"],
            key="box_regra_divisao_fardo"
        )
        
        # Divisão dinâmica de volumes
        num_volumes = 1
        if total_pecas > 0:
            if meio_envio_selecionado == "Padrão (Dividir acima de 50 kg)" and peso_total_calculado > 50.0:
                num_volumes = int(peso_total_calculado // 50) + (1 if peso_total_calculado % 50 > 0 else 0)
            elif meio_envio_selecionado == "Correios / J&T / Azul Cargo (Dividir acima de 30 kg)" and peso_total_calculado > 30.0:
                num_volumes = int(peso_total_calculado // 30) + (1 if peso_total_calculado % 30 > 0 else 0)
            elif meio_envio_selecionado == "Não Dividir fardo":
                num_volumes = 1

        peso_por_volume = peso_total_calculado / num_volumes if num_volumes > 0 else 0
        pecas_por_volume = total_pecas // num_volumes if num_volumes > 0 else 0

        if total_pecas == 0:
            tipo_embalagem = "Nenhum produto"
            comp, larg, alt = 0, 0, 0
            classificacao_tamanho = "Sem Carga"
        elif pecas_por_volume <= 15:
            tipo_embalagem = "Caixa Pequena" if num_volumes == 1 else f"{num_volumes} Caixas Pequenas"
            comp, larg, alt = 40, 30, 20
            classificacao_tamanho = "PP (Caixa Pequena)"
        elif pecas_por_volume <= 30:
            tipo_embalagem = "Caixa Média" if num_volumes == 1 else f"{num_volumes} Caixas Médias"
            comp, larg, alt = 50, 40, 30
            classificacao_tamanho = "P (Caixa Média)"
        elif pecas_por_volume <= 60:
            tipo_embalagem = "Fardo Comercial" if num_volumes == 1 else f"{num_volumes} Fardos Comerciais"
            comp, larg, alt = 60, 45, 35
            classificacao_tamanho = "M (Fardo Padrão)"
        elif pecas_por_volume <= 120:
            tipo_embalagem = "Fardo Comercial" if num_volumes == 1 else f"{num_volumes} Fardos Comerciais"
            comp, larg, alt = 80, 50, 40
            classificacao_tamanho = "G (Fardo Grande)"
        else:
            tipo_embalagem = "Fardo Comercial" if num_volumes == 1 else f"{num_volumes} Fardos Comerciais"
            comp, larg, alt = 100, 60, 50
            classificacao_tamanho = "XG (Fardo Master)"

        # Regra: Se o tamanho for G ou XG, o comprimento fica na vertical (em pé) e largura na horizontal
        if "G" in classificacao_tamanho:
            visual_altura = comp
            visual_largura = larg
            orientacao_texto = "Fardo em Pé"
        else:
            visual_altura = alt
            visual_largura = larg
            orientacao_texto = "Fardo Deitado"

        valor_nf_meia = (
            (qtd_calcas * 40) + (qtd_bermudas * 33) + (qtd_shorts * 33) + 
            (qtd_gola_o * 18) + (qtd_tshirt * 19) + (qtd_polo * 25) +
            (qtd_vestidos * 45) + (qtd_conjuntos * 50) + (qtd_bones * 15) +
            (qtd_camisas * 30) + (qtd_saias * 35) + (qtd_croppeds * 20)
        )
        valor_para_seguro = valor_manual_nf if valor_manual_nf > 0 else valor_nf_meia
        
        txt_volumes_resumo = f" ({num_volumes} Vol. de {peso_por_volume:.2f} kg)" if num_volumes > 1 else ""
        st.info(f"**📊 Resumo do Pedido:**\n* **Carga:** {total_pecas} un | {peso_total_calculado:.2f} kg{txt_volumes_resumo}\n* **Embalagem:** {tipo_embalagem}\n* **Seguro:** R$ {valor_para_seguro:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

    # DISPARADOR DE CÁLCULO
    st.markdown("<br>", unsafe_allow_html=True)
    btn_calcular = st.button("🚀 CALCULAR FRETE E GERAR WHATSAPP", type="primary", use_container_width=True, key="trigger_calculo")
    st.markdown("<br>", unsafe_allow_html=True)

    # PASSO 3: RESULTADOS E WHATSAPP
    if btn_calcular or st.session_state.get('frete_calculado_ok', False):
        st.session_state['frete_calculado_ok'] = True
        cidade_busca = st.session_state.get("cidade_input_fiel", "").strip().upper()
        uf_busca = st.session_state.get("uf_input_fiel", "").strip().upper()
        
        if not cidade_busca:
            st.error("❌ Por favor, informe um CEP ou preencha a Cidade no Passo 1.")
        elif total_pecas == 0:
            st.error("❌ Insira a quantidade de produtos no Passo 2 para calcular.")
        else:
            
            # --- BLOCO VISUAL: CALCULADORA DE VOLUMETRIA E ESCALA HUMANA ---
            st.markdown('<div class="bloco-etapa" style="border-top: 4px solid #d4a017;">', unsafe_allow_html=True)
            st.markdown(f'<div class="titulo-etapa" style="color: #2c3e50;">📐 Dimensões e Comparativo de Escala ({orientacao_texto})</div>', unsafe_allow_html=True)
            
            v_col1, v_col2 = st.columns([1, 1.2])
            
            with v_col1:
                txt_vol_detalhe = f"<p style='margin: 0 0 8px 0; font-size: 15px; color: #d4a017;'><b>⚠️ Carga Dividida: {num_volumes} Volumes ({meio_envio_selecionado})</b></p>" if num_volumes > 1 else ""
                st.html(f"""
<div style="background-color: #f8f9fa; padding: 18px; border-radius: 12px; border: 1px solid #e0e0e0; font-family: sans-serif;">
{txt_vol_detalhe}
<p style="margin: 0 0 8px 0; font-size: 14px; color: #2c3e50;"><b>Quantidade Total de Volumes:</b> {num_volumes} volume(s)</p>
<p style="margin: 0 0 8px 0; font-size: 14px; color: #2c3e50;"><b>Classificação (por volume):</b> {classificacao_tamanho}</p>
<p style="margin: 0 0 8px 0; font-size: 14px; color: #2c3e50;"><b>Peso por Volume:</b> {peso_por_volume:.2f} kg</p>
<p style="margin: 0 0 8px 0; font-size: 14px; color: #2c3e50;"><b>Comprimento:</b> {comp} cm</p>
<p style="margin: 0 0 8px 0; font-size: 14px; color: #2c3e50;"><b>Largura:</b> {larg} cm</p>
<p style="margin: 0 0 0 0; font-size: 14px; color: #2c3e50;"><b>Altura:</b> {alt} cm</p>
</div>
""")
            
            with v_col2:
                # Proporção matemática de escala (1cm = 1.3px)
                px_alt_fardo = int(visual_altura * 1.3)
                px_larg_fardo = int(visual_largura * 1.3)
                
                html_fardos_render = ""
                for vol_i in range(num_volumes):
                    label_fardo = "FARDO" if num_volumes == 1 else f"VOL {vol_i+1}"
                    html_fardos_render += f"""
<div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%;">
<div style="font-family: sans-serif; font-size: 11px; color: #3498db; font-weight: bold; margin-bottom: 4px;">{comp}x{larg}x{alt} cm</div>
<div style="width: {px_larg_fardo}px; height: {px_alt_fardo}px; background-color: #d4a017; border: 2px solid #b8860b; border-radius: 6px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 0px;">
<span style="color: white; font-size: 10px; font-weight: bold; text-align: center; font-family: sans-serif; padding: 2px;">{label_fardo}</span>
</div>
</div>
"""

                # Pessoa utilizando DIVs estruturadas em CSS Puro.
                st.html(f"""
<div style="display: flex; align-items: flex-end; justify-content: center; gap: 20px; background: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e5e7eb; height: 250px; overflow-x: auto;">
<div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; flex-shrink: 0;">
<div style="font-family: sans-serif; font-size: 11px; color: #7f8c8d; margin-bottom: 4px;">Pessoa (1.75m)</div>
<div style="width: 50px; height: 215px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; margin-bottom: 0px;">
    <!-- Cabeça -->
    <div style="width: 26px; height: 26px; background-color: #f3c693; border-radius: 50%; margin-bottom: 4px;"></div>
    <!-- Tronco (Camisa Azul UniLog) -->
    <div style="width: 38px; height: 65px; background-color: #3498db; border-radius: 4px 4px 0 0; position: relative;">
        <!-- Braços -->
        <div style="width: 6px; height: 45px; background-color: #f3c693; position: absolute; left: -7px; top: 0; border-radius: 3px;"></div>
        <div style="width: 6px; height: 45px; background-color: #f3c693; position: absolute; right: -7px; top: 0; border-radius: 3px;"></div>
    </div>
    <!-- Pernas (Calça Escura) -->
    <div style="width: 34px; height: 105px; display: flex; justify-content: space-between;">
        <div style="width: 14px; height: 105px; background-color: #2c3e50; border-radius: 0 0 2px 2px; position: relative;">
            <div style="width: 18px; height: 6px; background-color: #f3c693; position: absolute; bottom: 0; left: -2px; border-radius: 2px 0 0 0;"></div>
        </div>
        <div style="width: 14px; height: 105px; background-color: #2c3e50; border-radius: 0 0 2px 2px; position: relative;">
            <div style="width: 18px; height: 6px; background-color: #f3c693; position: absolute; bottom: 0; right: -2px; border-radius: 0 2px 0 0;"></div>
        </div>
    </div>
</div>
</div>
{html_fardos_render}
</div>
""")
            st.markdown('</div>', unsafe_allow_html=True)
            
            opcoes_whatsapp = []
            
            if df_fretes_fixos.empty:
                st.warning("⚠️ Planilha 'SISTEMA_DE_FRETES_AUTOMATIZADO.xlsx' não encontrada.")
            else:
                resultados_fixos = df_fretes_fixos[(df_fretes_fixos['CIDADE'] == cidade_busca) & (df_fretes_fixos['UF'] == uf_busca)]
                
                if not resultados_fixos.empty:
                    if btn_calcular: 
                        st.markdown("### 🏁 Transportadoras Encontradas para a Região")
                        for idx, row in resultados_fixos.iterrows():
                            print_prazo = str(row['PRAZO'])
                            if "cotar" not in print_prazo.lower() and "dias" not in print_prazo.lower() and print_prazo != '-': 
                                print_prazo = f"{print_prazo} Dias"
                                
                            st.markdown(f"""
                            <div class="card-frete" style="border-left: 5px solid #3498db;">
                                <div>
                                    <strong style="font-size:16px; color:#2c3e50;"><b>🚛 {row['TRANSPORTADORA']}</b></strong><br>
                                    <span style="font-size:13px; color:#7f8c8d;">📍 Rota: {row['ROTA_ENVIO']} | 📞 Fone: {row['FONE']}</span><br>
                                    <span style="font-size:12px; color:#95a5a6;">⏱️ Prazo: {print_prazo} | 📄 Exige NF: {row['EXIGE_NF']}</span>
                                </div>
                                <div style="text-align: right;"><span style="font-size:12px; color:#7f8c8d; font-weight:600;">Mínimo</span><br><span style="font-size:18px; font-weight:700; color:#2c3e50;">R$ {row['VALOR_MINIMO']}</span></div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                    for idx, row in resultados_fixos.iterrows():
                        print_prazo = str(row['PRAZO'])
                        if "cotar" not in print_prazo.lower() and "dias" not in print_prazo.lower() and print_prazo != '-': 
                            print_prazo = f"{print_prazo} Dias"
                        opcoes_whatsapp.append(
                            f"🚛 *{row['TRANSPORTADORA']}*\n"
                            f"💰 Mínimo: R$ {row['VALOR_MINIMO']}\n"
                            f"⏱️ Prazo: {print_prazo}\n"
                            f"📞 Contato: {row['FONE']}\n"
                        )
                else: 
                    st.warning(f"Nenhuma transportadora cadastrada no Excel regional para {cidade_busca}-{uf_busca}.")

            # PASSO 4: ENVIAR PARA O WHATSAPP
            if opcoes_whatsapp:
                st.markdown("<br><hr style='border-top: 1px dashed #cbd5e1;'><br>", unsafe_allow_html=True)
                st.markdown('<div class="bloco-etapa" style="border-top: 4px solid #25d366;">', unsafe_allow_html=True)
                st.markdown('<div class="titulo-etapa" style="color: #27ae60;">💬 PASSO 3: Enviar Cotação ao Cliente</div>', unsafe_allow_html=True)
                
                texto_opcoes = "\n".join(opcoes_whatsapp)
                
                txt_whatsapp_volumes = f"{num_volumes} fardos" if num_volumes > 1 else "1 fardo"
                mensagem_vendedor = (
                    f"Olá! Segue a cotação de frete para o seu pedido da *Cia do Jeans*:\n\n"
                    f"📍 *Destino:*\n{cidade_busca} - {uf_busca}\n\n"
                    f"📦 *Volume estimado:*\n{total_pecas} peças ({peso_total_calculado:.2f} kg) - Dividido em {txt_whatsapp_volumes}\n\n"
                    f"🛍️ *Embalagem:*\n{tipo_embalagem} ({classificacao_tamanho}) - Medidas unitárias: {comp}x{larg}x{alt} cm ({orientacao_texto})\n\n"
                    f"-----------------------------------------\n"
                    f"🚚 *OPÇÕES DE ENVIO:*\n\n"
                    f"{texto_opcoes}"
                    f"-----------------------------------------\n\n"
                    f"_Qual destas opções fica melhor para fazermos o despacho?_"
                )
                
                texto_editavel = st.text_area("Pré-visualização da Mensagem:", value=mensagem_vendedor, height=250, key="txt_area_print")
                texto_codificado = urllib.parse.quote(texto_editavel)
                link_whatsapp = f"https://api.whatsapp.com/send?text={texto_codificado}"
                
                # Botão Original do WhatsApp
                st.markdown(f"""
                    <a href="{link_whatsapp}" target="_blank" style="text-decoration: none;">
                        <div style="background-color: #25d366; color: white; text-align: center; padding: 14px; border-radius: 50px; font-weight: bold; font-size: 16px; box-shadow: 0 8px 20px rgba(37,211,102,0.25); cursor: pointer; margin-bottom: 12px; font-family: sans-serif; transition: 0.3s;">
                            📲 ENVIAR COTAÇÃO PARA O WHATSAPP DO CLIENTE
                        </div>
                    </a>
                """, unsafe_allow_html=True)

                # Botão nativo Streamlit azul 
                if st.button("📋 COPIAR TEXTO DA COTAÇÃO", key="btn_pure_copy_frete"):
                    texto_js_safe = texto_editavel.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('\n', '\\n')
                    st.components.v1.html(f"""
                        <script>
                        parent.navigator.clipboard.writeText(`{texto_js_safe}`);
                        alert("Cotação copiada com sucesso! 🎉");
                        </script>
                    """, height=0)
                
                st.markdown('</div>', unsafe_allow_html=True)


# --- EXIBIÇÃO DA TELA: RASTREAMENTO ---
elif st.session_state.tela_ativa == "rastreio":
    st.markdown('<div class="bloco-etapa" style="border-top: 4px solid #2c3e50;">', unsafe_allow_html=True)
    st.markdown('<div class="titulo-etapa">📦 PASSO ÚNICO: Gerar Rastreio para o Cliente</div>', unsafe_allow_html=True)

    # Reajustado layout de colunas para adicionar o campo do Nome do Cliente mantendo proporção limpa
    col_nome_cli, col_transp, col_cod, col_doc = st.columns([1.2, 1.2, 1.2, 1])

    with col_nome_cli:
        nome_cliente_rastreio = st.text_input("Nome do Cliente:", placeholder="Ex: Maria Silva", key="campo_nome_cliente_estavel").strip()

    with col_transp:
        transportadora_rastreio = st.selectbox(
            "Selecione a Transportadora:",
            ["Correios", "J&T Express", "Braspress", "Azul Cargo", "Jadlog"],
            key="box_selecao_transportadora_estavel"
        )

    with col_cod:
        codigo_rastreio = st.text_input("Código de Rastreio / Nº Nota Fiscal:", placeholder="Ex: BR123456789X / 4552", key="campo_codigo_estavel").strip()

    with col_doc:
        doc_cliente = st.text_input("CPF ou CNPJ do Cliente (Se J&T/Braspress):", placeholder="Apenas números", key="campo_doc_estavel").strip()

    btn_gerar_mensagem = st.button("⚙️ GERAR INFORMAÇÕES DE RASTREAMENTO", type="primary", use_container_width=True, key="action_processar_rastreio")

    if btn_gerar_mensagem:
        if not codigo_rastreio:
            st.error("⚠️ Por favor, digite o código de rastreio ou número do documento antes de gerar.")
            st.session_state["rastreio_gerado"] = False
        else:
            st.session_state["rastreio_gerado"] = True

    if st.session_state["rastreio_gerado"] and codigo_rastreio:
        link_rastreio_final = ""
        mensagem_rastreio = ""
        
        # Define saudação inicial com base na presença do nome do cliente
        txt_saudacao = f"Olá, *{nome_cliente_rastreio}*!" if nome_cliente_rastreio else "Olá!"
        
        if transportadora_rastreio == "Correios":
            link_rastreio_final = f"https://rastreamento.correios.com.br/app/index.php?objetos={codigo_rastreio}"
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já foi despachado! 🎉\n\n"
                f"🚚 *Transportadora:* Correios\n"
                f"📦 *Código de Rastreio:* `{codigo_rastreio}`\n\n"
                f"🔗 *Clique no link abaixo para acompanhar seu envio:*\n"
                f"{link_rastreio_final}"
            )
            
        elif transportadora_rastreio == "Jadlog":
            link_rastreio_final = f"https://www.jadlog.com.br/siteInstitucional/tracking.jad?conteudo={codigo_rastreio}"
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já está a caminho! 🎉\n\n"
                f"🚚 *Transportadora:* Jadlog\n"
                f"📦 *Código de Rastreio:* `{codigo_rastreio}`\n\n"
                f"🔗 *Clique no link abaixo para acompanhar seu envio:*\n"
                f"{link_rastreio_final}"
            )
            
        elif transportadora_rastreio == "J&T Express":
            link_rastreio_final = "https://www.jtexpress.com.br/trajectoryQuery"
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já foi despachado! 🎉\n\n"
                f"🚚 *Transportadora:* J&T Express\n"
                f"📦 *Código de Rastreio:* `{codigo_rastreio}`\n\n"
                f"🔗 *Como rastrear:*\n"
                f"1. Acesse o site: {link_rastreio_final}\n"
                f"2. Digite o seu código de rastreio acima ou o seu CPF/CNPJ."
            )
            
        elif transportadora_rastreio == "Braspress":
            link_rastreio_final = "https://www.braspress.com.br/"
            doc_info = f" (CNPJ/CPF: {doc_cliente})" if doc_cliente else ""
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já foi coletado! 🎉\n\n"
                f"🚚 *Transportadora:* Braspress\n"
                f"📄 *Número da Nota Fiscal:* `{codigo_rastreio}`{doc_info}\n\n"
                f"🔗 *Como rastrear:*\n"
                f"1. Acesse o site: {link_rastreio_final}\n"
                f"2. No topo da página, clique em *'Rastreie sua Encomenda'*\n"
                f"3. Informe o número da NF acima e o seu CPF/CNPJ."
            )
            
        elif transportadora_rastreio == "Azul Cargo":
            link_rastreio_final = f"https://www.azullogistica.com.br/Rastreio/Rastrear?awb={codigo_rastreio}"
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já está voando até você! 🎉\n\n"
                f"🚚 *Transportadora:* Azul Cargo Express\n"
                f"📦 *Código de Rastreio (AWB):* `{codigo_rastreio}`\n\n"
                f"🔗 *Clique no link abaixo para acompanhar seu envio:*\n"
                f"{link_rastreio_final}"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        
        texto_rastreio_editavel = st.text_area("Pré-visualização da Mensagem de Rastreio:", value=mensagem_rastreio, height=180, key="txt_area_rastreio")
        texto_rastreio_codificado = urllib.parse.quote(texto_rastreio_editavel)
        link_whatsapp_rastreio = f"https://api.whatsapp.com/send?text={texto_rastreio_codificado}"
        
        # Botão Original do WhatsApp (Rastreio)
        st.markdown(f"""
            <a href="{link_whatsapp_rastreio}" target="_blank" style="text-decoration: none;">
                <div style="background-color: #25d366; color: white; text-align: center; padding: 14px; border-radius: 50px; font-weight: bold; font-size: 16px; box-shadow: 0 8px 20px rgba(37,211,102,0.25); cursor: pointer; margin-top: 5px; margin-bottom: 12px; font-family: sans-serif; transition: 0.3s;">
                    📲 ENVIAR MENSAGEM DE RASTREIO PARA O WHATSAPP
                </div>
            </a>
        """, unsafe_allow_html=True)
        
        # Botão nativo Streamlit azul (Rastreio)
        if st.button("📋 COPIAR TEXTO DO RASTREIO", key="btn_pure_copy_rastreio"):
            texto_rastreio_js_safe = texto_rastreio_editavel.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('\n', '\\n')
            st.components.v1.html(f"""
                <script>
                parent.navigator.clipboard.writeText(`{texto_rastreio_js_safe}`);
                alert("Rastreio copiado com sucesso! 🎉");
                </script>
            """, height=0)
        
        st.markdown("---")
        btn_abrir_painel = st.checkbox("🖥️ QUER VISUALIZAR O RASTREIO DENTRO DO SITE?", value=False, key="check_painel_integrated")
        
        if btn_abrir_painel:
            st.markdown(f"### 🖥️ Painel de Rastreio em Tempo Real - {transportadora_rastreio}")
            st.markdown(f"👉 _Caso a janela abaixo fique em branco devido à segurança da transportadora, [CLIQUE AQUI PARA ABRIR EM NOVA ABA]({link_rastreio_final})._")
            
            st.components.v1.html(
                f"""
                <iframe src="{link_rastreio_final}" width="100%" height="600px" style="border: 2px solid #e2e8f0; border-radius: 12px; background-color: white;"></iframe>
                """,
                height=620
            )
    else:
        st.info("✍️ Digite o código de rastreio acima para gerar o link de envio imediatamente.")

    st.markdown('</div>', unsafe_allow_html=True)
