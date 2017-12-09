# scipy
import scipy
print('scipy: %s' % scipy.__version__)

# numpy
import numpy as np
print('numpy: %s' % np.__version__)

# pandas
import pandas as pd
print('pandas: %s' % pd.__version__)

# scikit-learn
import sklearn
print('sklearn: %s' % sklearn.__version__)

# statsmodels
import statsmodels
import statsmodels.api as sm
import statsmodels.formula.api as smf
import statsmodels.tsa.api as smt
print('statsmodels: %s' % statsmodels.__version__)

# json
from bson import json_util, ObjectId
from bson.json_util import dumps
from pandas.io.json import json_normalize
import json

import itertools
import warnings
import datetime

from flask import jsonify

# Importa o banco de dados
from app import db

def PredictArimaRainfall():

    # Busca dataset no banco de dados
    weather = list(db.meteo_data_weather_data.find({'weather_station_id': ObjectId('598f58415718dd578b4c8255')}))
    weather_normalized = pd.io.json.json_normalize(weather)
    df_rainfall = pd.DataFrame(weather_normalized[['analysis_date', 'rainfall.rainfall']])
    df_rainfall = df_rainfall.set_index('analysis_date')
    ts_rainfall = df_rainfall['2000-03-01':'2017-08-11'].groupby(pd.TimeGrouper(freq='MS')).mean()

    # Cria amostra de treinamento e de teste antes de realizar a análise
    n_sample = ts_rainfall.shape[0]
    n_forecast=12
    n_train=n_sample-n_forecast
    ts_train = ts_rainfall.iloc[:n_train]['rainfall.rainfall']
    ts_test = ts_rainfall.iloc[n_train:]['rainfall.rainfall']
    print(ts_train.shape)
    print(ts_test.shape)
    print("Training Series:", "\n", ts_train.tail(), "\n")
    print("Testing Series:", "\n", ts_test.head())

    # Treina e define o modelo
    arima202 = sm.tsa.SARIMAX(ts_train, order=(2,0,2))
    model_results = arima202.fit()

    # Realiza previsões
    pred_begin = ts_train.index[model_results.loglikelihood_burn]
    pred_end = ts_test.index[-1]
    pred = model_results.get_prediction(start=pred_begin.strftime('2000-03-%d'),
                                        end=pred_end.strftime('%Y-%m-%d'))
    pred_mean = pred.predicted_mean
    pred_ci = pred.conf_int(alpha=0.05)

    # Prepara listas com dados
    pred = pred_mean.values
    pred_list = pred.tolist()
    data = ts_rainfall['rainfall.rainfall'].values
    data_list = data.tolist()
    index = ts_rainfall.index
    index_list = index.tolist()
    # Prepara dicionário a serem persistido
    dict_data = {}
    dict_data['data']=data_list
    dict_data['data_pred']=pred_list
    dict_data['index']=index_list
    dict_data['city']='Sao Paulo'
    dict_data['model']='ARIMA'
    tempoFinalização=datetime.datetime.now()
    dict_data['date']=tempoFinalização
    

    # Persiste dicionário
    _id = db.rainfall_predictions.insert(dict_data)
    
    message="Finalizado em " + tempoFinalização.strftime("%Y/%m/%d às %H:%M:%S") + ".    (ID: " + str(_id) + ")"

    del dict_data['date']
    del dict_data['_id']

    return jsonify({'message':message,'result':dict_data})