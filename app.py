import os
import random
import time
import datetime

# flask
from flask import Flask, request, render_template, Markup, \
session, flash, Response, redirect, url_for, jsonify 

# pymongo
# from flask.ext.pymongo import PyMongo
import pymongo 

#--------------------- Configurações da Aplicação ------------------------

def before_request():
    app.jinja_env.cache = {}

# Inicia o aplicativo
app = Flask(__name__)
app.config.from_pyfile('config.py')
app.before_request(before_request)

# Cria conexão com o Banco de Dados
from pymongo import MongoClient
client = MongoClient('localhost', 27017)

# Cria Instância do Banco de Dados
db = client.AgroAnalyticsDatum

# Machine Learning Models
from machine_learning.RainfallARIMA import PredictARIMARainfall
from machine_learning.RainfallSARIMA import PredictSARIMARainfall

# ------------------------------ Routes -----------------------------------

@app.route('/')
def index():
    '''
        Rota para renderizar página inicial.
    '''
    return render_template('index.html')

@app.route('/precipitacao')
def precipitacao():
    '''
        Rota para renderizar página de Precipitação
    '''
    return render_template('precipitacao.html')

@app.route('/PredictRainfall', methods=['POST'])
def PredictRainfall():
    if request.form['modelo'] == 'ARIMA':
        result = PredictARIMARainfall()
    elif request.form['modelo'] == 'SARIMA':
        result = PredictSARIMARainfall()
    else:
        result = 'ERRO!'
    return result

@app.route("/chartRainfallARIMA")
def chartRainfallARIMAdata():
    '''
        Rota utilizada para plotar gráfico de treino e teste do último modelo ARIMA processado
        para dados de Precipitação
    '''
    # Obtem ultimo documento de previsão processado
    last_data = list(db.rainfall_predictions.find({'model': 'ARIMA'}).sort([('_id',-1)]).limit(1))
    # Carraga para variável timestamps o index dos ultimos 5 anos
    timestamps=last_data[0]['index'][-60:]
    # Trata formato do index
    date_strings = [d.strftime('%m-%Y') for d in timestamps]
    # Cria uma lista com um index por ano, para não sobrecarregar a visão do gráfico
    date=[]
    for i in range(0,len(date_strings)):
        if i%4 == 0:
            date.append(date_strings[i])
        else:
            date.append("")
    # Preenche lista com index
    index = date
    # Preenche lista com dados originais de precipitação
    data_train = last_data[0]['data_train'][-len(date_strings):]
    # Preenche lista com dados originais de precipitação
    data_test = last_data[0]['data_test'][-len(date_strings):]
    # Preenche lista com dados de previsão 
    pred = last_data[0]['data_pred'][-len(date_strings):]
    return jsonify({'data_train':data_train, 
                    'data_test':data_test, 
                    'pred': pred, 'index':index, 
                    'pdq':last_data[0]['pdq'], 
                    'rmse_train':format(last_data[0]['rmse_train'], '.4f'), 
                    'rmse_test':format(last_data[0]['rmse_test'], '.4f'),
                    'AIC':format(last_data[0]['AIC'], '.4f'),
                    'BIC':format(last_data[0]['BIC'], '.4f'),
                    'city':last_data[0]['city'],
                    'date':last_data[0]['date'].strftime('%d/%m/%Y')})

@app.route("/chartRainfallSARIMA")
def chartRainfallSARIMAdata():
    '''
        Rota utilizada para plotar gráfico de treino e teste do último modelo ARIMA processado
        para dados de Precipitação
    '''
    # Obtem ultimo documento de previsão processado
    last_data = list(db.rainfall_predictions.find({'model': 'SARIMA'}).sort([('_id',-1)]).limit(1))
    # Carraga para variável timestamps o index dos ultimos 5 anos
    timestamps=last_data[0]['index'][-60:]
    # Trata formato do index
    date_strings = [d.strftime('%m-%Y') for d in timestamps]
    # Cria uma lista com um index por ano, para não sobrecarregar a visão do gráfico
    date=[]
    for i in range(0,len(date_strings)):
        if i%4 == 0:
            date.append(date_strings[i])
        else:
            date.append("")
    # Preenche lista com index
    index = date
    # Preenche lista com dados originais de precipitação
    data_train = last_data[0]['data_train'][-len(date_strings):]
    # Preenche lista com dados originais de precipitação
    data_test = last_data[0]['data_test'][-len(date_strings):]
    # Preenche lista com dados de previsão 
    pred = last_data[0]['data_pred'][-len(date_strings):]
    return jsonify({'data_train':data_train, 
                    'data_test':data_test, 
                    'pred': pred, 'index':index, 
                    'pdq':last_data[0]['pdq'],
                    'PDQs':last_data[0]['PDQs'], 
                    'rmse_train':format(last_data[0]['rmse_train'], '.4f'), 
                    'rmse_test':format(last_data[0]['rmse_test'], '.4f'),
                    'AIC':format(last_data[0]['AIC'], '.4f'),
                    'BIC':format(last_data[0]['BIC'], '.4f'),
                    'city':last_data[0]['city'],
                    'date':last_data[0]['date'].strftime('%d/%m/%Y')})

# ------------------------------ Routes -----------------------------------

if __name__ == '__main__':
    app.run(debug=True)