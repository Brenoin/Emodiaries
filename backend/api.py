from types import MethodType
from flask import Flask, current_app, jsonify, request, session
from flask_session import Session

import sqlite3
import hashlib
import os 
from datetime import timedelta
is_cors = False
if os.path.isfile('.enable-cors'):
    print('Enabling Flask-CORS')
    is_cors = True
    from flask_cors import CORS, cross_origin

import ujson as json
from flask_compress import Compress
import uuid

app = Flask(__name__)
app.host = '0.0.0.0'
app.config['SESSION_TYPE'] = 'filesystem'
app.config.from_object(__name__)

app.secret_key = str(uuid.uuid4())
Session(app)

if is_cors:
    CORS(
	    app,
    	headers=['application/json'],
	    expose_headers=[
    		'Access-Control-Allow-Credentials',
	    	'true'
    	],
    	supports_credentials=True
    )

Compress(app)

if not is_cors:
    def cross_origin(func):
        def wrapper():
            func()
        return wrapper


# This is another implementation of Flask's jsonify, but optimized.
def jsonify(*args, **kwargs):
	if args and kwargs:
		raise TypeError('jsonify() behavior undefined when passed both args and kwargs')
	elif len(args) == 1: # single args are passed directly to dumps()
		data = args[0]
	else:
		data = args or kwargs
	return current_app.response_class(
		json.dumps(data) + '\n',
		mimetype=current_app.config['JSONIFY_MIMETYPE']
	)

#-------------------------------------------------------------------------
@cross_origin
@app.route('/login' , methods=['POST'])
def _login():
		# Define o tempo da sessão
		session.permanent = True
		app.permanent_session_lifetime = timedelta(hours=2)
		
	 	# Se ja estiver logado, só ignora
		if 'user' in session:
			return jsonify({
				'autenticado': session.get('auth'),
				'usuario': session.get('user'),
				'erro': None
			})
		elif request.form:
			nome = request.form.get('username')
			# define variavéis para o login
			senha = request.form.get('password')
			# variaveis para mensagens de erro
			json = {'autenticado': False}
			# converte senha num hash
			senha = hashlib.sha256(senha.encode()).hexdigest()
			conx = sqlite3.connect('database.db')  # conecta no sqlite
			cur = conx.cursor()  # cursor do banco de dados
			cur.execute('SELECT * FROM users WHERE username like ? AND password = ?',
					(nome, senha))
			res = cur.fetchone()
			if res is None:  # se não tem nenhum usuario com esse nome e esse hash de senha
				json = {
					'autenticado': False,
					'erro': 'Usuário inexistente'
				}
			else:
				session['auth'] = True
				session['user'] = res[1] #nome
				json = {
					'autenticado': session.get('auth'),
					'usuario': session.get('user'),
					'erro': None
					}
			return jsonify(json)
		else:
			session['auth'] = False
			return jsonify({
					'usuario': session.get('user'),
					'autenticado': session.get('auth'),
					'erro': "Usuário não está logado"
				})
#rota de logout / sair da conta

@cross_origin
@app.route('/logout' , methods=['POST'])
def _logout():
	session.pop('user')
	session.pop('auth')
	return jsonify({
					'usuario': session.get('user'),
					'autenticado': session.get('auth'),
					'erro': "Usuário não está logado"
				})

#apenas para teste do session
@cross_origin
@app.route('/visitantes', methods=['POST', 'GET'])
def _visitantes():
		if 'visitas' in session:   
			session["visitas"] = session.get('visitas') + 1
		else:
			session['visitas'] = 1
		return jsonify({'Total de visitas' : session.get('visitas')})  

#consultando o bd de publicações:
@cross_origin
@app.route('/publicacoes', methods=['POST', 'GET'])
def _publicacoes():
	conx = sqlite3.connect('database.db')  # conecta no sqlite
	cur = conx.cursor()  # cursor do banco de dados
	if MethodType == "GET":
		cur.execute('SELECT * FROM feed;')
		res = cur.fetchone()
		if res is None:  # se não tem nenhum usuario com esse nome e esse hash de senha
			json = {
					'autenticado': False,
					'erro': 'Usuário inexistente'
			}
	elif MethodType == "POST":
		# define variavéis para subir a postagem no banco de dados
		titulo = request.form.get('titulo')
		texto = request.form.get('texto')
		emoteCod = request.form.get('emote')
		cur.execute('INSERT INTO table(feed) VALUES (?, ?, ?)',(texto,titulo,emoteCod))


if __name__ == '__main__':
	app.run(threaded=True, debug=True, port=9999)