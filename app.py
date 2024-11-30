import os
import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import json
import sqlite3

import logging



app = Flask(__name__)
CORS(app)


handler = logging.FileHandler('logs/flask_app.log')  # Log to a file
app.logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
app.logger.addHandler(handler)


# Crie uma métrica de exemplo (contador de requisições)
REQUEST_COUNT = Counter('http_requests_total', 'Total de requisições HTTP', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'Latência das requisições HTTP em segundos', ['method', 'endpoint'])
HTTP_ERRORS = Counter('http_errors_total', 'Total de respostas HTTP com erro', ['method', 'endpoint', 'status_code'])


def log_message(level, message):
    """Loga uma mensagem com o nível especificado."""

    log_methods = {
        'debug': app.logger.debug,
        'info': app.logger.info,
        'warning': app.logger.warning,
        'error': app.logger.error,
        'critical': app.logger.critical
    }
    if level in log_methods:
        log_methods[level](f"{message}")
    else:
        app.logger.error(f"Unrecognized logging level: {level}")


# Middleware para contar requisições
@app.before_request
def before_request():
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()

# Rota para o Prometheus coletar as métricas
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# Endpoint para devolver todos as pessoas cadastradas
@app.route('/')
def home():
    '''
    log_message('info', 'This is an INFO message')
    log_message('debug', 'This is a DEBUG message')
    log_message('warning', 'This is a WARNING message')
    log_message('error', 'This is an ERROR message')
    log_message('critical', 'This is a CRITICAL message')

    '''
    log_message('info', '/')
    return "API de pessoas"

@app.route('/pessoas', methods=['GET'])
def pessoas():
    log_message('info', '/pessoas')
    try:
        with sqlite3.connect('crud.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''SELECT nome, sobrenome, cpf, data_nascimento FROM pessoa''')
            result = cursor.fetchall()
            return json.dumps([dict(ix) for ix in result]), 200
    except Exception as e:
        log_message('error', '/pessoas')
        return jsonify(error=str(e)), 500

@app.route('/pessoa/<cpf>', methods=['GET', 'DELETE'])
def pessoa_por_cpf(cpf):
    log_message('info', '/pessoa/' + str(cpf))
    try:
        with sqlite3.connect('crud.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if request.method == 'GET':
                cursor.execute('''SELECT nome, sobrenome, cpf, data_nascimento FROM pessoa WHERE cpf=?''', [cpf])
                result = cursor.fetchall()
                if result:
                    return json.dumps([dict(ix) for ix in result]), 200
                return jsonify(error="Pessoa não encontrada"), 404
            elif request.method == 'DELETE':
                cursor.execute('DELETE FROM pessoa WHERE cpf = ?', (cpf,))
                if cursor.rowcount == 0:
                    return jsonify(error="Pessoa não encontrada"), 404
                conn.commit()
                return jsonify(success="Pessoa deletada com sucesso"), 200
    except Exception as e:
        log_message('error', '/pessoa/' + str(cpf))
        return jsonify(error=str(e)), 500

@app.route('/pessoa', methods=['POST'])
def insere_atualiza_pessoa():

    log_message('info', '/pessoa POST')

    data = request.get_json(force=True)
    nome = data.get('nome')
    sobrenome = data.get('sobrenome')
    cpf = data.get('cpf')
    datanascimento = data.get('data_nascimento')

    try:
        with sqlite3.connect('crud.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM pessoa WHERE cpf = ?', (cpf,))
            exists = cursor.fetchone()
            if exists:
                cursor.execute('UPDATE pessoa SET nome=?, sobrenome=?, data_nascimento=? WHERE cpf=?', (nome, sobrenome, datanascimento, cpf))
                conn.commit()
                return jsonify(success="Pessoa atualizada com sucesso"), 200
            cursor.execute('INSERT INTO pessoa (nome, sobrenome, cpf, data_nascimento) VALUES (?, ?, ?, ?)', (nome, sobrenome, cpf, datanascimento))
            conn.commit()
            return jsonify(success="Pessoa inserida com sucesso"), 201
    except Exception as e:
        log_message('error', '/pessoa/POST')
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)