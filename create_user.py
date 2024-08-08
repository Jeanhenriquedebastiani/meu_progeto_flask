from app import db, User, app

# Criação de um novo contexto de aplicação
with app.app_context():
    # Criação de todas as tabelas
    db.create_all()

    # Criação de um usuário de teste

    admin = User(
        username="JeanHD",
        password="Pasteldepizza12",
        first_name="Jean Henrique",
        last_name="De Bastiani",
        role="Administrador",
        is_admin=True,
    )
    db.session.add(admin)
    db.session.commit()

    print(f"Usuário {admin.username} criado com sucesso!")
