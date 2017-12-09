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
from machine_learning.RainfallARIMA import PredictArimaRainfall

# ------------------------------ Routes -----------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/precipitacao')
def precipitacao():
    return render_template('precipitacao.html')

@app.route("/chartRainfallARIMA")
def chartRainfallARIMAdata():
    last_data = list(db.rainfall_predictions.find({'model': 'ARIMA'}).sort([('_id',-1)]).limit(1))
    timestamps=last_data[0]['index'][-120:]
    date_strings = [d.strftime('%m-%d-%Y') for d in timestamps]

    date=[]
    for i in range(0,120):
        if i%12 == 0:
            date.append(date_strings[i])
        else:
            date.append("")

    index = date
    data = last_data[0]['data'][-120:]
    pred = last_data[0]['data_pred'][-120:]
    return jsonify({'data':data, 'pred': pred, 'index':index })

@app.route('/PredictRainfall', methods=['POST'])
def PredictRainfall():
    result = PredictArimaRainfall()
    return result

# ------------------------------ Routes -----------------------------------

if __name__ == '__main__':
    app.run(debug=True)