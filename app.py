import base64
import urllib.parse
import pandas as pd
import requests
import streamlit as st

# Configurações do Token Frenet
FRENET_TOKEN = "96BCC656R0FA4R4CBERBCE2R86EF8956C1BA"
FRENET_CEP_ORIGEM = "76320464"  # CEP de Origem padrão (Jaraguá - GO)

# 1. Configuração de Design da Página
st.set_page_config(
    page_title="Cia do Jeans - Calculadora Inteligente",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CONTROLE DE NAVEGAÇÃO À PROVA DE REFRESH (SESSION STATE)
if "tela_ativa" not in st.session_state:
    st.session_state.tela_ativa = "cotacao"
if "cidade_input_fiel" not in st.session_state:
    st.session_state["cidade_input_fiel"] = ""
if "uf_input_fiel" not in st.session_state:
    st.session_state["uf_input_fiel"] = ""
if "rastreio_gerado" not in st.session_state:
    st.session_state["rastreio_gerado"] = False


# Função de cotação via API da Frenet (Cota J&T, Correios, Jadlog)
def cotar_frenet(
    cep_destino, peso, comp, larg, alt, valor_declarado, num_volumes=1
):
    if not FRENET_TOKEN or FRENET_TOKEN == "SEU_TOKEN_FRENET_AQUI":
        return []

    url = "https://api.frenet.com.br/shipping/quote"
    headers = {
        "Content-Type": "application/json",
        "token": FRENET_TOKEN,
    }

    payload = {
        "SellerCEP": FRENET_CEP_ORIGEM,
        "RecipientCEP": str(cep_destino).replace("-", "").replace(" ", ""),
        "ShipmentInvoiceValue": valor_declarado,
        "ShippingItemArray": [
            {
                "Weight": max(peso / num_volumes, 0.1),
                "Length": max(comp, 16),
                "Height": max(alt, 2),
                "Width": max(larg, 11),
                "Quantity": num_volumes,
            }
        ],
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=4)
        if res.status_code == 200:
            dados = res.json()
            servicos = []
            for op in dados.get("ShippingSevicesArray", []):
                if not op.get("Error"):
                    nome_transp = op.get("Carrier", "").upper()
                    nome_servico = op.get("ServiceDescription", "")
                    preco = op.get("ShippingPrice", 0.0)
                    prazo = op.get("DeliveryTime", "-")
                    servicos.append({
                        "TRANSPORTADORA": f"{nome_transp} ({nome_servico})",
                        "VALOR_MINIMO": f"{preco:.2f}".replace(".", ","),
                        "PRAZO": f"{prazo} Dias",
                        "ROTA_ENVIO": "Cotação Online API",
                        "FONE": "Atendimento Online",
                        "EXIGE_NF": "Sim",
                    })
            return servicos
    except Exception:
        pass
    return []


# Funções de clique rápido
def mudar_para_cotacao():
    st.session_state.tela_ativa = "cotacao"


def mudar_para_rastreio():
    st.session_state.tela_ativa = "rastreio"


# Estilização CSS Ultra Moderna
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f8fafc !important;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: #0f172a;
        }
        
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
            max-width: 1140px !important;
        }
        
        .bloco-etapa {
            background-color: #ffffff;
            padding: 28px;
            border-radius: 16px;
            box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
            margin-bottom: 24px;
            border: 1px solid #e2e8f0;
            position: relative;
            overflow: hidden;
        }
        .bloco-etapa::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        }
        
        .titulo-etapa {
            color: #0f172a;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .card-frete {
            background-color: #ffffff;
            padding: 20px 24px;
            border-radius: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #e2e8f0;
            transition: all 0.2s ease;
        }
        
        div.stButton > button[key="trigger_calculo"], div.stButton > button[key="action_processar_rastreio"] {
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            padding: 16px 28px !important;
            border-radius: 12px !important;
            border: none !important;
            box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.4) !important;
        }

        div.stButton > button[key="btn_pure_copy_frete"], div.stButton > button[key="btn_pure_copy_rastreio"] {
            background-color: #0f172a !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            padding: 14px !important;
            border-radius: 10px !important;
            border: none !important;
            width: 100% !important;
            margin-top: 8px !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# CACHE: Organização dos dados da planilha de fretes fixos
@st.cache_data(ttl=3600)
def carregar_e_limpar_dados():
    try:
        df = pd.read_excel(
            "SISTEMA_DE_FRETES_AUTOMATIZADO.xlsx", sheet_name="Plan1"
        )
    except Exception:
        return pd.DataFrame()

    df.columns = [str(c).strip().upper() for c in df.columns]

    pares = [
        (
            "TRANSPORTADORA",
            "ENVIO",
            "FONE",
            "PRAZO",
            "FRETE",
            "NF",
            "VALOR MINIMO A PARTIR DE",
        ),
        (
            "TRANPORTADORA 2",
            "ENVIO 2",
            "FONE 2",
            "PRAZO 2",
            "FRETE 2",
            "NF 2",
            "VALOR MINIMO 2",
        ),
        (
            "TRANSPORTADORA 3",
            "ENVIO 3",
            "FONE 3",
            "PRAZO 3",
            "FRETE 3",
            "NF 3",
            "VALOR 3",
        ),
        (
            "TRANSPORTADORA 4",
            "ENVIO 4",
            "FONE 4",
            "PRAZO 4",
            "FRETE 4",
            "NF 4",
            "VALOR 4",
        ),
        (
            "TRANSPORTADORA 5",
            "ENVIO 5",
            "FONE 5",
            "PRAZO 5",
            "FRETE 5",
            "NF 5",
            "VALOR 5",
        ),
        (
            "TRANSPORTADORA 6",
            "ENVIO 6",
            "FONE2",
            "PRAZO 6",
            "FRETE 6",
            "NF 6",
            "VALOR 6",
        ),
        (
            "TRANSPORTADORA 7",
            "ENVIO 7",
            "FONE 7",
            "PRAZO 7",
            "FRETE 7",
            "NF 7",
            "VALOR MINIMO 7",
        ),
    ]

    cidade_col = (
        [c for c in df.columns if "CIDADE" in c][0]
        if any("CIDADE" in c for c in df.columns)
        else None
    )
    uf_col = (
        [c for c in df.columns if "UF" in c][0]
        if any("UF" in c for c in df.columns)
        else None
    )

    if not cidade_col or not uf_col:
        return pd.DataFrame()

    linhas = []
    for _, r in df.iterrows():
        cidade = str(r[cidade_col]).strip().upper()
        uf = str(r[uf_col]).strip().upper()
        if not cidade or cidade in ["NAN", "-", ""] or uf in ["NAN", "-", ""]:
            continue

        for t_col, env_col, fon_col, prz_col, frt_col, nf_col, val_col in pares:

            def buscar(nome):
                for c in df.columns:
                    if c.replace(" ", "") == nome.replace(" ", ""):
                        val = r[c]
                        return str(val).strip() if pd.notna(val) else "-"
                return "-"

            t_name = buscar(t_col)
            if t_name and t_name not in ["-", "0", "NAN", ""]:
                linhas.append({
                    "CIDADE": cidade,
                    "UF": uf,
                    "TRANSPORTADORA": t_name,
                    "ROTA_ENVIO": buscar(env_col),
                    "FONE": buscar(fon_col),
                    "PRAZO": buscar(prz_col),
                    "TIPO_FRETE": buscar(frt_col),
                    "EXIGE_NF": buscar(nf_col),
                    "VALOR_MINIMO": buscar(val_col),
                })
    return pd.DataFrame(linhas)


df_fretes_fixos = carregar_e_limpar_dados()


# Imagem
def arrumar_imagem_local(caminho):
    try:
        with open(caminho, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return ""


img_base64 = arrumar_imagem_local("logo_ciadojeans.PNG")

# Cabeçalho
st.markdown(
    f"""
    <div style='background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #1e40af 100%); padding: 12px 16px 14px 16px; border-radius: 16px; text-align: center; margin-bottom: 24px; box-shadow: 0 12px 20px -5px rgba(15, 23, 42, 0.2); position: relative; overflow: hidden;'>
        <div style='margin: 0 auto; position: relative; z-index: 2;'>
            <img src="data:image/png;base64,{img_base64}" style="display: block; margin: 0 auto; width: 900px; max-width: 98%; height: auto; max-height: 280px; object-fit: contain;">
        </div>
        <div style='position: relative; z-index: 2; margin-top: -6px;'>
            <p style='color: #93c5fd; font-weight: 600; margin: 0; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 2px;'>
                ⚡ Logística & Cotação Inteligente
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Abas
col_aba1, col_aba2 = st.columns(2)

with col_aba1:
    st.button(
        "📊 COTAR NOVO FRETE",
        use_container_width=True,
        key="aba_cot_btn",
        on_click=mudar_para_cotacao,
    )

with col_aba2:
    st.button(
        "📦 RASTREAR ENCOMENDA",
        use_container_width=True,
        key="aba_ras_btn",
        on_click=mudar_para_rastreio,
    )

st.markdown("<br>", unsafe_allow_html=True)


# --- COTAÇÃO ---
if st.session_state.tela_ativa == "cotacao":

    # PASSO 1: LOCALIZAÇÃO
    st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
    st.markdown(
        '<div class="titulo-etapa">📍 PASSO 1: Destino do Pedido</div>',
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1.5, 2, 1])

    with col1:
        cep_input = st.text_input(
            "📬 Digite o CEP do Cliente:",
            placeholder="00000000",
            max_chars=9,
            key="cep_input_fiel",
        )

    desabilitar_campos = False

    if cep_input:
        cep_limpo = cep_input.replace("-", "").replace(" ", "")
        if len(cep_limpo) == 8 and cep_limpo.isdigit():
            try:
                url_api = f"https://opencep.com/v1/{cep_limpo}"
                resposta = requests.get(url_api, timeout=3).json()
                if "localidade" in resposta and resposta.get("localidade"):
                    st.session_state["cidade_input_fiel"] = resposta.get(
                        "localidade", ""
                    ).upper()
                    st.session_state["uf_input_fiel"] = resposta.get(
                        "uf", ""
                    ).upper()
                    desabilitar_campos = True
                else:
                    desabilitar_campos = False
            except Exception:
                desabilitar_campos = False

    with col2:
        cidade_automatica = st.text_input(
            "📍 Cidade Identificada:",
            placeholder="Digite a Cidade se não buscar...",
            disabled=desabilitar_campos,
            key="cidade_input_fiel",
        )

    with col3:
        uf_automatica = st.text_input(
            "🏳️ UF:",
            placeholder="EX: GO",
            disabled=desabilitar_campos,
            key="uf_input_fiel",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # PASSO 2: PRODUTOS
    st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
    st.markdown(
        '<div class="titulo-etapa">👖 PASSO 2: O que estamos enviando'
        ' hoje?</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        qtd_calcas = st.number_input(
            "Quantidade de Calças:", min_value=0, value=0, step=1, key="calc_un"
        )
        qtd_bermudas = st.number_input(
            "Quantidade de Bermudas:",
            min_value=0,
            value=0,
            step=1,
            key="berm_un",
        )
        qtd_shorts = st.number_input(
            "Quantidade de Shorts:", min_value=0, value=0, step=1, key="shor_un"
        )
        qtd_camisas = st.number_input(
            "Quantidade de Camisas:", min_value=0, value=0, step=1, key="cam_un"
        )
        qtd_saias = st.number_input(
            "Quantidade de Saias:", min_value=0, value=0, step=1, key="saia_un"
        )
        qtd_croppeds = st.number_input(
            "Quantidade de Croppeds:",
            min_value=0,
            value=0,
            step=1,
            key="crop_un",
        )

    with c2:
        qtd_gola_o = st.number_input(
            "Quantidade de Gola O:", min_value=0, value=0, step=1, key="gola_un"
        )
        qtd_tshirt = st.number_input(
            "Quantidade de T-Shirt:", min_value=0, value=0, step=1, key="tsh_un"
        )
        qtd_polo = st.number_input(
            "Quantidade de Gola Polo:",
            min_value=0,
            value=0,
            step=1,
            key="polo_un",
        )
        qtd_vestidos = st.number_input(
            "Quantidade de Vestidos:",
            min_value=0,
            value=0,
            step=1,
            key="vest_un",
        )
        qtd_conjuntos = st.number_input(
            "Quantidade de Conjuntos:",
            min_value=0,
            value=0,
            step=1,
            key="conj_un",
        )
        qtd_bones = st.number_input(
            "Quantidade de Bonés:", min_value=0, value=0, step=1, key="bone_un"
        )

    peso_pecas_puro = (
        (qtd_calcas * 0.60)
        + (qtd_bermudas * 0.40)
        + (qtd_shorts * 0.35)
        + (qtd_gola_o * 0.28)
        + (qtd_tshirt * 0.20)
        + (qtd_polo * 0.32)
        + (qtd_vestidos * 0.55)
        + (qtd_conjuntos * 0.50)
        + (qtd_bones * 0.10)
        + (qtd_camisas * 0.25)
        + (qtd_saias * 0.30)
        + (qtd_croppeds * 0.15)
    )
    peso_total_calculado = peso_pecas_puro + (
        0.4 if peso_pecas_puro > 0 else 0
    )
    total_pecas = (
        qtd_calcas
        + qtd_bermudas
        + qtd_shorts
        + qtd_gola_o
        + qtd_tshirt
        + qtd_polo
        + qtd_vestidos
        + qtd_conjuntos
        + qtd_bones
        + qtd_camisas
        + qtd_saias
        + qtd_croppeds
    )

    with c3:
        valor_manual_nf_txt = st.text_input(
            "✍️ Valor Real da NF (Opcional):",
            placeholder="Ex: 1250,00",
            key="nf_manual_txt",
        ).strip()

        valor_manual_nf = 0.0
        if valor_manual_nf_txt:
            try:
                valor_manual_nf = float(
                    valor_manual_nf_txt.replace(".", "").replace(",", ".")
                )
            except ValueError:
                st.error("⚠️ Digite um valor numérico válido para a NF.")

        meio_envio_selecionado = st.selectbox(
            "📦 Regra de Divisão do Fardo:",
            [
                "Padrão (Dividir acima de 50 kg)",
                "Correios / J&T / Azul Cargo (Dividir acima de 30 kg)",
                "Não Dividir fardo",
            ],
            key="box_regra_divisao_fardo",
        )

        num_volumes = 1
        if total_pecas > 0:
            if (
                meio_envio_selecionado == "Padrão (Dividir acima de 50 kg)"
                and peso_total_calculado > 50.0
            ):
                num_volumes = int(peso_total_calculado // 50) + (
                    1 if peso_total_calculado % 50 > 0 else 0
                )
            elif (
                meio_envio_selecionado
                == "Correios / J&T / Azul Cargo (Dividir acima de 30 kg)"
                and peso_total_calculado > 30.0
            ):
                num_volumes = int(peso_total_calculado // 30) + (
                    1 if peso_total_calculado % 30 > 0 else 0
                )
            elif meio_envio_selecionado == "Não Dividir fardo":
                num_volumes = 1

        peso_por_volume = (
            peso_total_calculado / num_volumes if num_volumes > 0 else 0
        )
        pecas_por_volume = (
            total_pecas // num_volumes if num_volumes > 0 else 0
        )

        if total_pecas == 0:
            tipo_embalagem = "Nenhum produto"
            comp, larg, alt = 0, 0, 0
            classificacao_tamanho = "Sem Carga"
        elif pecas_por_volume <= 15:
            tipo_embalagem = (
                "Caixa Pequena"
                if num_volumes == 1
                else f"{num_volumes} Caixas Pequenas"
            )
            comp, larg, alt = 40, 30, 20
            classificacao_tamanho = "PP (Caixa Pequena)"
        elif pecas_por_volume <= 30:
            tipo_embalagem = (
                "Caixa Média"
                if num_volumes == 1
                else f"{num_volumes} Caixas Médias"
            )
            comp, larg, alt = 50, 40, 30
            classificacao_tamanho = "P (Caixa Média)"
        elif pecas_por_volume <= 60:
            tipo_embalagem = (
                "Fardo Comercial"
                if num_volumes == 1
                else f"{num_volumes} Fardos Comerciais"
            )
            comp, larg, alt = 60, 45, 35
            classificacao_tamanho = "M (Fardo Padrão)"
        elif pecas_por_volume <= 120:
            tipo_embalagem = (
                "Fardo Comercial"
                if num_volumes == 1
                else f"{num_volumes} Fardos Comerciais"
            )
            comp, larg, alt = 80, 50, 40
            classificacao_tamanho = "G (Fardo Grande)"
        else:
            tipo_embalagem = (
                "Fardo Comercial"
                if num_volumes == 1
                else f"{num_volumes} Fardos Comerciais"
            )
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
            (qtd_calcas * 40)
            + (qtd_bermudas * 33)
            + (qtd_shorts * 33)
            + (qtd_gola_o * 18)
            + (qtd_tshirt * 19)
            + (qtd_polo * 25)
            + (qtd_vestidos * 45)
            + (qtd_conjuntos * 50)
            + (qtd_bones * 15)
            + (qtd_camisas * 30)
            + (qtd_saias * 35)
            + (qtd_croppeds * 20)
        )
        valor_para_seguro = (
            valor_manual_nf if valor_manual_nf > 0 else valor_nf_meia
        )

        txt_volumes_resumo = (
            f" ({num_volumes} Vol. de {peso_por_volume:.2f} kg)"
            if num_volumes > 1
            else ""
        )
        st.info(
            f"**📊 Resumo do Pedido:**\n* **Carga:** {total_pecas} un |"
            f" {peso_total_calculado:.2f} kg{txt_volumes_resumo}\n*"
            f" **Embalagem:** {tipo_embalagem}\n* **Seguro:** R$"
            f" {valor_para_seguro:.2f}"
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # DISPARADOR
    st.markdown("<br>", unsafe_allow_html=True)
    btn_calcular = st.button(
        "🚀 CALCULAR FRETE E GERAR WHATSAPP",
        type="primary",
        use_container_width=True,
        key="trigger_calculo",
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # RESULTADOS
    if btn_calcular or st.session_state.get("frete_calculado_ok", False):
        st.session_state["frete_calculado_ok"] = True
        cidade_busca = (
            st.session_state.get("cidade_input_fiel", "").strip().upper()
        )
        uf_busca = st.session_state.get("uf_input_fiel", "").strip().upper()

        if not cidade_busca:
            st.error(
                "❌ Por favor, informe um CEP ou preencha a Cidade no Passo 1."
            )
        elif total_pecas == 0:
            st.error(
                "❌ Insira a quantidade de produtos no Passo 2 para calcular."
            )
        else:
            opcoes_whatsapp = []

            # 1. COTAÇÃO FRENET (ONLINE)
            if cep_input:
                cotacoes_api = cotar_frenet(
                    cep_input,
                    peso_total_calculado,
                    comp,
                    larg,
                    alt,
                    valor_para_seguro,
                    num_volumes,
                )
                for item in cotacoes_api:
                    opcoes_whatsapp.append(
                        f"🚛 *{item['TRANSPORTADORA']}*\n💰 Valor:"
                        f" R$ {item['VALOR_MINIMO']}\n⏱️ Prazo:"
                        f" {item['PRAZO']}\n"
                    )
                    st.markdown(
                        f"""
                    <div class="card-frete" style="border-left: 5px solid #2563eb;">
                        <div>
                            <strong style="font-size:16px; color:#0f172a;"><b>🚛 {item['TRANSPORTADORA']}</b></strong><br>
                            <span style="font-size:13px; color:#64748b;">📍 Rota: {item['ROTA_ENVIO']} | 📞 {item['FONE']}</span><br>
                            <span style="font-size:12px; color:#94a3b8;">⏱️ Prazo: {item['PRAZO']} | 📄 Exige NF: {item['EXIGE_NF']}</span>
                        </div>
                        <div style="text-align: right;"><span style="font-size:12px; color:#64748b; font-weight:600;">Valor Frete</span><br><span style="font-size:18px; font-weight:700; color:#0f172a;">R$ {item['VALOR_MINIMO']}</span></div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            # 2. COTAÇÃO PLANILHA LOCAL
            if not df_fretes_fixos.empty:
                resultados_fixos = df_fretes_fixos[
                    (df_fretes_fixos["CIDADE"] == cidade_busca)
                    & (df_fretes_fixos["UF"] == uf_busca)
                ]

                if not resultados_fixos.empty:
                    st.markdown(
                        "### 🏁 Transportadoras Regionais (Planilha)"
                    )
                    for idx, row in resultados_fixos.iterrows():
                        print_prazo = str(row["PRAZO"])
                        if (
                            "cotar" not in print_prazo.lower()
                            and "dias" not in print_prazo.lower()
                            and print_prazo != "-"
                        ):
                            print_prazo = f"{print_prazo} Dias"

                        st.markdown(
                            f"""
                        <div class="card-frete" style="border-left: 5px solid #1e3a8a;">
                            <div>
                                <strong style="font-size:16px; color:#0f172a;"><b>🚛 {row['TRANSPORTADORA']}</b></strong><br>
                                <span style="font-size:13px; color:#64748b;">📍 Rota: {row['ROTA_ENVIO']} | 📞 Fone: {row['FONE']}</span><br>
                                <span style="font-size:12px; color:#94a3b8;">⏱️ Prazo: {print_prazo} | 📄 Exige NF: {row['EXIGE_NF']}</span>
                            </div>
                            <div style="text-align: right;"><span style="font-size:12px; color:#64748b; font-weight:600;">Mínimo</span><br><span style="font-size:18px; font-weight:700; color:#0f172a;">R$ {row['VALOR_MINIMO']}</span></div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        opcoes_whatsapp.append(
                            f"🚛 *{row['TRANSPORTADORA']}*\n"
                            f"💰 Mínimo: R$ {row['VALOR_MINIMO']}\n"
                            f"⏱️ Prazo: {print_prazo}\n"
                            f"📞 Contato: {row['FONE']}\n"
                        )

            # PASSO 3: WHATSAPP
            if opcoes_whatsapp:
                st.markdown(
                    '<div class="bloco-etapa" style="border-top-color:'
                    ' #25d366;">',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="titulo-etapa" style="color: #16a34a;">💬 PASSO'
                    " 3: Enviar Cotação ao Cliente</div>",
                    unsafe_allow_html=True,
                )

                texto_opcoes = "\n".join(opcoes_whatsapp)
                txt_whatsapp_volumes = (
                    f"{num_volumes} fardos" if num_volumes > 1 else "1 fardo"
                )

                mensagem_vendedor = (
                    "Olá! Segue a cotação de frete para o seu pedido da *Cia do"
                    " Jeans*:\n\n"
                    f"📍 *Destino:*\n{cidade_busca} - {uf_busca}\n\n"
                    f"📦 *Volume estimado:*\n{total_pecas} peças"
                    f" ({peso_total_calculado:.2f} kg) - Dividido em"
                    f" {txt_whatsapp_volumes}\n\n"
                    f"🛍️ *Embalagem:*\n{tipo_embalagem}"
                    f" ({classificacao_tamanho}) - Medidas unitárias:"
                    f" {comp}x{larg}x{alt} cm ({orientacao_texto})\n\n"
                    "-----------------------------------------\n"
                    "🚚 *OPÇÕES DE ENVIO:*\n\n"
                    f"{texto_opcoes}"
                    "-----------------------------------------\n\n"
                    "_Qual destas opções fica melhor para fazermos o despacho?_"
                )

                texto_editavel = st.text_area(
                    "Pré-visualização da Mensagem:",
                    value=mensagem_vendedor,
                    height=250,
                    key="txt_area_print",
                )
                texto_codificado = urllib.parse.quote(texto_editavel)
                link_whatsapp = f"https://api.whatsapp.com/send?text={texto_codificado}"

                st.markdown(
                    f"""
                    <a href="{link_whatsapp}" target="_blank" style="text-decoration: none;">
                        <div style="background: linear-gradient(135deg, #25d366 0%, #16a34a 100%); color: white; text-align: center; padding: 16px; border-radius: 12px; font-weight: 700; font-size: 16px; cursor: pointer; margin-bottom: 12px; font-family: sans-serif;">
                            📲 ENVIAR COTAÇÃO PARA O WHATSAPP DO CLIENTE
                        </div>
                    </a>
                """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "📋 COPIAR TEXTO DA COTAÇÃO", key="btn_pure_copy_frete"
                ):
                    texto_js_safe = (
                        texto_editavel.replace("\\", "\\\\")
                        .replace("`", "\\`")
                        .replace("$", "\\$")
                        .replace("\n", "\\n")
                    )
                    st.components.v1.html(
                        f"""
                        <script>
                        parent.navigator.clipboard.writeText(`{texto_js_safe}`);
                        alert("Cotação copiada com sucesso! 🎉");
                        </script>
                    """,
                        height=0,
                    )

                st.markdown("</div>", unsafe_allow_html=True)


# --- RASTREAMENTO ---
elif st.session_state.tela_ativa == "rastreio":
    st.markdown('<div class="bloco-etapa">', unsafe_allow_html=True)
    st.markdown(
        '<div class="titulo-etapa">📦 PASSO ÚNICO: Gerar Rastreio para o'
        " Cliente</div>",
        unsafe_allow_html=True,
    )

    col_nome_cli, col_transp, col_cod, col_doc = st.columns([1.2, 1.2, 1.2, 1])

    with col_nome_cli:
        nome_cliente_rastreio = st.text_input(
            "Nome do Cliente:",
            placeholder="Ex: Maria Silva",
            key="campo_nome_cliente_estavel",
        ).strip()

    with col_transp:
        transportadora_rastreio = st.selectbox(
            "Selecione a Transportadora:",
            ["Correios", "J&T Express", "Braspress", "Azul Cargo", "Jadlog"],
            key="box_selecao_transportadora_estavel",
        )

    with col_cod:
        codigo_rastreio = st.text_input(
            "Código de Rastreio / Nº Nota Fiscal:",
            placeholder="Ex: BR123456789X / 4552",
            key="campo_codigo_estavel",
        ).strip()

    with col_doc:
        doc_cliente = st.text_input(
            "CPF ou CNPJ do Cliente (Se J&T/Braspress):",
            placeholder="Apenas números",
            key="campo_doc_estavel",
        ).strip()

    btn_gerar_mensagem = st.button(
        "⚙️ GERAR INFORMAÇÕES DE RASTREAMENTO",
        type="primary",
        use_container_width=True,
        key="action_processar_rastreio",
    )

    if btn_gerar_mensagem:
        if not codigo_rastreio:
            st.error(
                "⚠️ Por favor, digite o código de rastreio ou número do"
                " documento antes de gerar."
            )
            st.session_state["rastreio_gerado"] = False
        else:
            st.session_state["rastreio_gerado"] = True

    if st.session_state["rastreio_gerado"] and codigo_rastreio:
        link_rastreio_final = ""
        mensagem_rastreio = ""

        txt_saudacao = (
            f"Olá, *{nome_cliente_rastreio}*!"
            if nome_cliente_rastreio
            else "Olá!"
        )

        if transportadora_rastreio == "Correios":
            link_rastreio_final = f"https://rastreamento.correios.com.br/app/index.php?objetos={codigo_rastreio}"
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já foi"
                " despachado! 🎉\n\n"
                "🚚 *Transportadora:* Correios\n"
                f"📦 *Código de Rastreio:* `{codigo_rastreio}`\n\n"
                "🔗 *Clique no link abaixo para acompanhar seu envio:*\n"
                f"{link_rastreio_final}"
            )

        elif transportadora_rastreio == "Jadlog":
            link_rastreio_final = f"https://www.jadlog.com.br/siteInstitucional/tracking.jad?conteudo={codigo_rastreio}"
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já está a"
                " caminho! 🎉\n\n"
                "🚚 *Transportadora:* Jadlog\n"
                f"📦 *Código de Rastreio:* `{codigo_rastreio}`\n\n"
                "🔗 *Clique no link abaixo para acompanhar seu envio:*\n"
                f"{link_rastreio_final}"
            )

        elif transportadora_rastreio == "J&T Express":
            link_rastreio_final = (
                "https://www.jtexpress.com.br/trajectoryQuery"
            )
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já foi"
                " despachado! 🎉\n\n"
                "🚚 *Transportadora:* J&T Express\n"
                f"📦 *Código de Rastreio:* `{codigo_rastreio}`\n\n"
                "🔗 *Como rastrear:*\n"
                f"1. Acesse o site: {link_rastreio_final}\n"
                "2. Digite o seu código de rastreio acima ou o seu CPF/CNPJ."
            )

        elif transportadora_rastreio == "Braspress":
            link_rastreio_final = "https://www.braspress.com.br/"
            doc_info = f" (CNPJ/CPF: {doc_cliente})" if doc_cliente else ""
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já foi"
                " coletado! 🎉\n\n"
                "🚚 *Transportadora:* Braspress\n"
                f"📄 *Número da Nota Fiscal:* `{codigo_rastreio}`{doc_info}\n\n"
                "🔗 *Como rastrear:*\n"
                f"1. Acesse o site: {link_rastreio_final}\n"
                "2. No topo da página, clique em *'Rastreie sua Encomenda'*\n"
                "3. Informe o número da NF acima e o seu CPF/CNPJ."
            )

        elif transportadora_rastreio == "Azul Cargo":
            link_rastreio_final = f"https://www.azullogistica.com.br/Rastreio/Rastrear?awb={codigo_rastreio}"
            mensagem_rastreio = (
                f"{txt_saudacao} Seu pedido da *Cia do Jeans* já está voando"
                " até você! 🎉\n\n"
                "🚚 *Transportadora:* Azul Cargo Express\n"
                f"📦 *Código de Rastreio (AWB):* `{codigo_rastreio}`\n\n"
                "🔗 *Clique no link abaixo para acompanhar seu envio:*\n"
                f"{link_rastreio_final}"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        texto_rastreio_editavel = st.text_area(
            "Pré-visualização da Mensagem de Rastreio:",
            value=mensagem_rastreio,
            height=180,
            key="txt_area_rastreio",
        )
        texto_rastreio_codificado = urllib.parse.quote(texto_rastreio_editavel)
        link_whatsapp_rastreio = f"https://api.whatsapp.com/send?text={texto_rastreio_codificado}"

        st.markdown(
            f"""
            <a href="{link_whatsapp_rastreio}" target="_blank" style="text-decoration: none;">
                <div style="background: linear-gradient(135deg, #25d366 0%, #16a34a 100%); color: white; text-align: center; padding: 16px; border-radius: 12px; font-weight: 700; font-size: 16px; cursor: pointer; margin-bottom: 12px; font-family: sans-serif;">
                    📲 ENVIAR MENSAGEM DE RASTREIO PARA O WHATSAPP
                </div>
            </a>
        """,
            unsafe_allow_html=True,
        )

        if st.button(
            "📋 COPIAR TEXTO DO RASTREIO", key="btn_pure_copy_rastreio"
        ):
            texto_rastreio_js_safe = (
                texto_rastreio_editavel.replace("\\", "\\\\")
                .replace("`", "\\`")
                .replace("$", "\\$")
                .replace("\n", "\\n")
            )
            st.components.v1.html(
                f"""
                <script>
                parent.navigator.clipboard.writeText(`{texto_rastreio_js_safe}`);
                alert("Rastreio copiado com sucesso! 🎉");
                </script>
            """,
                height=0,
            )

    st.markdown("</div>", unsafe_allow_html=True)
