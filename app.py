from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import database
import sugestoes
import ml_sugestoes
import backtest
import main

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui' # Mude para uma chave secreta forte!

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Define a rota para onde o usuário será redirecionado se não estiver logado

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    user_data = database.get_user_by_id(user_id)
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['password_hash'])
    return None

@app.route('/')
@login_required
def index():
    ultimo_concurso_num = database.obter_ultimo_concurso_salvo()
    ultimo_concurso_info = None
    if ultimo_concurso_num > 0:
        ultimo_concurso_info = database.obter_resultado_concurso(ultimo_concurso_num)
    return render_template('index.html', ultimo_concurso=ultimo_concurso_info)

@app.route('/update_db')
@login_required
def update_db():
    main.atualizar_banco_de_dados()
    return redirect(url_for('index'))

@app.route('/freq_suggestion')
@login_required
def freq_suggestion():
    proximo_concurso = database.obter_ultimo_concurso_salvo() + 1
    todos_os_resultados = database.obter_todos_os_resultados()
    if not todos_os_resultados:
        message = "O banco de dados está vazio. Por favor, atualize o banco primeiro."
        suggestions = []
    else:
        suggestions = sugestoes.gerar_sugestoes(todos_os_resultados, proximo_concurso, current_user.id)
        message = f"Sugestões de Jogo para o concurso {proximo_concurso} (Análise de Frequência):"
    return render_template('suggestions.html', message=message, suggestions=suggestions)

@app.route('/ml_suggestion')
@login_required
def ml_suggestion():
    proximo_concurso = database.obter_ultimo_concurso_salvo() + 1
    # Força o retreinamento se for a primeira vez ou se o usuário pedir
    # Para a web, vamos sempre tentar carregar, e o retreinamento será uma opção separada
    suggestion = ml_sugestoes.gerar_sugestao_ml(proximo_concurso, current_user.id, force_retrain=False)
    if suggestion:
        message = f"Sugestão de Jogo para o concurso {proximo_concurso} (Machine Learning):"
    else:
        message = "Não foi possível gerar sugestão de ML. Verifique se há dados suficientes."
    return render_template('suggestions.html', message=message, suggestions=[("ML Sugestão", suggestion)])

@app.route('/retrain_ml')
@login_required
def retrain_ml():
    proximo_concurso = database.obter_ultimo_concurso_salvo() + 1
    ml_sugestoes.gerar_sugestao_ml(proximo_concurso, current_user.id, force_retrain=True)
    return redirect(url_for('index'))

@app.route('/run_backtest', methods=['GET', 'POST'])
@login_required
def run_backtest():
    if request.method == 'POST':
        try:
            periodo_testes = int(request.form['periodo_testes'])
            if periodo_testes <= 0:
                message = "O número de concursos deve ser positivo."
                return render_template('backtest_results.html', message=message, results={})
            
            results = backtest.executar_backtest(periodo_testes)
            message = f"Relatório Final do Backtest ({periodo_testes} concursos):"

            total_concursos_testados = sum(count for points, count in results)
            maior_pontuacao = 0
            if results:
                maior_pontuacao = max(points for points, count in results)

            return render_template('backtest_results.html', 
                                   message=message, 
                                   results=results,
                                   total_concursos_testados=total_concursos_testados,
                                   maior_pontuacao=maior_pontuacao)
        except ValueError:
            message = "Entrada inválida. Por favor, insira um número válido."
            return render_template('backtest_results.html', message=message, results={})
    return render_template('backtest_form.html')

@app.route('/sugestoes_salvas')
@login_required
def sugestoes_salvas():
    """Exibe todas as sugestões de jogos que foram salvas no banco de dados."""
    sugestoes = database.obter_sugestoes_salvas(current_user.id)
    return render_template('sugestoes_salvas.html', sugestoes=sugestoes)

@app.route('/delete_sugestao/<int:sugestao_id>', methods=['POST'])
@login_required
def delete_sugestao(sugestao_id):
    database.deletar_sugestao(sugestao_id, current_user.id)
    return redirect(url_for('sugestoes_salvas'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        if database.create_user(username, hashed_password):
            flash('Usuário registrado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Nome de usuário já existe.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = database.get_user_by_username(username)

        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'], user_data['password_hash'])
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login inválido. Verifique seu nome de usuário e senha.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
