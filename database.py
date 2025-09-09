import sqlite3
import json

DB_FILE = "lotofacil.db"

def conectar_db():
    """Cria uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    return conn

def criar_tabela():
    """Cria a tabela de resultados se ela não existir."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            concurso INTEGER PRIMARY KEY,
            dezenas TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
    print("Banco de dados e tabela verificados com sucesso.")

def inserir_resultado(concurso, dezenas):
    """Insere um resultado de concurso no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    # Usamos json.dumps para converter a lista de dezenas em uma string
    dezenas_str = json.dumps(dezenas)
    cursor.execute("""
        INSERT OR IGNORE INTO resultados (concurso, dezenas)
        VALUES (?, ?);
    """, (concurso, dezenas_str))
    conn.commit()
    conn.close()

def obter_ultimo_concurso_salvo():
    """Retorna o número do último concurso salvo no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(concurso) FROM resultados;")
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado if resultado else 0

def obter_todos_os_resultados():
    """Retorna todos os resultados do banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT concurso, dezenas FROM resultados ORDER BY concurso;")
    resultados = cursor.fetchall()
    conn.close()
    
    # Converte as strings de dezenas de volta para listas
    return [(concurso, json.loads(dezenas_str)) for concurso, dezenas_str in resultados]

def obter_resultado_concurso(numero_concurso):
    """Retorna os detalhes de um concurso específico."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT concurso, dezenas FROM resultados WHERE concurso = ?;", (numero_concurso,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        concurso, dezenas_str = resultado
        return {"concurso": concurso, "dezenas": json.loads(dezenas_str)}
    return None

def criar_tabela():
    """Cria as tabelas de resultados e usuários se elas não existirem."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            concurso INTEGER PRIMARY KEY,
            dezenas TEXT NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
    print("Banco de dados e tabelas verificados com sucesso.")

def criar_tabela_sugestoes_salvas():
    """Cria a tabela para armazenar as sugestões de jogos salvos."""
    conn = conectar_db()
    cursor = conn.cursor()
    # Para desenvolvimento, dropar a tabela para garantir que o novo schema seja aplicado.
    # CUIDADO: Isso apaga todos os dados da tabela.
    cursor.execute("DROP TABLE IF EXISTS sugestoes_salvas;")
    cursor.execute("""
        CREATE TABLE sugestoes_salvas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            concurso INTEGER NOT NULL,
            tipo_sugestao TEXT NOT NULL,
            numeros_sugeridos TEXT NOT NULL,
            resultado_concurso TEXT,
            acertos INTEGER,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

def create_user(username, password_hash):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?);", (username, password_hash))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None # Username already exists
    finally:
        conn.close()

def get_user_by_username(username):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?;", (username,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return {"id": user_data[0], "username": user_data[1], "password_hash": user_data[2]}
    return None

def get_user_by_id(user_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE id = ?;", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return {"id": user_data[0], "username": user_data[1], "password_hash": user_data[2]}
    return None


def salvar_sugestao(user_id, concurso, numeros_sugeridos, tipo_sugestao):
    """Salva uma sugestão de jogo no banco de dados, evitando duplicatas."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Converte a lista/tupla de números para uma string JSON para verificação
    numeros_str = json.dumps(sorted(list(numeros_sugeridos)))

    # Verifica se a sugestão já existe para este usuário
    cursor.execute("""
        SELECT id FROM sugestoes_salvas
        WHERE user_id = ? AND concurso = ? AND numeros_sugeridos = ? AND tipo_sugestao = ?
    """, (user_id, concurso, numeros_str, tipo_sugestao))
    
    if cursor.fetchone():
        # A sugestão já existe, então não faz nada
        conn.close()
        return

    # Se não existir, insere a nova sugestão
    cursor.execute("""
        INSERT INTO sugestoes_salvas (user_id, concurso, numeros_sugeridos, tipo_sugestao)
        VALUES (?, ?, ?, ?);
    """, (user_id, concurso, numeros_str, tipo_sugestao))
    conn.commit()
    conn.close()

def obter_sugestoes_salvas(user_id):
    """Retorna todas as sugestões salvas para um usuário, ordenadas pelo concurso."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, concurso, tipo_sugestao, numeros_sugeridos, resultado_concurso, acertos
        FROM sugestoes_salvas 
        WHERE user_id = ?
        ORDER BY concurso DESC, id DESC;
    """, (user_id,))
    sugestoes_raw = cursor.fetchall()
    conn.close()
    
    sugestoes_formatadas = []
    for id, concurso, tipo, numeros_str, resultado_str, acertos in sugestoes_raw:
        numeros = json.loads(numeros_str)
        resultado = json.loads(resultado_str) if resultado_str else None
        sugestoes_formatadas.append({
            "id": id,
            "concurso": concurso,
            "tipo_sugestao": tipo,
            "numeros_sugeridos": numeros,
            "resultado_concurso": resultado,
            "acertos": acertos
        })
    return sugestoes_formatadas

def deletar_sugestao(sugestao_id, user_id):
    """Deleta uma sugestão específica do banco de dados, verificando o user_id."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sugestoes_salvas WHERE id = ? AND user_id = ?;", (sugestao_id, user_id))
    conn.commit()
    conn.close()

def atualizar_acertos_sugestoes():
    """Verifica sugestões pendentes e calcula os acertos se o resultado estiver disponível."""
    conn = conectar_db()
    cursor = conn.cursor()

    # Pega todas as sugestões que ainda não têm acertos calculados
    cursor.execute("SELECT id, concurso, numeros_sugeridos FROM sugestoes_salvas WHERE acertos IS NULL;")
    sugestoes_pendentes = cursor.fetchall()

    if not sugestoes_pendentes:
        conn.close()
        return

    print(f"Verificando acertos para {len(sugestoes_pendentes)} sugestão(ões) pendente(s)...")

    for sugestao_id, concurso_num, numeros_sugeridos_str in sugestoes_pendentes:
        # Busca o resultado oficial para o concurso da sugestão
        cursor.execute("SELECT dezenas FROM resultados WHERE concurso = ?;", (concurso_num,))
        resultado_oficial = cursor.fetchone()

        if resultado_oficial:
            dezenas_oficiais_str = resultado_oficial[0]
            dezenas_oficiais = set(json.loads(dezenas_oficiais_str))
            numeros_sugeridos = set(json.loads(numeros_sugeridos_str))
            
            # Calcula a interseção para encontrar os acertos
            acertos = len(dezenas_oficiais.intersection(numeros_sugeridos))
            
            # Atualiza a linha no banco de dados com o resultado e os acertos
            cursor.execute("""
                UPDATE sugestoes_salvas
                SET resultado_concurso = ?, acertos = ?
                WHERE id = ?;
            """, (dezenas_oficiais_str, acertos, sugestao_id))
            print(f"Sugestão ID {sugestao_id} (Concurso {concurso_num}) atualizada: {acertos} acertos.")

    conn.commit()
    conn.close()



# Garante que as tabelas sejam criadas na primeira vez que este módulo for usado
criar_tabela()
criar_tabela_sugestoes_salvas()
