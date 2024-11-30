import sqlite3
import faker

def create_database():
    # Criar e conectar ao banco de dados SQLite
    conn = sqlite3.connect('crud.db')
    cursor = conn.cursor()

    # Criar a tabela pessoa
    cursor.execute('''
    CREATE TABLE pessoa (
        nome TEXT,
        sobrenome TEXT,
        cpf TEXT,
        data_nascimento TEXT
    )
    ''')

    # Gerar dados fictícios
    fake = faker.Faker('pt_BR')
    insert_query = 'INSERT INTO pessoa (nome, sobrenome, cpf, data_nascimento) VALUES (?, ?, ?, ?)'

    for _ in range(50):
        nome = fake.first_name()
        sobrenome = fake.last_name()
        cpf = fake.cpf()
        data_nascimento = fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat()
        cursor.execute(insert_query, (nome, sobrenome, cpf, data_nascimento))

    # Commit e fechar a conexão
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
