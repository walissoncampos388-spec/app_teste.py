# ==============================================================================
# FUNÇÕES DA API DOS CORREIOS (VERSÃO CORRIGIDA COM FALLBACK/SANDBOX AUTOMÁTICO)
# ==============================================================================
@st.cache_data(ttl=600)  # Faz cache do token por 10 minutos
def obter_token_correios(usuario, api_key):
    """Autentica na API oficial dos Correios. Tenta Produção e Sandbox automaticamente."""
    # Definição das URLs de tentativa
    urls = [
        {"ambiente": "PROD", "url": "https://api.correios.com.br/token/v1/autentica"},
        {"ambiente": "SANDBOX", "url": "https://sandbox.correios.com.br/token/v1/autentica"}
    ]
    
    # Prepara a autenticação em Base64
    credenciais = f"{usuario}:{api_key}"
    token_base64 = base64.b64encode(credenciais.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {token_base64}",
        "Content-Type": "application/json"
    }
    
    # Tenta conectar primeiro em Produção, depois em Sandbox caso falhe
    for tentativa in urls:
        try:
            response = requests.post(tentativa["url"], headers=headers, json={}, timeout=5)
            if response.status_code in [200, 201]:
                token = response.json().get("token")
                # Salva no estado qual ambiente deu certo para usarmos no cálculo
                st.session_state["correios_ambiente"] = tentativa["ambiente"]
                return token
        except Exception:
            continue
            
    # Última tentativa: Enviar diretamente a API Key limpa (sem o "usuario:" concatenado)
    # Alguns contratos novos exigem este formato no Basic Auth
    headers_direto = {
        "Authorization": f"Basic {base64.b64encode(api_key.encode()).decode()}",
        "Content-Type": "application/json"
    }
    for tentativa in urls:
        try:
            response = requests.post(tentativa["url"], headers=headers_direto, json={}, timeout=5)
            if response.status_code in [200, 201]:
                token = response.json().get("token")
                st.session_state["correios_ambiente"] = tentativa["ambiente"]
                return token
        except Exception:
            continue
            
    return None

def calcular_frete_correios(token, cep_destino, peso, largura, altura, comprimento, seguro_valor):
    """Consulta a precificação de fretes nacionais (SEDEX e PAC) via API Correios."""
    # Identifica se usaremos o endereço de Produção ou Sandbox baseado no token gerado
    ambiente = st.session_state.get("correios_ambiente", "PROD")
    base_url = "https://api.correios.com.br" if ambiente == "PROD" else "https://sandbox.correios.com.br"
    
    url = f"{base_url}/preco/v1/nacional"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Códigos de Serviço com Contrato vs Sem Contrato
    codigo_sedex = "03298" if CORREIOS_CONTRATO else "04014"
    codigo_pac = "03220" if CORREIOS_CONTRATO else "04510"
    
    payload = {
        "cepOrigem": CORREIOS_CEP_ORIGEM,
        "cepDestino": cep_destino,
        "psObjeto": str(int(peso * 1000)),  # Em gramas
        "tpObjeto": "1",  # Caixa/Pacote
        "nuLargura": int(largura),
        "nuAltura": int(altura),
        "nuComprimento": int(comprimento),
        "vlDeclarado": f"{seguro_valor:.2f}".replace(".", ","),
        "coServico": f"{codigo_sedex},{codigo_pac}"
    }
    
    if CORREIOS_CONTRATO:
        payload["nuContrato"] = CORREIOS_CONTRATO

    resultados = []
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=6)
        if response.status_code == 200:
            dados = response.json()
            for servico in dados:
                co_servico = servico.get("coServico")
                nome_servico = "Correios SEDEX ⚡" if co_servico in [codigo_sedex, "04014", "03298"] else "Correios PAC 📦"
                
                valor = servico.get("pcProduto", "0").replace(",", ".")
                prazo = servico.get("prazoEntrega", "-")
                
                if float(valor) > 0:
                    resultados.append({
                        "TRANSPORTADORA": nome_servico,
                        "ROTA_ENVIO": "Correios Nacional",
                        "FONE": "3003-0100",
                        "PRAZO": f"{prazo} Dias",
                        "EXIGE_NF": "Não",
                        "VALOR_MINIMO": f"{float(valor):.2f}"
                    })
    except Exception:
        pass
    return resultados
