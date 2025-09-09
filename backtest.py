import pandas as pd
from collections import Counter
import time

# Importa as funções necessárias dos outros módulos
from database import obter_todos_os_resultados
from ml_sugestoes import (
    criar_dataframe_features,
    calcular_features_atraso,
    calcular_features_frequencia,
    calcular_feature_lag,
    calcular_feature_soma,
    treinar_ou_carregar_modelos_e_prever
)

def executar_backtest(periodo_testes):
    """
    Executa uma simulação histórica (backtest) para avaliar a performance da
    estratégia de Machine Learning.

    Args:
        periodo_testes (int): Quantidade de concursos recentes para usar no teste.

    Returns:
        dict: Um dicionário com a distribuição de acertos.
    """    
    if periodo_testes <= 0:
        print("O número de concursos deve ser positivo.")
        return {}

    print("Carregando todo o histórico de resultados...")
    todos_resultados = obter_todos_os_resultados()
    
    if len(todos_resultados) < periodo_testes + 60: # 60 é uma margem de segurança para o treino inicial
        print("Histórico de dados insuficiente para realizar o backtest com esse período.")
        return {}

    print(f"O backtest irá simular o treinamento e a previsão para cada um dos {periodo_testes} concursos.")
    print("Este processo pode ser bastante demorado...")

    # Separa os dados: uma parte para o teste e o resto para o treino inicial
    dados_para_teste = todos_resultados[-periodo_testes:]
    
    resultados_backtest = []

    # Loop principal do backtest
    for i, (concurso_real, dezenas_reais) in enumerate(dados_para_teste):
        start_time = time.time()
        print(f"\nTestando para o concurso {concurso_real} ({i+1}/{periodo_testes})...")

        # Pega todos os resultados que vieram ANTES do concurso que estamos testando
        dados_treino_historico = [r for r in todos_resultados if r[0] < concurso_real]

        # 1. Roda todo o pipeline de features para os dados históricos
        df_resultados_hist = criar_dataframe_features_para_backtest(dados_treino_historico)
        df_atraso_hist = calcular_features_atraso(df_resultados_hist)
        df_frequencia_hist = calcular_features_frequencia(df_resultados_hist)
        df_lag_hist = calcular_feature_lag(df_resultados_hist)
        df_soma_hist = calcular_feature_soma(df_resultados_hist)
        
        df_features_hist = pd.concat([df_resultados_hist, df_atraso_hist, df_frequencia_hist, df_lag_hist, df_soma_hist], axis=1)
        df_features_hist = df_features_hist.dropna()
        for j in range(1, 26):
            if f'lag_{j}' in df_features_hist.columns:
                df_features_hist[f'lag_{j}'] = df_features_hist[f'lag_{j}'].astype(int)
        df_features_hist['soma_dezenas'] = df_features_hist['soma_dezenas'].astype(int)

        # 2. Treina os modelos (sem salvar) e gera a sugestão para o concurso_real
        # Usamos verbose=False para manter o output limpo
        sugestao = treinar_ou_carregar_modelos_e_prever(df_features_hist, force_retrain=True, verbose=False)

        # 3. Compara a sugestão com o resultado real
        acertos = len(set(sugestao).intersection(set(dezenas_reais)))
        resultados_backtest.append(acertos)
        end_time = time.time()
        print(f"Sugestão: {sugestao}")
        print(f"Resultado Real: {dezenas_reais}")
        print(f"=> Acertos: {acertos} (levou {end_time - start_time:.2f}s)")

    # 4. Apresenta o relatório final
    print("--- RELATÓRIO FINAL DO BACKTEST ---")
    contagem_acertos = Counter(resultados_backtest)
    print(f"Período testado: {periodo_testes} concursos.")
    print("Distribuição de acertos:")
    
    # Ordena os resultados por número de acertos (pontos) em ordem decrescente
    resultados_ordenados = sorted(contagem_acertos.items(), key=lambda item: item[0], reverse=True)

    for acertos, contagem in resultados_ordenados:
        print(f"- {acertos} pontos: {contagem} vez(es)")
    
    return resultados_ordenados

def criar_dataframe_features_para_backtest(resultados):
    """ Versão modificada de criar_dataframe_features para o backtest """
    if not resultados:
        return pd.DataFrame()
    dados = []
    for concurso, dezenas in resultados:
        linha = {'concurso': concurso}
        for i in range(1, 26):
            linha[f'dezena_{i}'] = 1 if i in dezenas else 0
        dados.append(linha)
    df = pd.DataFrame(dados)
    df = df.set_index('concurso')
    df = df.sort_index()
    return df

# Exemplo de como usar (para teste)
if __name__ == '__main__':
    executar_backtest(50)
