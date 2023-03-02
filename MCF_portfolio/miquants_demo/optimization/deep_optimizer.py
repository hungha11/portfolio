import tensorflow as tf
from tensorflow.keras.layers import LSTM, Flatten, Dense
from tensorflow.keras.models import Sequential
import tensorflow.keras.backend as K
import numpy as np

class deep_sharpe:
    def __init__(self):
        self.data = None
        self.model = None
    
    def sharpe_loss(self,_, y_pred):
        # make all time-series start at 1
        data = tf.divide(self.data, self.data[0])  

        # value of the portfolio after allocations applied
        portfolio_values = tf.reduce_sum(tf.multiply(data, y_pred), axis=1) 

        portfolio_returns = (portfolio_values[1:] - portfolio_values[:-1]) / portfolio_values[:-1]  # % change formula

        sharpe = K.mean(portfolio_returns) / K.std(portfolio_returns)

        return -sharpe
    
    def __build_model(self, input_shape, outputs):
        '''
        Builds and returns the Deep Neural Network that will compute the allocation ratios
        that optimize the Sharpe Ratio of the portfolio
        
        inputs: input_shape - tuple of the input shape, outputs - the number of assets
        returns: a Deep Neural Network model
        '''
        model = Sequential([
            LSTM(64, input_shape=input_shape,return_sequences=True),
            LSTM(64, return_sequences=False),
            Flatten(),
            Dense(outputs, activation='softmax')
        ])
        
        model.compile(loss=self.sharpe_loss, optimizer='adam')
        return model
    
    def get_allocations(self, data,epochs):
        '''
        Computes and returns the allocation ratios that optimize the Sharpe over the given data
        
        input: data - DataFrame of historical closing prices of various assets
        
        return: the allocations ratios for each of the given assets
        '''
        
        # data with returns
        data_w_ret = np.concatenate([ data.values[1:], data.pct_change().values[1:] ], axis=1)
        
        data = data.iloc[1:]
        self.data = tf.cast(tf.constant(data), float)
        
        if self.model is None:
            self.model = self.__build_model(data_w_ret.shape, len(data.columns))
        fit_predict_data = data_w_ret[np.newaxis,:]        
        self.model.fit(fit_predict_data, np.zeros((1, len(data.columns))), epochs=epochs, shuffle=False)
        print(self.model.summary())
        return self.model.predict(fit_predict_data)[0]