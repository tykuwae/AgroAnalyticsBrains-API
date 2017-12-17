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

def PredictSARIMARainfall(stationId):

    # Get station Infos
    station_info = list(db.meteo_data_weather_stations.find({'_id':ObjectId(stationId)}))

    print('\n')
    print('*************************************************************')
    print('**************** AgroAnalytics BRAINS API *******************')
    print('*************************************************************')
    print('\n')
    print('------------------------ SARIMA -----------------------------')
    print('\n')
    print('Preparando dados da cidade de '+ station_info[0]['unparsed_city'] +'....')
    print('\n')

    # Busca dataset no banco de dados
    weather = list(db.meteo_data_weather_data.find({'weather_station_id': ObjectId(stationId)}))
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

    print('----------------- Iniciando Treinamento ---------------------')
    print('\n')
    # Treina e define o modelo
    p=0
    d=0
    q=4
    P=3
    D=0
    Q=4
    s=12
    arima202 = sm.tsa.SARIMAX(ts_train, order=(p,d,q), seasonal_order=(P,D,Q,s), enforce_stationarity=False, enforce_invertibility=False)
    model_results = arima202.fit()

    # Realiza previsões
    pred_begin = ts_train.index[model_results.loglikelihood_burn]
    pred_end = ts_test.index[-1] + datetime.timedelta(days=365)
    pred = model_results.get_prediction(start=pred_begin.strftime('2000-03-%d'),
                                        end=pred_end.strftime('%Y-%m-%d'))
    pred_mean = pred.predicted_mean
    pred_ci = pred.conf_int(alpha=0.05)

    # Prepara listas com dados
    
    pred = pred_mean.values
    pred_list = pred.tolist()

    data = ts_rainfall['rainfall.rainfall'].values
    data_list = data.tolist()

    index = pred_mean.index
    index_list = index.tolist()

    data_train = data_list
    data_test = [None] * len(data_list)

    for i in range(1,13):
        data_test[-i]=data_list[-i]
        data_train[-i]=None

    data_train[-12]=data_test[-12]

    for i in range(12):
        data_train.append(None)
        data_test.append(None)

    # Prepara métricas do modelo

    def get_rmse(y, y_hat):
        mse = np.mean((y - y_hat)**2)
        return np.sqrt(mse)


    # Prepara dicionário a serem persistido
    dict_data = {}
    dict_data['data']=data_list
    dict_data['data_test']=data_test
    dict_data['data_train']=data_train
    dict_data['data_pred']=pred_list
    dict_data['index']=index_list
    dict_data['city']=station_info[0]['unparsed_city']
    dict_data['model']='SARIMA'
    tempoFinalização=datetime.datetime.now()
    dict_data['date']=tempoFinalização
    dict_data['pdq']= str(p)+',  '+str(d)+',  '+str(q)
    dict_data['PDQs']= str(P)+',  '+str(D)+',  '+str(Q)+', '+str(s)
    dict_data['rmse_train']=get_rmse(ts_train, pred_mean.ix[ts_train.index])
    dict_data['rmse_test']=get_rmse(ts_test, pred_mean.ix[ts_test.index])
    dict_data['AIC']=model_results.aic
    dict_data['BIC']=model_results.bic
    

    # Persiste dicionário
    _id = db.rainfall_predictions.insert(dict_data)
    
    message="Finalizado em " + tempoFinalização.strftime("%Y/%m/%d às %H:%M:%S") + ".    (ID: " + str(_id) + ")"

    del dict_data['date']
    del dict_data['_id']

    print('----------------------- Sucesso! ----------------------------')
    print('\n')

    return jsonify({'message':message,'result':dict_data})