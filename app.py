@st.cache_data(ttl=600)  # Faz cache do token por 10 minutos
def obter_token_correios(usuario, api_key):
    """Autentica na API oficial dos Correios testando múltiplos formatos de credenciais."""
    urls = [
        {"ambiente": "PROD", "url": "https://api.correios.com.br/token/v1/autentica"},
        {"ambiente": "SANDBOX", "url": "https://sandbox.correios.com.br/token/v1/autentica"}
    ]
    
    # FORMATO 1: usuario:api_key (Padrão)
    credenciais_1 = f"{usuario}:{api_key}"
    token_1 = base64.b64encode(credenciais_1.encode()).decode()
    
    # FORMATO 2: usuario:contrato (Alguns sistemas antigos/novos exigem usuário + contrato na autenticação básica)
    credenciais_2 = f"{usuario}:{CORREIOS_CONTRATO}"
    token_2 = base64.b64encode(credenciais_2.encode()).decode()
    
    # FORMATO 3: Apenas a API Key (Para chaves que já vêm pré-codificadas de fábrica)
    token_3 = base64.b64encode(api_key.encode()).decode()

    formatos_headers = [
        {"Authorization": f"Basic {token_1}"},
        {"Authorization": f"Basic {token_2}"},
        {"Authorization": f"Basic {token_3}"}
    ]
    
    for tentativa in urls:
        for headers_auth in formatos_headers:
            headers = {
                "Authorization": headers_auth["Authorization"],
                "Content-Type": "application/json"
            }
            try:
                response = requests.post(tentativa["url"], headers=headers, json={}, timeout=5)
                if response.status_code in [200, 201]:
                    token = response.json().get("token")
                    st.session_state["correios_ambiente"] = tentativa["ambiente"]
                    return token
            except Exception:
                continue
            
    return None
