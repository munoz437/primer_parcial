#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from flask import Flask, redirect, url_for, render_template, session, request
from flask_socketio import emit, SocketIO
from tinydb import TinyDB, Query
import argparse
import os
import aiml


# Carga aplicación Flask
app = Flask(__name__)

# Habilita sockets in aplicación Flaks
socketio = SocketIO(app)

# Carga nucleo de AIML
k = aiml.Kernel()

# Carga base de datos de conversaciones
db = TinyDB('conversations.json')
Usuario= Query()

# Página principa.
@app.route('/')
def login():
  return render_template('home.html')

# Paǵina acerca de
@app.route('/about')
def about():
  return render_template('about.html')

# Página con chat
@app.route('/chat')
def chat():
  username=request.args['username']
  if not len(username)>0:
      username='desconocido'
  user=db.search(Usuario.user == username)
  print(user)
  if len(user)==0:
      user=db.insert({'user':username,'conversations':[[]]})
      user=db.get(eid=user)
  else:
      user=user[0]
      conv=user['conversations']
      conv.append([])
      db.update({'conversations':conv},eids=[user.eid])

  return render_template('chat.html',username=username)

# Mensajes con chat
@socketio.on('message', namespace='/ask')
def receive_message(message):
    username,message_=message['data'].split(':',1)
    user=db.search(Usuario.user == username)
    if len(user)==0:
      user=db.insert({'user':username,'conversations':[[]]})
      user=db.get(eid=user)
    else:
      user=user[0]
    ans=k.respond(message_)
    conv=user['conversations']
    conv[-1].append({'msg':message_,'ans':ans})
    db.update({'conversations':conv},eids=[user.eid])
    emit('response', {'data': ans.lower()})


# Función principal (interfaz con línea de comandos)
if __name__ == '__main__':
    p = argparse.ArgumentParser("pyAIML")
    p.add_argument("--host",default="127.0.0.1",
            action="store", dest="host",
            help="Root url [127.0.0.1]")
    p.add_argument("--port",default=5000,type=int,
            action="store", dest="port",
            help="Port url [500]")
    p.add_argument("--aiml",default="aiml/mibot.aiml",type=str,
            action="store", dest="aiml",
            help="AIML file with rules [aiml/mibot.aiml]")
    p.add_argument("--debug",default=False,
            action="store_true", dest="debug",
            help="Use debug deployment [Flase]")
    p.add_argument("-v", "--verbose",
            action="store_true", dest="verbose",
            help="Verbose mode [Off]")

    opts = p.parse_args()

    k.learn(opts.aiml)
    k.respond("load aiml b")

    socketio.run(app,
	    debug=opts.debug,
            host=opts.host,
            port=opts.port)
