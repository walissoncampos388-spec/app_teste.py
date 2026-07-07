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

# Token Oficial do SuperFrete
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
        "from": { "postal_code": CEP_ORIGEM },
        "to": { "postal_code": cep_destino.replace("-", "").strip() },
        "services": "1,2", 
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
            return {"sucesso": False, "msg": f"Erro na API SuperFrete (Status: {response.status_code})."}
    except Exception:
        return {"sucesso": False, "msg": "Instabilidade
