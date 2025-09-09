
import pandas as pd
import numpy as np
import os
import joblib
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from database import obter_todos_os_resultados
import database

MODEL_DIR = "trained_models"
# Garante que o diretório para salvar os modelos exista
os.makedirs(MODEL_DIR, exist_ok=True)

def criar_dataframe_features():
    """
    Cria um DataFrame do pandas com todos os resultados e a presença de cada dezena.
    """
    # Obter todos os resultados do banco de dados
    resultados = obter_todos_os_resultados()
    if not resultados:
        return pd.DataFrame()

    # Converter para um formato mais fácil de analisar
    dados = []
    for concurso, dezenas in resultados:
        linha = {'concurso': concurso}
        # Adiciona uma coluna para cada dezena, marcando 1 se ela foi sorteada
        for i in range(1, 26):
            linha[f'dezena_{i}'] = 1 if i in dezenas else 0
        dados.append(linha)

    df = pd.DataFrame(dados)
    df = df.set_index('concurso')
    df = df.sort_index()
    
    return df

def calcular_features_atraso(df):
    """
    Calcula o atraso de cada dezena (há quantos concursos não aparece).
    """
    df_atraso = pd.DataFrame(index=df.index)
    for i in range(1, 26):
        dezena_col = f'dezena_{i}'
        # Encontra os concursos em que a dezena apareceu
        sorteios_com_dezena = df[df[dezena_col] == 1].index
        # Calcula o atraso para cada concurso no DataFrame original
        atrasos = []
        for concurso_atual in df.index:
            # Filtra os sorteios que aconteceram antes do concurso atual
            sorteios_passados = sorteios_com_dezena[sorteios_com_dezena < concurso_atual]
            if not sorteios_passados.empty:
                ultimo_sorteio = sorteios_passados.max()
                atraso = concurso_atual - ultimo_sorteio
            else:
                # Se a dezena nunca saiu antes, o atraso é o próprio número do concurso
                atraso = concurso_atual
            atrasos.append(atraso)
        df_atraso[f'atraso_{i}'] = atrasos
    return df_atraso

def calcular_features_frequencia(df):
    """
    Calcula a frequência de cada dezena nas últimas N janelas (10, 20, 50).
    """
    df_frequencia = pd.DataFrame(index=df.index)
    janelas = [10, 20, 50]
    for i in range(1, 26):
        dezena_col = f'dezena_{i}'
        for j in janelas:
            # Usamos shift(1) para que a frequência seja baseada nos jogos *anteriores*
            df_frequencia[f'freq_{j}_{i}'] = df[dezena_col].shift(1).rolling(window=j).sum()
    
    # Remove as linhas que terão valores NaN devido à janela de rolling
    df_frequencia = df_frequencia.dropna()
    return df_frequencia

def calcular_feature_lag(df):
    """
    Cria a feature de lag (se a dezena saiu no concurso anterior).
    """
    df_lag = pd.DataFrame(index=df.index)
    for i in range(1, 26):
        # A feature de lag é simplesmente o resultado da dezena no concurso anterior
        df_lag[f'lag_{i}'] = df[f'dezena_{i}'].shift(1)
    return df_lag

def calcular_feature_soma(df):
    """
    Calcula a soma das dezenas sorteadas para cada concurso.
    """
    df_soma = pd.DataFrame(index=df.index)
    somas = []
    for index, row in df.iterrows():
        # Pega apenas as colunas de dezenas (dezena_1 a dezena_25)
        dezenas_sorteadas_no_concurso = [i for i in range(1, 26) if row[f'dezena_{i}'] == 1]
        somas.append(sum(dezenas_sorteadas_no_concurso))
    
    # Usamos shift(1) para que a feature seja baseada no concurso *anterior*
    df_soma['soma_dezenas'] = pd.Series(somas, index=df.index).shift(1)
    return df_soma

def treinar_ou_carregar_modelos_e_prever(df_features, force_retrain=False, verbose=True):
    """
    Função principal que lida com o treinamento, carregamento e previsão.
    Retorna a sugestão de 15 dezenas.
    `verbose=False` a torna silenciosa para uso em backtesting.
    """
    if verbose:
        print("\nCarregando ou treinando modelos...")

    features_para_prever = df_features.iloc[[-1]]
    probabilidades = {}
    
    for i in range(1, 26):
        model_path = os.path.join(MODEL_DIR, f"modelo_dezena_{i}.joblib")
        model = None

        if not force_retrain and os.path.exists(model_path):
            model = joblib.load(model_path)
        
        if model is None:
            if verbose and force_retrain:
                print(f"Forçando retreinamento do modelo para a dezena {i:02d}...")
            
            feature_cols = [f'atraso_{i}', f'freq_10_{i}', f'freq_20_{i}', f'freq_50_{i}', f'lag_{i}', 'soma_dezenas']
            target_col = f'dezena_{i}'

            X_train = df_features[feature_cols]
            y_train = df_features[target_col]
            
            # model = LogisticRegression(solver='liblinear')
            model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)
            joblib.dump(model, model_path)

        # Realiza a previsão com o modelo (carregado ou recém-treinado)
        feature_cols_predict = [f'atraso_{i}', f'freq_10_{i}', f'freq_20_{i}', f'freq_50_{i}', f'lag_{i}', 'soma_dezenas']
        X_predict = features_para_prever[feature_cols_predict]
        prob = model.predict_proba(X_predict)[0, 1]
        probabilidades[i] = prob

    if verbose:
        print("Modelos processados.")

    dezenas_ordenadas = sorted(probabilidades, key=probabilidades.get, reverse=True)
    sugestao = sorted(dezenas_ordenadas[:15])
    return sugestao

def gerar_sugestao_ml(concurso, user_id, force_retrain=False):
    """
    Orquestra a criação de features e a geração de sugestão, imprimindo os resultados.
    """
    if force_retrain:
        print("\nO retreinamento forçado dos modelos foi solicitado.")

    print("\nIniciando a preparação de dados para Machine Learning...")
    
    df_resultados = criar_dataframe_features()

    if len(df_resultados) < 60:
        print("\nDados insuficientes para treinar os modelos. Atualize o banco de dados.")
        return

    print("Calculando todas as features (Atraso, Frequência, Lag, Soma)...")
    df_atraso = calcular_features_atraso(df_resultados)
    df_frequencia = calcular_features_frequencia(df_resultados)
    df_lag = calcular_feature_lag(df_resultados)
    df_soma = calcular_feature_soma(df_resultados)

    df_features = pd.concat([df_resultados, df_atraso, df_frequencia, df_lag, df_soma], axis=1)
    df_features = df_features.dropna()
    for i in range(1, 26):
        df_features[f'lag_{i}'] = df_features[f'lag_{i}'].astype(int)
    df_features['soma_dezenas'] = df_features['soma_dezenas'].astype(int)

    print("\nEngenharia de Features Concluída!")

    sugestao = treinar_ou_carregar_modelos_e_prever(df_features, force_retrain=force_retrain, verbose=True)

    # Salva a sugestão no banco de dados
    database.salvar_sugestao(user_id, concurso, sugestao, "Machine Learning")

    return sugestao


# Exemplo de como usar (para teste)
if __name__ == '__main__':
    gerar_sugestao_ml()
