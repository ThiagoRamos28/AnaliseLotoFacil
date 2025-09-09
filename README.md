# 🎲 Analisador de Resultados da Lotofácil

Este projeto é uma ferramenta para baixar, armazenar e analisar os resultados históricos da Lotofácil. Ele oferece sugestões de jogos com base em análises estatísticas e está sendo expandido para utilizar Machine Learning para identificar padrões mais complexos.

---

## ✨ Funcionalidades Atuais

- **Banco de Dados Local:** Utiliza um banco de dados SQLite (`lotofacil.db`) para armazenar todos os resultados, evitando a necessidade de baixá-los repetidamente.
- **Atualização Eficiente:** A ferramenta verifica o último resultado salvo e baixa apenas os sorteios mais recentes que ainda não estão no banco de dados.
- **Estrutura Modular:** O código é organizado em módulos com responsabilidades bem definidas:
    - `main.py`: A interface de linha de comando (CLI) para interagir com o programa.
    - `database.py`: Gerencia todas as operações do banco de dados.
    - `api_client.py`: Responsável por se comunicar com a API da Caixa e buscar os resultados.
    - `sugestoes.py`: Contém a lógica para as análises e geração de sugestões.
- **Análise de Frequência:** Gera 3 sugestões de jogos com base em uma análise de frequência dos números sorteados:
    1.  **Números "Quentes":** Foco nos números que mais aparecem.
    2.  **Números "Frios":** Aposta nos números que estão há mais tempo sem serem sorteados.
    3.  **Jogo Equilibrado:** Uma combinação balanceada entre os diferentes grupos de frequência.
- **Autenticação de Usuários:** Sistema de login e registro para que cada usuário possa ter seu próprio progresso e sugestões salvas.
- **Sugestões Salvas:** Armazena as sugestões geradas, calcula os acertos com base nos resultados oficiais e permite a exclusão condicional de sugestões pendentes.

---

## 🚀 Como Usar (Interface Web)

A principal forma de interação com o sistema agora é através da interface web.

1.  **Configuração do Ambiente:**
    *   Certifique-se de ter Python 3.x instalado.
    *   Crie e ative um ambiente virtual (recomendado):
        ```bash
        python -m venv venv
        # No Windows
        .\venv\Scripts\activate
        # No macOS/Linux
        source venv/bin/activate
        ```
    *   Instale as dependências:
        ```bash
        pip install Flask Flask-Login Werkzeug pandas numpy scikit-learn joblib requests
        ```

2.  **Executar a Aplicação:**
    ```bash
    python app.py
    ```
3.  **Acessar no Navegador:** Abra seu navegador e acesse `http://127.0.0.1:5000/`.

### ⚙️ Configuração Inicial (Primeiro Acesso)

Ao acessar a aplicação pela primeira vez, você será redirecionado para a página de login. Como não há usuários, você precisará se registrar:

1.  Clique em "Registrar" no menu lateral ou na página de login.
2.  Crie um nome de usuário e senha.
3.  Após o registro, faça login com suas credenciais.

**Nota sobre o Banco de Dados:** O arquivo `lotofacil.db` não é versionado no Git (está no `.gitignore`). Ele será criado automaticamente na primeira vez que você executar a aplicação (`python app.py`) e acessar a página inicial ou tentar atualizar o banco de dados. Os modelos de ML (`trained_models/`) também são ignorados e serão gerados após o primeiro treinamento.

### 🌐 Funcionalidades Disponíveis na Web

A interface web oferece uma experiência de usuário aprimorada com um layout moderno de barra lateral e cards.

*   **Página Inicial:** Exibe o último concurso salvo e as dezenas sorteadas.
*   **Atualizar Banco de Dados:** Busca e salva os resultados mais recentes da Lotofácil. Após a atualização, o sistema automaticamente calcula os acertos das sugestões salvas.
*   **Sugestões Salvas:** Visualiza todas as sugestões de jogos que você salvou, incluindo o número de acertos e o resultado oficial do concurso. Permite excluir sugestões que ainda não tiveram o resultado processado.
*   **Sugestão (Frequência):** Gera sugestões de jogos baseadas em análise de frequência.
*   **Sugestão (ML):** Gera uma sugestão usando modelos de Machine Learning pré-treinados.
*   **Atualizar Modelos ML:** Força o retreinamento dos modelos de Machine Learning (recomendado após atualizar o banco de dados).
*   **Executar Backtest:** Permite rodar um teste histórico para avaliar o desempenho da estratégia de ML, com visualização aprimorada dos resultados.
*   **Indicador de Carregamento:** Um spinner visual é exibido durante operações demoradas para melhorar a experiência do usuário.

---

## 🧠 Sugestão com Machine Learning

Esta funcionalidade avançada utiliza modelos de Machine Learning para gerar sugestões sofisticadas.

**Como Funciona:**

1.  **Engenharia de Features:** Para cada sorteio e para cada dezena (de 1 a 25), o sistema calcula um conjunto de características (features) para "entender" o contexto daquele número:
    - **Atraso:** Há quantos sorteios a dezena não é sorteada.
    - **Frequência:** Quantas vezes a dezena apareceu nos últimos 10, 20 e 50 sorteios.
    - **Lag:** Se a dezena foi sorteada no concurso imediatamente anterior.
    - **Soma das Dezenas:** A soma dos valores das 15 dezenas sorteadas no concurso anterior.

2.  **Treinamento e Persistência:** O sistema treina 25 modelos de classificação (um para cada dezena). Após testes e avaliações de backtesting, o modelo `RandomForestClassifier` do `scikit-learn` foi escolhido por apresentar um desempenho superior na previsão de dezenas premiadas em comparação com outros modelos como a Regressão Logística. Para otimizar o desempenho, os modelos treinados são salvos na pasta `trained_models/` usando `joblib`. Ao gerar uma nova sugestão, o sistema carrega os modelos já prontos em vez de retreiná-los, tornando o processo muito mais rápido.

3.  **Geração da Sugestão:** O sistema usa os modelos (carregados ou recém-treinados) para prever a probabilidade de cada dezena ser sorteada no próximo concurso. A sugestão final é composta pelas 15 dezenas com as maiores probabilidades.

---

## 📊 Avaliação da Estratégia (Backtesting)

Para validar a eficácia da abordagem de Machine Learning, o sistema inclui um módulo de backtesting (`backtest.py`).

**Como Funciona:**

1.  O usuário define um período de teste (ex: os últimos 100 concursos).
2.  O sistema itera por cada um desses concursos em ordem cronológica.
3.  Para cada concurso `N` no período de teste, o sistema:
    a.  Pega todos os resultados históricos *anteriores* a `N`.
    b.  Treina um conjunto de modelos de ML do zero, usando apenas esses dados passados.
    c.  Gera uma sugestão de 15 dezenas para o concurso `N`.
    d.  Compara a sugestão com o resultado real do concurso `N` e registra o número de acertos.
4.  Ao final, o sistema apresenta um relatório consolidado, mostrando quantas vezes a estratégia teria acertado 11, 12, 13, 14 ou 15 pontos. Isso oferece uma medida quantitativa do desempenho histórico do modelo.

**Nota:** O processo de backtesting é computacionalmente intensivo e pode demorar bastante, pois envolve treinar centenas de modelos de ML.
