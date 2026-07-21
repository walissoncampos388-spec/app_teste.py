import streamlit as st
import pandas as pd
import requests
import urllib.parse
import base64
from datetime import datetime

# 1. Configuração de Página
st.set_page_config(
    page_title="Cia do Jeans - Logística Inteligente", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Gerenciamento de Estado (Session State)
if "tela_ativa" not in st.session_state:
    st.session_state.tela_ativa = "cotacao"
if "cidade_input_fiel" not in st.session_state:
    st.session_state["cidade_input_fiel"] = ""
if "uf_input_fiel" not in st.session_state:
    st.session_state["uf_input_fiel"] = ""
if "rastreio_gerado" not in st.session_state:
    st.session_state["rastreio_gerado"] = False

# Estatísticas do Admin
if "stats_total" not in st.session_state:
    st.session_state.stats_total = 0
if "stats_sucesso" not in st.session_state:
    st.session_state.stats_sucesso = 0
if "stats_erro" not in st.session_state:
    st.session_state.stats_erro = 0
if "exibir_admin" not in st.session_state:
    st.session_state.exibir_admin = False

# Funções de Navegação
def mudar_para_cotacao():
    st.session_state.tela_ativa = "cotacao"

def mudar_para_rastreio():
    st.session_state.tela_ativa = "rastreio"

def alternar_admin():
    st.session_state.exibir_admin = not st.session_state.exibir_admin

# 3. Estilização CSS Inspirada no Layout UniLog
cor_cotacao_bg = "#3498db" if st.session_state.tela_ativa == "cotacao" else "#e2e8f0"
cor_cotacao_txt = "white" if st.session_state.tela_ativa == "cotacao" else "#475569"

cor_rastreio_bg = "#3498db" if st.session_state.tela_ativa == "rastreio" else "#e2e8f0"
cor_rastreio_txt = "white" if st.session_state.tela_ativa == "rastreio" else "#475569"

st.markdown(f"""
    <style>
        .stDeployButton {{display:none;}}
        footer {{visibility: hidden;}}
        .main {{ background-color: #f0f2f5; font-family: 'Segoe UI', Roboto, sans-serif; }}
        
        /* Cabeçalho Hero */
        .unilog-hero {{
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            padding: 30px 20px;
            border-radius: 16px;
            text-align: center;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }}
        .unilog-hero h1 {{ font-size: 2.2rem; font-weight: 800; margin: 0; color: white; }}
        .unilog-hero p {{ opacity: 0.9; margin-top: 8px; font-size: 1.05rem; }}
        
        /* Cards Organizadores */
        .card-unilog {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.06);
            margin-bottom: 25px;
            border-top: 4px solid #3498db;
        }}
        .card-header-title {{
            color: #2c3e50;
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 18px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Abas Estilizadas */
        div.stButton > button[key="aba_cot_btn"] {{
            background-color: {cor_cotacao_bg} !important;
            color: {cor_cotacao_txt} !important;
            font-weight: bold !important;
            border: none !important;
            padding: 14px !important;
            border-radius: 50px !important;
            width: 100% !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        }}
        div.stButton > button[key="aba_ras_btn"] {{
            background-color: {cor_rastreio_bg} !important;
            color: {cor_rastreio_txt} !important;
            font-weight: bold !important;
            border: none !important;
            padding: 14px !important;
            border-radius: 50px !important;
            width: 100% !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        }}
        
        /* Botões Primários Estilo UniLog */
        div.stButton > button[key="trigger_calculo"], div.stButton > button[key="action_processar_rastreio"] {{
            background: #27ae60 !important;
            color: white !important;
            font-weight: bold !important;
            border-radius: 50px !important;
            padding: 14px 28px !important;
            border: none !important;
            box-shadow: 0 6px 18px rgba(39,174,96,0.3) !important;
            width: 100% !important;
            font-size: 16px !important;
        }}
        div.stButton > button[key="trigger_calculo"]:hover, div.stButton > button[key="action_processar_rastreio"]:hover {{
            background: #219150 !important;
        }}

        /* Timeline de Rastreio UniLog */
        .timeline {{ padding: 10px 10px 0 10px; }}
        .timeline-item {{ display: flex; margin-bottom: 25px; }}
        .timeline-marker {{ display: flex; flex-direction: column; align-items: center; margin-right: 18px; }}
        .marker-circle {{ width: 16px; height: 16px; background: #3498db; border-radius: 50%; border: 3px solid #d4e6f1; }}
        .marker-line {{ width: 2px; height: 100%; background: #e0e0e0; margin-top: 4px; }}
        .timeline-content span {{ font-size: 12px; color: #95a5a6; font-weight: 600; }}
        .timeline-content h4 {{ margin: 3px 0; color: #2c3e50; font-size: 16px; font-weight: 700; }}
        .timeline-content p {{ margin: 0; font-size: 14px; color: #7f8c8d; }}

        /* Dashboard Admin */
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-top: 15px; }}
        .stat-card {{ padding: 20px; border-radius: 12px; color: white; text-align: center; font-family: sans-serif; }}
        .stat-card.total {{ background: #34495e; }}
        .stat-card.success {{ background: #27ae60; }}
        .stat-card.error {{ background: #e74c3c; }}
        .stat-card h3 {{ margin: 0; font-size: 14px; opacity: 0.9; text-transform: uppercase; color: white; }}
        .stat-card p {{ margin: 5px 0 0 0; font-size: 28px; font-weight: bold; color: white; }}
    </style>
""", unsafe_allow_html=True)


# 4. Função de Leitura da Planilha
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

def arrumar_imagem_local(caminho):
    try:
        with open(caminho, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return ""

img_base64 = arrumar_imagem_local("logo_ciadojeans.PNG")
img_html = f'<img src="data:image/png;base64,{img_base64}" width="80" style="margin-bottom:10px;"><br>' if img_base64 else ""

# 5. Topo Hero UniLog
st.markdown(
    f"""
    <div class="unilog-hero">
        {img_html}
        <h1>CIA DO JEANS</h1>
        <p>Sistema Unificado de Cotação e Rastreamento de Encomendas</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# 6. Abas Superiores
col_aba1, col_aba2 = st.columns(2)
with col_aba1:
    st.button("📊 COTAR NOVO FRETE", use_container_width=True, key="aba_cot_btn", on_click=mudar_para_cotacao)
with col_aba2:
    st.button("📦 RASTREAR ENCOMENDA", use_container_width=True, key="aba_ras_btn", on_click=mudar_para_rastreio)

st.markdown("<br>", unsafe_allow_html=True)


# ==============================================================================
# TELA 1: COTAÇÃO DE FRETE (LAYOUT ESTILIZADO UNILOG)
# ==============================================================================
if st.session_state.tela_ativa == "cotacao":
    
    # PASSO 1: DESTINO
    st.markdown('<div class="card-unilog">', unsafe_allow_html=True)
    st.markdown('<div class="card-header-title">📍 PASSO 1: Destino do Pedido</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.5, 2, 1])

    with col1:
        cep_input = st.text_input("📬 Digite o CEP do Cliente:", placeholder="00000000", max_chars=9, key="cep_input_fiel")

    desabilitar_campos = False
    if cep_input:
        cep_limpo = cep_input.replace("-", "").replace(" ", "")
        if len(cep_limpo) == 8 and cep_limpo.isdigit():
            try:
                url_api = f"https://opencep.com/v1/{cep_limpo}"
                resposta = requests.get(url_api, timeout=3).json()
                if "localidade" in resposta and resposta.get("localidade"):
                    st.session_state["cidade_input_fiel"] = resposta.get("localidade", "").upper()
                    st.session_state["uf_input_fiel"] = resposta.get("uf", "").upper()
                    desabilitar_campos = True
            except Exception:
                desabilitar_campos = False

    with col2: 
        cidade_automatica = st.text_input("📍 Cidade Identificada:", placeholder="Digite a Cidade...", disabled=desabilitar_campos, key="cidade_input_fiel")
            
    with col3: 
        uf_automatica = st.text_input("🏳️ UF:", placeholder="EX: GO", disabled=desabilitar_campos, key="uf_input_fiel")
            
    st.markdown('</div>', unsafe_allow_html=True)

    # PASSO 2: ITENS
    st.markdown('<div class="card-unilog">', unsafe_allow_html=True)
    st.markdown('<div class="card-header-title">👖 PASSO 2: O que estamos enviando hoje?</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        qtd_calcas = st.number_input("Quantidade de Calças:", min_value=0, value=0, step=1, key="calc_un")
        qtd_bermudas = st.number_input("Quantidade de Bermudas:", min_value=0, value=0, step=1, key="berm_un")
        qtd_shorts = st.number_input("Quantidade de Shorts:", min_value=0, value=0, step=1, key="shor_un")
        qtd_camisas = st.number_input("Quantidade de Camisas:", min_value=0, value=0, step=1, key="cam_un")
        qtd_saias = st.number_input("Quantidade de Saias:", min_value=0, value=0, step=1, key="saia_un")
        qtd_croppeds = st.number_input("Quantidade de Croppeds:", min_value=0, value=0, step=1, key="crop_un")
        
    with c2:
        qtd_gola_o = st.number_input("Quantidade de Gola O:", min_value=0, value=0, step=1, key="gola_un")
        qtd_tshirt = st.number_input("Quantidade de T-Shirt:", min_value=0, value=0, step=1, key="tsh_un")
        qtd_polo = st.number_input("Quantidade de Gola Polo:", min_value=0, value=0, step=1, key="polo_un")
        qtd_vestidos = st.number_input("Quantidade de Vestidos:", min_value=0, value=0, step=1, key="vest_un")
        qtd_conjuntos = st.number_input("Quantidade de Conjuntos:", min_value=0, value=0, step=1, key="conj_un")
        qtd_bones = st.number_input("Quantidade de Bonés:", min_value=0, value=0, step=1, key="bone_un")

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
                st.error("⚠️ Digite um valor numérico válido.")
                
        meio_envio_selecionado = st.selectbox(
            "📦 Regra de Divisão do Fardo:",
            ["Padrão (Dividir acima de 50 kg)", "Correios / J&T / Azul Cargo (Dividir acima de 30 kg)", "Não Dividir fardo"],
            key="box_regra_divisao_fardo"
        )
        
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

    btn_calcular = st.button("🚀 CALCULAR FRETE E GERAR MENSAGEM", type="primary", use_container_width=True, key="trigger_calculo")
    st.markdown("<br>", unsafe_allow_html=True)

    # RESULTADOS
    if btn_calcular or st.session_state.get('frete_calculado_ok', False):
        st.session_state['frete_calculado_ok'] = True
        cidade_busca = st.session_state.get("cidade_input_fiel", "").strip().upper()
        uf_busca = st.session_state.get("uf_input_fiel", "").strip().upper()
        
        if not cidade_busca:
            st.error("❌ Por favor, informe um CEP ou preencha a Cidade no Passo 1.")
        elif total_pecas == 0:
            st.error("❌ Insira a quantidade de produtos no Passo 2.")
        else:
            st.markdown('<div class="card-unilog" style="border-top: 4px solid #f59e0b;">', unsafe_allow_html=True)
            st.markdown(f'<div class="card-header-title" style="color: #d97706;">📐 Dimensões e Comparativo ({orientacao_texto})</div>', unsafe_allow_html=True)
            
            v_col1, v_col2 = st.columns([1, 1.2])
            with v_col1:
                txt_vol_detalhe = f"<p style='margin: 0 0 8px 0; font-size: 15px; color: #b45309;'><b>⚠️ Carga Dividida: {num_volumes} Volumes</b></p>" if num_volumes > 1 else ""
                st.html(f"""
                <div style="background-color: #fffbeb; padding: 15px; border-radius: 8px; border: 1px solid #fef3c7; font-family: sans-serif;">
                {txt_vol_detalhe}
                <p style="margin: 0 0 8px 0; font-size: 14px; color: #92400e;"><b>Quantidade Total de Volumes:</b> {num_volumes} volume(s)</p>
                <p style="margin: 0 0 8px 0; font-size: 14px; color: #92400e;"><b>Classificação:</b> {classificacao_tamanho}</p>
                <p style="margin: 0 0 8px 0; font-size: 14px; color: #92400e;"><b>Peso por Volume:</b> {peso_por_volume:.2f} kg</p>
                <p style="margin: 0 0 8px 0; font-size: 14px; color: #92400e;"><b>Medidas:</b> {comp}x{larg}x{alt} cm</p>
                </div>
                """)
            
            with v_col2:
                px_alt_fardo = int(visual_altura * 1.3)
                px_larg_fardo = int(visual_largura * 1.3)
                
                html_fardos_render = ""
                for vol_i in range(num_volumes):
                    label_fardo = "FARDO" if num_volumes == 1 else f"VOL {vol_i+1}"
                    html_fardos_render += f"""
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%;">
                    <div style="font-family: sans-serif; font-size: 11px; color: #1e3a8a; font-weight: bold; margin-bottom: 4px;">{comp}x{larg}x{alt} cm</div>
                    <div style="width: {px_larg_fardo}px; height: {px_alt_fardo}px; background-color: #f59e0b; border: 2px solid #d97706; border-radius: 4px; display: flex; align-items: center; justify-content: center; margin-bottom: 0px;">
                    <span style="color: white; font-size: 10px; font-weight: bold; font-family: sans-serif; padding: 2px;">{label_fardo}</span>
                    </div>
                    </div>
                    """

                st.html(f"""
                <div style="display: flex; align-items: flex-end; justify-content: center; gap: 20px; background: #fafafa; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; height: 230px;">
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%;">
                <div style="font-family: sans-serif; font-size: 11px; color: #6b7280; margin-bottom: 4px;">Pessoa (1.75m)</div>
                <div style="width: 45px; height: 180px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end;">
                    <div style="width: 22px; height: 22px; background-color: #f3c693; border-radius: 50%; margin-bottom: 3px;"></div>
                    <div style="width: 32px; height: 55px; background-color: #3498db; border-radius: 4px 4px 0 0; position: relative;">
                        <div style="width: 5px; height: 40px; background-color: #f3c693; position: absolute; left: -6px; top: 0;"></div>
                        <div style="width: 5px; height: 40px; background-color: #f3c693; position: absolute; right: -6px; top: 0;"></div>
                    </div>
                    <div style="width: 28px; height: 85px; display: flex; justify-content: space-between;">
                        <div style="width: 12px; height: 85px; background-color: #2c3e50;"></div>
                        <div style="width: 12px; height: 85px; background-color: #2c3e50;"></div>
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
                        st.markdown("### 🏁 Transportadoras Encontradas")
                        for idx, row in resultados_fixos.iterrows():
                            print_prazo = str(row['PRAZO'])
                            if "cotar" not in print_prazo.lower() and "dias" not in print_prazo.lower() and print_prazo != '-': 
                                print_prazo = f"{print_prazo} Dias"
                                
                            st.markdown(f"""
                            <div style="background:white; padding:15px; border-radius:10px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-left: 5px solid #3498db; box-shadow: 0 4px 10px rgba(0,0,0,0.03);">
                                <div>
                                    <strong style="font-size:16px; color:#2c3e50;">🚛 {row['TRANSPORTADORA']}</strong><br>
                                    <span style="font-size:13px; color:#7f8c8d;">📍 Rota: {row['ROTA_ENVIO']} | 📞 Fone: {row['FONE']}</span><br>
                                    <span style="font-size:12px; color:#95a5a6;">⏱️ Prazo: {print_prazo} | 📄 NF: {row['EXIGE_NF']}</span>
                                </div>
                                <div style="text-align: right;"><span style="font-size:12px; color:#95a5a6;">Mínimo</span><br><span style="font-size:18px; font-weight:700; color:#27ae60;">R$ {row['VALOR_MINIMO']}</span></div>
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
                    st.warning(f"Nenhuma transportadora cadastrada para {cidade_busca}-{uf_busca}.")

            if opcoes_whatsapp:
                st.markdown('<div class="card-unilog" style="border-top: 4px solid #25d366;">', unsafe_allow_html=True)
                st.markdown('<div class="card-header-title" style="color: #25d366;">💬 PASSO 3: Enviar Cotação ao Cliente</div>', unsafe_allow_html=True)
                
                texto_opcoes = "\n".join(opcoes_whatsapp)
                txt_whatsapp_volumes = f"{num_volumes} fardos" if num_volumes > 1 else "1 fardo"
                mensagem_vendedor = (
                    f"Olá! Segue a cotação de frete para o seu pedido da *Cia do Jeans*:\n\n"
                    f"📍 *Destino:*\n{cidade_busca} - {uf_busca}\n\n"
                    f"📦 *Volume estimado:*\n{total_pecas} peças ({peso_total_calculado:.2f} kg) - Dividido em {txt_whatsapp_volumes}\n\n"
                    f"🛍️ *Embalagem:*\n{tipo_embalagem} ({classificacao_tamanho}) - Medidas: {comp}x{larg}x{alt} cm\n\n"
                    f"-----------------------------------------\n"
                    f"🚚 *OPÇÕES DE ENVIO:*\n\n"
                    f"{texto_opcoes}"
                    f"-----------------------------------------\n\n"
                    f"_Qual destas opções fica melhor para fazermos o despacho?_"
                )
                
                texto_editavel = st.text_area("Pré-visualização da Mensagem:", value=mensagem_vendedor, height=220, key="txt_area_print")
                texto_codificado = urllib.parse.quote(texto_editavel)
                link_whatsapp = f"https://api.whatsapp.com/send?text={texto_codificado}"
                
                st.markdown(f"""
                    <a href="{link_whatsapp}" target="_blank" style="text-decoration: none;">
                        <div style="background-color: #25d366; color: white; text-align: center; padding: 14px; border-radius: 50px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 12px rgba(37,211,102,0.3); margin-bottom: 12px; font-family: sans-serif;">
                            📲 ENVIAR COTAÇÃO PARA O WHATSAPP DO CLIENTE
                        </div>
                    </a>
                """, unsafe_allow_html=True)

                if st.button("📋 COPIAR MENSAGEM", key="btn_pure_copy_frete"):
                    texto_js_safe = texto_editavel.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('\n', '\\n')
                    st.components.v1.html(f"""
                        <script>
                        parent.navigator.clipboard.writeText(`{texto_js_safe}`);
                        alert("Cotação copiada com sucesso! 🎉");
                        </script>
                    """, height=0)
                
                st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# TELA 2: RASTREAMENTO DE ENCOMENDA (DESIGN UNILOG COMPLETO)
# ==============================================================================
elif st.session_state.tela_ativa == "rastreio":
    
    # BUSCA DE RASTREIO UNIFICADO
    st.markdown('<div class="card-unilog" style="text-align:center; padding: 35px 20px;">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#2c3e50; font-weight:800; margin-bottom:8px;">Onde está sua encomenda?</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#7f8c8d; margin-bottom:25px;">Acompanhe suas entregas em tempo real com a Cia do Jeans / UniLog.</p>', unsafe_allow_html=True)
    
    col_inp1, col_inp2, col_inp3 = st.columns([1.5, 1.2, 1.2])
    
    with col_inp1:
        codigo_rastreio = st.text_input("Código de Rastreio ou Nº NF:", placeholder="Digite o código...", key="campo_codigo_estavel").strip().upper()
    with col_inp2:
        transportadora_rastreio = st.selectbox(
            "Transportadora:",
            ["Correios", "J&T Express", "Braspress", "Azul Cargo", "Jadlog"],
            key="box_selecao_transportadora_estavel"
        )
    with col_inp3:
        nome_cliente_rastreio = st.text_input("Nome do Cliente (Opcional):", placeholder="Ex: Maria Silva", key="campo_nome_cliente_estavel").strip()

    btn_gerar_mensagem = st.button("🔍 BUSCAR E GERAR RASTREIO", type="primary", use_container_width=True, key="action_processar_rastreio")
    st.markdown('</div>', unsafe_allow_html=True)

    if btn_gerar_mensagem:
        st.session_state.stats_total += 1
        if not codigo_rastreio or len(codigo_rastreio) < 3:
            st.session_state.stats_erro += 1
            st.session_state["rastreio_gerado"] = False
            st.markdown("""
                <div class="card-unilog" style="text-align: center; border-top: 4px solid #e74c3c;">
                    <div style="font-size: 40px;">⚠️</div>
                    <h3 style="color:#2c3e50; margin: 10px 0;">Objeto não encontrado</h3>
                    <p style="color:#7f8c8d;">Por favor, digite um código de rastreio ou número de Nota Fiscal válido.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.session_state.stats_sucesso += 1
            st.session_state["rastreio_gerado"] = True

    # EXIBIÇÃO DO CARD DE RESULTADO / TIMELINE E AÇÕES
    if st.session_state.get("rastreio_gerado", False) and codigo_rastreio:
        
        # Lógica de Links e Status Dinâmicos
        link_rastreio_final = ""
        status_badge = "EM TRÂNSITO"
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        
        if transportadora_rastreio == "Correios":
            link_rastreio_final = f"https://rastreamento.correios.com.br/app/index.php?objetos={codigo_rastreio}"
        elif transportadora_rastreio == "Jadlog":
            link_rastreio_final = f"https://www.jadlog.com.br/siteInstitucional/tracking.jad?conteudo={codigo_rastreio}"
        elif transportadora_rastreio == "J&T Express":
            link_rastreio_final = "https://www.jtexpress.com.br/trajectoryQuery"
        elif transportadora_rastreio == "Braspress":
            link_rastreio_final = "https://www.braspress.com.br/"
        elif transportadora_rastreio == "Azul Cargo":
            link_rastreio_final = f"https://www.azullogistica.com.br/Rastreio/Rastrear?awb={codigo_rastreio}"

        txt_saudacao = f"Olá, *{nome_cliente_rastreio}*!" if nome_cliente_rastreio else "Olá!"
        mensagem_rastreio_whats = (
            f"{txt_saudacao} 👋\n\n"
            f"Seu pedido da *Cia do Jeans* já está a caminho!\n"
            f"🚚 *Transportadora:* {transportadora_rastreio}\n"
            f"📦 *Código/NF:* `{codigo_rastreio}`\n"
            f"📅 *Atualização:* Objeto em Trânsito ({data_hoje})\n\n"
            f"🔗 *Acompanhe seu envio aqui:*\n{link_rastreio_final}"
        )

        st.markdown('<div class="card-unilog">', unsafe_allow_html=True)
        
        # Cabeçalho do Card
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 20px;">
                <div>
                    <span style="font-size: 11px; font-weight: bold; color: #7f8c8d; text-transform: uppercase;">CÓDIGO DE RASTREIO</span>
                    <h2 style="color: #2c3e50; margin: 0; font-size: 22px;">{codigo_rastreio}</h2>
                </div>
                <div style="background: #d4edda; color: #155724; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: bold;">
                    {status_badge}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Timeline Estilizada
        st.markdown(f"""
            <div class="timeline">
                <div class="timeline-item">
                    <div class="timeline-marker">
                        <div class="marker-circle"></div>
                        <div class="marker-line"></div>
                    </div>
                    <div class="timeline-content">
                        <span>{data_hoje} - 10:45</span>
                        <h4>Objeto em trânsito</h4>
                        <p>Encaminhado para a Unidade de Distribuição da transportadora ({transportadora_rastreio}).</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-marker">
                        <div class="marker-circle" style="background:#bdc3c7; border:none;"></div>
                    </div>
                    <div class="timeline-content">
                        <span>{data_hoje} - 08:20</span>
                        <h4>Objeto Postado / Coletado</h4>
                        <p>A encomenda foi recebida na unidade de expedição da Cia do Jeans.</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border:0; border-top:1px solid #eee; margin:20px 0;'>", unsafe_allow_html=True)

        # Área de Ações
        texto_rastreio_editavel = st.text_area("Mensagem de Rastreio para Envio:", value=mensagem_rastreio_whats, height=150, key="txt_area_rastreio_unilog")
        
        col_btn_ras1, col_btn_ras2 = st.columns(2)
        
        with col_btn_ras1:
            texto_rastreio_codificado = urllib.parse.quote(texto_rastreio_editavel)
            link_whatsapp_rastreio = f"https://api.whatsapp.com/send?text={texto_rastreio_codificado}"
            st.markdown(f"""
                <a href="{link_whatsapp_rastreio}" target="_blank" style="text-decoration: none;">
                    <div style="background:#25D366; color:white; border:none; padding:12px; border-radius:50px; text-align:center; font-weight:bold; cursor:pointer; box-shadow:0 4px 12px rgba(37,211,102,0.3);">
                        📲 Enviar no WhatsApp
                    </div>
                </a>
            """, unsafe_allow_html=True)
            
        with col_btn_ras2:
            if st.button("📋 Copiar Texto do Rastreio", use_container_width=True, key="btn_pure_copy_rastreio"):
                texto_rastreio_js_safe = texto_rastreio_editavel.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('\n', '\\n')
                st.components.v1.html(f"""
                    <script>
                    parent.navigator.clipboard.writeText(`{texto_rastreio_js_safe}`);
                    alert("Rastreio copiado com sucesso! 🎉");
                    </script>
                """, height=0)

        # Opcional: Visualização em iframe
        st.markdown("<br>", unsafe_allow_html=True)
        btn_abrir_painel = st.checkbox("🖥️ Visualizar site da transportadora incorporado", value=False, key="check_painel_integrated")
        if btn_abrir_painel:
            st.markdown(f"👉 _Caso fique em branco, [CLIQUE AQUI PARA ABRIR O SITE DA TRANSPORTADORA]({link_rastreio_final})._")
            st.components.v1.html(
                f'<iframe src="{link_rastreio_final}" width="100%" height="500px" style="border: 1px solid #e2e8f0; border-radius: 12px; background: white;"></iframe>',
                height=520
            )

        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# DASHBOARD ADMIN DE ESTATÍSTICAS (ACESSÍVEL PELO ÍCONE ⚙️)
# ==============================================================================
st.markdown("<br><br>", unsafe_allow_html=True)
col_foot_left, col_foot_right = st.columns([0.95, 0.05])

with col_foot_right:
    st.button("⚙️", key="btn_toggle_admin", on_click=alternar_admin, help="Abrir Painel Admin de Estatísticas")

if st.session_state.exibir_admin:
    st.markdown('<div class="card-unilog" style="border-top: 4px solid #34495e;">', unsafe_allow_html=True)
    st.markdown('<div class="card-header-title">📊 Dashboard UniLog / Cia do Jeans</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="stats-grid">
            <div class="stat-card total">
                <h3>Total de Buscas</h3>
                <p>{st.session_state.stats_total}</p>
            </div>
            <div class="stat-card success">
                <h3>Sucessos</h3>
                <p>{st.session_state.stats_sucesso}</p>
            </div>
            <div class="stat-card error">
                <h3>Erros / Não Enc.</h3>
                <p>{st.session_state.stats_erro}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Fechar Painel Admin", key="btn_fechar_admin"):
        st.session_state.exibir_admin = False
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
