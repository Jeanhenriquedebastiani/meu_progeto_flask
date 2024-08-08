from flask import Flask, render_template, request, redirect, url_for, flash 
from flask_sqlalchemy import SQLAlchemy
from asgiref.wsgi import WsgiToAsgi
from flask_bcrypt import Bcrypt
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
from functools import wraps
from flask import abort
import pandas as pd
import os
import datetime 


app = Flask(__name__)

app.config["SECRET_KEY"] = "Pasteldepizza8816"
# Configuração do banco de dados SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///livros.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, password, first_name, last_name, role, is_admin=False):
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.is_admin = is_admin


class Livro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    editora = db.Column(db.String(200), default="Sem Editora")
    ativo = db.Column(db.Boolean, default=False)

    def __init__(self, titulo, autor, categoria, ano, editora="Sem Editora", ativo=False):
        self.titulo = titulo
        self.autor = autor
        self.categoria = categoria
        self.ano = ano
        self.editora = editora
        self.ativo = ativo

    def __repr__(self):
        return f"<Livro {self.titulo}>"

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('livro.id'), nullable=False)
    date_reserved = db.Column(db.DateTime, nullable=False, default=datetime.UTC)

    def __init__(self, user_id, book_id):
        self.user_id = user_id
        self.book_id = book_id

with app.app_context():
    db.create_all()

    # Ler o arquivo CSV para um DataFrame
    df = pd.read_csv("tabela - livros.csv")

    # Adicionar cada livro à base de dados, se ainda não estiverem presentes
    for index, row in df.iterrows():
        if not Livro.query.filter_by(titulo=row["Titulo do Livro"]).first():
            livro = Livro(titulo=row["Titulo do Livro"],
                autor=row["Autor"],
                categoria=row["Categoria"],
                ano=row["Ano de Publicação"],
                ativo=row["Ativo"] == "TRUE",)
            db.session.add(livro)
    db.session.commit()


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/inicio")
@login_required
def inicio():
    livros = Livro.query.all()
    return render_template("lista.html", lista_de_livros = livros)

@app.route("/curriculo")
@login_required
def curriculo():
    return render_template("curriculo.html")

@app.route("/novo")
@login_required
def novo():
    return render_template("novo.html", titulo = "Novo Livro")


@app.route("/criar", methods=["POST"])
@login_required
def criar():
    titulo = request.form["titulo"]
    autor = request.form["autor"]
    categoria = request.form["categoria"]
    ano = request.form["ano"]
    editora = request.form["editora"]
    livro = Livro(titulo = titulo, autor = autor, categoria = categoria, ano = ano, editora = editora)
    db.session.add(livro)
    db.session.commit()
    return redirect(url_for("inicio"))

@app.route("/deletar/<int:id>")
@login_required
def deletar(id):
    # buscar livro pelo id
    livro = Livro.query.get(id)
    if livro:
        #remover o livro do banco de dados
        db.session.delete(livro)
        db.session.commit()
        #redirecionar ao inicio
    return redirect(url_for("inicio"))

@app.route("/editar/<int:id>")
@login_required
def editar(id):
    #buscar o livro pelo id
    livro = Livro.query.get(id)
    if livro:
        return render_template("editar.html",livro=livro)
    return redirect(url_for("inicio"))

@app.route("/atualizar/<int:id>", methods=["POST"])
@login_required
def atualizar(id):
    # Buscar o livro pelo ID
    livro = Livro.query.get(id)
    if livro:
        # Atualizar os dados do livro
        livro.titulo = request.form["titulo"]
        livro.autor = request.form["autor"]
        livro.categoria = request.form["categoria"]
        livro.ano = request.form["ano"]
        livro.editora = request.form["editora"]
        db.session.commit()
    return redirect(url_for("inicio"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username = username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("inicio"))
        else:
            flash("Login ou senha incorretos. Tente novamente.")
    return render_template ("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/cadastro", methods=["GET", "POST"])
@login_required
@admin_required
def cadastro():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        role = request.form.get("role")
        is_admin = request.form.get("is_admin") == 'on'  # Verifica se o checkbox foi marcado

        # Verifique se o usuário já existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Nome de usuário já existe. Tente um diferente.")
            return redirect(url_for("cadastro"))

        # Criação de um novo usuário
        new_user = User(username=username, password=password, first_name=first_name, last_name=last_name, role=role, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()
        flash("Cadastro realizado com sucesso! Você já pode fazer login.")
        return redirect(url_for("login"))
    return render_template("cadastro.html")

@app.errorhandler(403)
def forbidden_error(error):
    return render_template("403.html"), 403

@app.route("/reservar", methods=["GET"])
@login_required
def reservar():
    livros = Livro.query.all()  # Pega todos os livros
    return render_template("reservar.html", livros=livros)

@app.route("/fazer_reserva/<int:book_id>")
@login_required
def fazer_reserva(book_id):
    # Verifica se o livro já foi reservado pelo usuário
    reserva_existente = Reservation.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if reserva_existente:
        flash("Você já reservou este livro.")
        return redirect(url_for("reservar"))

    # Criação de uma nova reserva
    nova_reserva = Reservation(user_id=current_user.id, book_id=book_id)
    db.session.add(nova_reserva)
    db.session.commit()
    flash("Reserva realizada com sucesso!")
    return redirect(url_for("reservar"))

@app.route("/minhas_reservas")
@login_required
def minhas_reservas():
    reservas = Reservation.query.filter_by(user_id=current_user.id).all()
    return render_template("minhas_reservas.html", reservas=reservas)

asgi_app = WsgiToAsgi(app)

if __name__ == "__main__":
    app.run(debug=True)
