from collections import Counter
import random
import database

def gerar_sugestoes(todos_os_resultados, concurso, user_id):
    """
    Analisa o histórico de resultados e gera 3 jogos sugeridos.
    """
    if not todos_os_resultados or len(todos_os_resultados) < 10: # Precisa de um histórico mínimo
        print("Histórico de dados insuficiente para gerar sugestões.")
        # Gera um jogo completamente aleatório se não houver dados
        jogo_aleatorio = sorted(random.sample(range(1, 26), 15))
        return [("Jogo Aleatório (dados insuficientes)", jogo_aleatorio)]

    print("\nGerando sugestões com base no histórico completo...")

    # 1. Análise de Frequência
    todas_as_dezenas = [dezena for resultado in todos_os_resultados for dezena in resultado[1]]
    frequencia = Counter(todas_as_dezenas)
    ranking = frequencia.most_common()

    # Separa as dezenas em 3 grupos: mais frequentes, intermediárias e menos frequentes
    numeros_quentes = [num for num, count in ranking[:8]]
    numeros_mornos = [num for num, count in ranking[8:17]]
    numeros_frios = [num for num, count in ranking[17:]]

    # 2. Gerar Sugestões com base em estratégias

    # Jogo 1: Foco nos números quentes
    sugestao_1 = []
    sugestao_1.extend(random.sample(numeros_quentes, 8)) # 8 quentes
    sugestao_1.extend(random.sample(numeros_mornos, 5))  # 5 mornos
    sugestao_1.extend(random.sample(numeros_frios, 2))   # 2 frios
    sugestao_1 = sorted(sugestao_1)

    # Jogo 2: Foco nos números frios (Atrasados)
    sugestao_2 = []
    sugestao_2.extend(random.sample(numeros_frios, 7))   # 7 frios
    sugestao_2.extend(random.sample(numeros_mornos, 5))  # 5 mornos
    sugestao_2.extend(random.sample(numeros_quentes, 3)) # 3 quentes
    sugestao_2 = sorted(sugestao_2)

    # Jogo 3: Jogo Equilibrado
    sugestao_3 = []
    sugestao_3.extend(random.sample(numeros_quentes, 5))
    sugestao_3.extend(random.sample(numeros_mornos, 5))
    sugestao_3.extend(random.sample(numeros_frios, 5))
    sugestao_3 = sorted(sugestao_3)

    sugestoes_geradas = [
        ("Jogo 1 (Foco em números 'quentes')", sugestao_1),
        ("Jogo 2 (Aposta nos números 'frios')", sugestao_2),
        ("Jogo 3 (Combinação equilibrada)", sugestao_3)
    ]

    # Salva as sugestões no banco de dados
    for tipo, numeros in sugestoes_geradas:
        database.salvar_sugestao(user_id, concurso, numeros, tipo)

    # 3. Retornar os resultados
    return sugestoes_geradas
