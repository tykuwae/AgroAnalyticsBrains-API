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

# convert an array of values into a dataset matrix
def create_dataset(dataset, look_back=1):
    data, dataX, dataY = [], [], []
    for i in range(len(dataset)-look_back):
        a = dataset[i:i+look_back, 0]
        dataX.append(a)
        dataY.append(dataset[i+look_back, 0])
    return numpy.array(dataX), numpy.array(dataY)

# prepara dataset final
def create_final_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-1*look_back):
        a = dataset[i:(i+look_back), 0]
        dataX.append(a)
    return numpy.array(dataX)

def PredictLSTMQuotation(uf_id, product_id):

    # Get uf and product Infos
    uf_info = list(db.federal_units.find({'_id':ObjectId(uf_id)}))
    product_info = list(db.products.find({'_id':ObjectId(product_id)}))

    print('\n')
    print('*************************************************************')
    print('**************** AgroAnalytics BRAINS API *******************')
    print('*************************************************************')
    print('\n')
    print('------------- LSTM Recurrent Neural Network -----------------')
    print('\n')
    print('Preparando dados de cotação de' +  product_info[0]['name'] + 'da unidade federativa' + uf_info[0]['name'] +'....')  
    print('\n')

    # Busca dataset no banco de dados
    # Extrai dados Climáticos da Estação Selecionada
    quotation = list(db.quotation_monthlies.find({'federal_unit_id': ObjectId(uf_id),'product_id': ObjectId(product_id)}))
    quotation_normalized = pd.io.json.json_normalize(quotation)
    df_quotation = pd.DataFrame(quotation_normalized[['reference_month', 'quotation_price']])
    df_quotation = df_quotation.set_index('reference_month')
    ts_quotation = df_quotation['2000-01-01':'2017-08-01'].groupby(pd.TimeGrouper(freq='MS')).mean()
    ts_quotation = ts_quotation.asfreq(freq='MS', method='bfill')
    ts_quotation = ts_quotation[ts_quotation.index >= '2005-01-01']

    # fix random seed for reproducibility
    numpy.random.seed(7)

    # formata valores do dataset
    dataset = ts_quotation.values
    dataset = dataset.astype('float32')
    # normalize the dataset
    scaler = MinMaxScaler(feature_range=(0, 1))
    dataset = scaler.fit_transform(dataset)

    look_back = 3
    forecasting = 3
    # split into train and test sets
    test_size = look_back + forecasting
    train_size = int(len(dataset) - test_size)
    train, test = dataset[0:train_size+look_back,:], dataset[train_size:len(dataset),:]
    print(len(train), len(test))

    # reshape into X=t and Y=t+1
    trainX, trainY = create_dataset(train, look_back)
    testX, testY = create_dataset(test, look_back)
    datasetX = create_final_dataset(dataset, look_back)

    # reshape input to be [samples, time steps, features]
    trainX = numpy.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
    #testX = numpy.reshape(testX, (testX.shape[0], 1, testX.shape[1]))
    testX = numpy.reshape(testX, (testX.shape[0], 1, testX.shape[1]))
    numpyDataset = numpy.reshape(datasetX, (datasetX.shape[0], 1, datasetX.shape[1]))

    print('----------------- Iniciando Treinamento ---------------------')
    print('\n')

    # create and fit the LSTM network
    model = Sequential()
    model.add(LSTM(4, input_shape=(1, look_back)))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=2)

    testX = numpy.reshape(testX[0], (testX[0].shape[0], 1, testX[0].shape[1]))
    numpyDataset = numpy.reshape(datasetX[0], (datasetX[0].shape[0], 1, datasetX[0].shape[1]))
    testPredict1 = model.predict(testX)
    testPredict1final = model.predict(numpyDataset)

    testX =numpy.array([[testX[0][0][1],testX[0][0][2],testPredict1[0][0]]])
    testX = numpy.reshape(testX, (testX.shape[0], 1, testX.shape[1]))
    numpyDataset =numpy.array([[numpyDataset[0][0][1],numpyDataset[0][0][2],testPredict1final[0][0]]])
    numpyDataset = numpy.reshape(numpyDataset, (numpyDataset.shape[0], 1, numpyDataset.shape[1]))
    testPredict2 = model.predict(testX)
    testPredict2final = model.predict(numpyDataset)

    testX =numpy.array([[testX[0][0][1],testX[0][0][2],testPredict2[0][0]]])
    testX = numpy.reshape(testX, (testX.shape[0], 1, testX.shape[1]))
    numpyDataset =numpy.array([[numpyDataset[0][0][1],numpyDataset[0][0][2],testPredict2final[0][0]]])
    numpyDataset = numpy.reshape(numpyDataset, (numpyDataset.shape[0], 1, numpyDataset.shape[1]))
    testPredict3 = model.predict(testX)
    testPredict3final = model.predict(numpyDataset)

    testPredict = numpy.array([testPredict1[0],testPredict2[0],testPredict3[0]])
    finalPredict = numpy.array([testPredict1final[0],testPredict2final[0],testPredict3final[0]])

    # make predictions
    trainPredict = model.predict(trainX)
    #testPredict = model.predict(testX)

    # invert predictions
    trainPredict = scaler.inverse_transform(trainPredict)
    trainY = scaler.inverse_transform([trainY])
    testPredict = scaler.inverse_transform(testPredict)
    testY = scaler.inverse_transform([testY])
    finalPredict = scaler.inverse_transform(finalPredict)

    # shift dataset predictions for plotting
    nanAppend = numpy.empty_like(dataset[:3])
    nanAppend[:, :] = numpy.nan
    finalPredictPlot = numpy.append(nanAppend,finalPredict)

    # shift train for plotting
    trainPlot = scaler.inverse_transform(dataset[:len(trainPredict)+2*look_back])

    # shift test for plotting
    testPlot = numpy.empty_like(dataset)
    testPlot[:, :] = numpy.nan
    testPlot[len(trainPredict)+look_back:len(dataset), :] = scaler.inverse_transform(dataset[len(trainPredict)+look_back:len(dataset)])
        
    # shift train predictions for plotting
    trainPredictPlot = numpy.empty_like(dataset[:len(dataset)-forecasting])
    trainPredictPlot[:, :] = numpy.nan
    trainPredictPlot[look_back:len(trainPredict)+look_back, :] = trainPredict
    
    # shift test predictions for plotting
    testPredictPlot = numpy.empty_like(dataset[len(trainPredictPlot):len(dataset)])
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
    
    index = ts_quotation.index.tolist()
    index2 = date_range(index[-1] + relativedelta(months=1), index[-1]+
            relativedelta(months=3), 1, 'months') 
    index = index + index2
    pred_list=finalPredictPlot.tolist()
    data = ts_quotation['quotation_price'].values
    data_list = data.tolist()
    data_train = data_list
    data_test = [None] * len(data_list)

    for i in range(1,4):
        data_test[-i]=data_list[-i]
        data_train[-i]=None
        
    data_train[-3]=data_test[-3]

    for i in range(4):
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
    dict_data['uf_id']=uf_id
    dict_data['uf']=uf_info[0]['name']
    dict_data['product_id']=uf_id
    dict_data['product']=product_info[0]['name']
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