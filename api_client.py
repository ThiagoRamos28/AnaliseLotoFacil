import requests

# URL base da API da Caixa para a Lotofácil
URL_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/"

def get_latest_concurso_info():
    """Busca os dados do último concurso para obter o número total de sorteios."""
    try:
        # O parâmetro verify=False é usado para contornar erros de certificado SSL que podem ocorrer.
        response = requests.get(URL_BASE, verify=False)
        response.raise_for_status()  # Lança um erro para respostas com status 4xx ou 5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao buscar o último concurso: {e}")
        return None

def get_concurso_data(numero_concurso):
    """Busca os dados de um concurso específico."""
    url_concurso = f"{URL_BASE}{numero_concurso}"
    try:
        response = requests.get(url_concurso, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao buscar o concurso {numero_concurso}: {e}")
        return None
