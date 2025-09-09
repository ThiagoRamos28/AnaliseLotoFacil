import time
import api_client
import database
import sugestoes
import ml_sugestoes
import backtest

def atualizar_banco_de_dados():
    """Busca por novos resultados da Lotofácil e atualiza o banco de dados."""
    print("Iniciando atualização do banco de dados...")
    
    # 1. Descobrir qual o último concurso salvo no nosso banco
    ultimo_concurso_salvo = database.obter_ultimo_concurso_salvo()
    print(f"Último concurso encontrado no banco de dados: {ultimo_concurso_salvo}")

    # 2. Descobrir qual o último concurso que saiu no site da Caixa
    dados_ultimo_concurso_api = api_client.get_latest_concurso_info()
    if not dados_ultimo_concurso_api:
        return # Encerra se não conseguir contato com a API

    numero_ultimo_concurso_api = dados_ultimo_concurso_api.get('numero')
    print(f"Último concurso disponível na API da Caixa: {numero_ultimo_concurso_api}")

    # 3. Baixar e salvar apenas os concursos que faltam
    concursos_a_baixar = range(ultimo_concurso_salvo + 1, numero_ultimo_concurso_api + 1)

    if not concursos_a_baixar:
        print("Seu banco de dados já está atualizado!")
        return

    print(f"Encontrados {len(concursos_a_baixar)} novos concursos para adicionar ao banco.")

    for numero_concurso in concursos_a_baixar:
        print(f"Buscando dados do concurso {numero_concurso}...")
        dados_concurso = api_client.get_concurso_data(numero_concurso)
        if dados_concurso and dados_concurso.get('listaDezenas'):
            dezenas = [int(d) for d in dados_concurso['listaDezenas']]
            database.inserir_resultado(numero_concurso, dezenas)
            print(f"Concurso {numero_concurso} salvo com sucesso.")
        else:
            print(f"Falha ao obter dados do concurso {numero_concurso}. Pulando.")
        time.sleep(0.5) # Pausa para não sobrecarregar a API

    print("\nAtualização do banco de dados concluída!")

    # Após atualizar os resultados, verifica e atualiza os acertos das sugestões salvas
    database.atualizar_acertos_sugestoes()

def exibir_sugestoes():
    """Busca os dados do banco e gera as sugestões de jogos."""
    print("\nCarregando histórico de resultados do banco de dados...")
    todos_os_resultados = database.obter_todos_os_resultados()
    if not todos_os_resultados:
        print("O banco de dados está vazio. Por favor, atualize o banco primeiro.")
        return
    
    sugestoes.gerar_sugestoes(todos_os_resultados)

def menu_principal():
    """Exibe o menu principal e gerencia a interação com o usuário."""
    while True:
        print("\n--- Analisador Lotofácil ---")
        print("1. Atualizar Banco de Dados")
        print("2. Gerar Sugestões (Análise de Frequência)")
        print("--- Machine Learning ---")
        print("3. Gerar Sugestão com ML (Rápido, usa modelos salvos)")
        print("4. Atualizar Modelos de ML (Lento, treina com novos dados)")
        print("5. Avaliar Estratégia de ML (Backtest)")
        print("6. Sair")
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            atualizar_banco_de_dados()
        elif escolha == '2':
            exibir_sugestoes()
        elif escolha == '3':
            # Gera sugestão usando modelos já treinados (rápido)
            ml_sugestoes.gerar_sugestao_ml(force_retrain=False)
        elif escolha == '4':
            # Força o retreinamento dos modelos (lento)
            ml_sugestoes.gerar_sugestao_ml(force_retrain=True)
        elif escolha == '5':
            backtest.executar_backtest()
        elif escolha == '6':
            print("Obrigado por usar o programa!")
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    menu_principal()
