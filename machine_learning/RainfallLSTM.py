# scipy
import scipy
print('scipy: %s' % scipy.__version__)

# numpy
import numpy
print('numpy: %s' % numpy.__version__)

# pandas
import pandas as pd
print('pandas: %s' % pd.__version__)

# scikit-learn
import sklearn
print('sklearn: %s' % sklearn.__version__)

# Keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

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
from app import db, db2

# prepara datesets de teste e treino
def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-2*look_back):
        a = dataset[i:(i+look_back), 0]
        dataX.append(a)
        dataY.append(dataset[i + 2*look_back, 0])
    return numpy.array(dataX), numpy.array(dataY)

# prepara dataset final
def create_final_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-1*look_back):
        a = dataset[i:(i+look_back), 0]
        dataX.append(a)
    return numpy.array(dataX)

def PredictLSTMRainfall(stationId):

    # Get station Infos
    station_info = list(db.meteo_data_weather_stations.find({'_id':ObjectId(stationId)}))

    print('\n')
    print('*************************************************************')
    print('**************** AgroAnalytics BRAINS API *******************')
    print('*************************************************************')
    print('\n')
    print('------------- LSTM Recurrent Neural Network -----------------')
    print('\n')
    print('Preparando dados da cidade de '+ station_info[0]['unparsed_city'] +'....')
    print('\n')

    # Busca dataset no banco de dados
    weather = list(db.meteo_data_weather_data.find({'weather_station_id': ObjectId(stationId)}))
    weather_normalized = pd.io.json.json_normalize(weather)
    df_rainfall = pd.DataFrame(weather_normalized[['analysis_date', 'rainfall.rainfall']])
    df_rainfall = df_rainfall.set_index('analysis_date')
    ts_rainfall = df_rainfall['2000-03-01':'2017-08-11'].groupby(pd.TimeGrouper(freq='MS')).mean()

    # fix random seed for reproducibility
    numpy.random.seed(7)

    # formata valores do dataset
    dataset = ts_rainfall.values
    dataset = dataset.astype('float32')

    # normalizando o dataset
    scaler = MinMaxScaler(feature_range=(0, 1))
    dataset = scaler.fit_transform(dataset)

    # split into train and test sets
    test_size = 36
    train_size = len(dataset) - 36
    train, test = dataset[0:train_size+24,:], dataset[train_size:len(dataset),:]

    # reshape into X=(t-24...t-12) and Y=t
    look_back = 12
    trainX, trainY = create_dataset(train, look_back)
    testX, testY = create_dataset(test, look_back)
    datasetX = create_final_dataset(dataset, look_back)

    # reshape input to be [samples, time steps, features]
    trainX = numpy.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
    testX = numpy.reshape(testX, (testX.shape[0], 1, testX.shape[1]))
    numpyDataset = numpy.reshape(datasetX, (datasetX.shape[0], 1, datasetX.shape[1]))

    print('----------------- Iniciando Treinamento ---------------------')
    print('\n')

    # create and fit the LSTM network
    model = Sequential()
    model.add(LSTM(4, input_shape=(1, 12)))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=2)

    # make predictions
    trainPredict = model.predict(trainX)
    testPredict = model.predict(testX)
    finalPredict = model.predict(numpyDataset)

    # invert predictions
    trainPredict = scaler.inverse_transform(trainPredict)
    trainY = scaler.inverse_transform([trainY])
    testPredict = scaler.inverse_transform(testPredict)
    testY = scaler.inverse_transform([testY])
    finalPredict = scaler.inverse_transform(finalPredict)

    # shift dataset predictions for plotting
    nanAppend = numpy.empty_like(dataset[:24])
    nanAppend[:, :] = numpy.nan
    finalPredictPlot = numpy.append(nanAppend,finalPredict)

    # shift train for plotting
    trainPlot = scaler.inverse_transform(dataset[:len(trainPredict)+2*look_back])

    # shift test for plotting
    testPlot = numpy.empty_like(dataset)
    testPlot[:, :] = numpy.nan
    testPlot[len(trainPredict)+(look_back*2)-1:len(dataset)-1, :] = scaler.inverse_transform(dataset[len(trainPredict)+(look_back*2)-1:len(dataset)-1])

    # shift train predictions for plotting
    trainPredictPlot = numpy.empty_like(dataset[:len(dataset)-12])
    trainPredictPlot[:, :] = numpy.nan
    trainPredictPlot[24:len(trainPredict)+48, :] = trainPredict

    # shift test predictions for plotting
    testPredictPlot = numpy.empty_like(dataset[len(trainPredict)+24:len(dataset)])
    testPredictPlot[:, :] = numpy.nan
    testPredictPlot[:len(dataset), :] = testPredict

    Predict = numpy.append(trainPredictPlot, testPredictPlot)

    # Prepara listas com dados
    
    # Preparando vetor com datas
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    def date_range(start_date, end_date, increment, period):
        result = []
        nxt = start_date
        delta = relativedelta(**{period:increment})
        while nxt <= end_date:
            result.append(nxt)
            nxt += delta
        return result
    
    index = ts_rainfall.index.tolist()
    index2 = date_range(index[-1] + relativedelta(months=1), index[-1]+
            relativedelta(months=13), 1, 'months') 
    index = index + index2
    pred_list=finalPredictPlot.tolist()
    data = ts_rainfall['rainfall.rainfall'].values
    data_list = data.tolist()
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
        mse = numpy.mean((y - y_hat)**2)
        return numpy.sqrt(mse)


    # Prepara dicionário a serem persistido
    dict_data = {}
    dict_data['data']=data_list
    dict_data['data_test']=data_test
    dict_data['data_train']=data_train
    dict_data['data_pred']=pred_list
    dict_data['index']=index
    dict_data['city']=station_info[0]['unparsed_city']
    dict_data['model']='LSTM'
    tempoFinalização=datetime.now()
    dict_data['date']=tempoFinalização
    dict_data['LSTM']= 4
    dict_data['Epoch']= 100
    dict_data['Optimizer']= 'Adam'
    dict_data['rmse_train']=get_rmse(trainY[0], trainPredict[:,0])
    dict_data['rmse_test']=get_rmse(testY[0], testPredict[:,0])
    

    # Persiste dicionário
    _id = db2.LSTM_predictions.insert(dict_data)
    
    message="Finalizado em " + tempoFinalização.strftime("%Y/%m/%d às %H:%M:%S") + ".    (ID: " + str(_id) + ")"

    del dict_data['date']
    del dict_data['_id']

    print(message)
    print('\n')
    print('----------------------- Sucesso! ----------------------------')
    print('\n')

    return jsonify({'message':message})