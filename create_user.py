from app import db, User, app

# Criação de um novo contexto de aplicação
with app.app_context():
    # Criação de todas as tabelas
    db.create_all()

admin = User(username="JeanH", password="pasteldepizza", is_admin=True)
db.session.add(admin)
db.session.commit()

print(f"Usuário {username} criado com sucesso!")
