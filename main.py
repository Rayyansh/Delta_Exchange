from delta import DeltaExchangeAPI
from datetime import datetime,date
import requests
import pandas as pd
from indicators import super_trend

class GetProductDetailDelta():
    def __init__(self, api_key,secret_key,expiry_date,premium_price,underlying_symbol,period, multiplier,option_symbol_call,option_symbol_put,resolution,start_date,end_date,contract_unit_currency):
        self.api_key = api_key
        self.secret_key = secret_key
        self.expiry_date = expiry_date
        self.symbol_list_call = []
        self.symbol_list_put = []
        self.premium_price = premium_price
        self.strike_price = None
        self.underlying_symbol = underlying_symbol
        self.period = period
        self.multiplier = multiplier
        self.option_symbol_call = option_symbol_call
        self.option_symbol_put = option_symbol_put
        self.resolution = resolution
        self.start_date = start_date
        self.end_date = end_date
        self.contract_unit_currency =contract_unit_currency


        self.sp1_val = f'sp_val_{self.period}_{self.multiplier}'
        self.sp1_dir = f'sp_dir_{self.period}_{self.multiplier}'

    
    def product(self):
        api = DeltaExchangeAPI(self.api_key, self.secret_key)
        # product_list = []
        product = api.get_product()
        prdct = product.json()
        # print([r for r in prdct['result'] if r['settlement_time'] == self.expiry_date and  r['contract_unit_currency'] == self.underlying_symbol and r['contract_type']=='call_options'])
        list_of_call_data = [r for r in prdct['result'] if r['settlement_time'] == self.expiry_date  and  r['contract_unit_currency'] == self.contract_unit_currency and r['contract_type']=='call_options']
        list_of_put_data =[r for r in prdct['result'] if r['settlement_time'] == self.expiry_date  and  r['contract_unit_currency'] == self.contract_unit_currency and r['contract_type'] =='put_options']

        self.symbol_list_call = [dict(option_symbol=s['symbol'],strike_price=s['strike_price']) for s in list_of_call_data]
        self.symbol_list_put = [dict(option_symbol=s['symbol'],strike_price=s['strike_price']) for s in list_of_put_data]

    
        
        return prdct
    
    def calculate_by_premium(self,symbol_list_type,ticker_data):

        strike_price_list = [sp['strike_price'] for sp in symbol_list_type]
        sorted_strike_price = sorted(strike_price_list, key=lambda x: abs(int(x) - self.strike_price))
        
        closest_strike_price = sorted_strike_price[:1]
        symbol_list_type = [q for price in closest_strike_price for q in symbol_list_type if q['strike_price'] == str(price)]



        for i in symbol_list_type:
            try:
                symbol = [s for s in ticker_data['result'] if s['symbol'] == i['option_symbol']]
                if symbol:
                    ticker_best_bid = symbol[0]['quotes']
                    i['quotes'] = ticker_best_bid
            except KeyError:
                continue
        
        symbol_list_type = [d for d in symbol_list_type if d['quotes']['best_bid'] is not None and d['strike_price'] is not None]

        # print(self.symbol_list)
        best_bid = [q['quotes']['best_bid'] for q in symbol_list_type]
        best_bid = [price for price in best_bid if price is not None]

        sorted_best_bid = sorted(best_bid, key=lambda x: abs(float(x) - self.premium_price))
        closest_value = sorted_best_bid[:1]

        call_option_list = []

        for price in closest_value:
            for q in symbol_list_type:
                if q['quotes']['best_bid'] == str(price):
                    symbol_info = {
                        'option_symbol': q['option_symbol'],
                        'strike_price': q['strike_price'],
                        'quotes': q['quotes']
                    }
                    # self.symbol_list.append(symbol_info)
                    call_option_list.append(symbol_info)
                    break
        
        
        return call_option_list
    
    def ticker_for_product(self):
        api  = DeltaExchangeAPI(self.api_key, self.secret_key)

        ticker = api.get_ticker_product()
        ticker_data = ticker.json()
        live_price = api.get_ticker_product_with_symbol(symbol=self.underlying_symbol)
        live_spot_price = live_price.json()
        self.strike_price = float(live_spot_price['result']['spot_price'])
        print(self.strike_price)

        call_data =  self.calculate_by_premium(symbol_list_type=self.symbol_list_call,ticker_data=ticker_data)
        put_data =  self.calculate_by_premium(symbol_list_type=self.symbol_list_put,ticker_data=ticker_data)

        print('Call OPtion Data',call_data)
        print('PUt OPtion Data',put_data)
    
    def fetch_ohlc(self):
        

        api = DeltaExchangeAPI(self.api_key, self.secret_key)
        ohlc_call = api.get_ohlc(symbol=self.option_symbol_call,resolution=self.resolution,start=self.start_date,end=self.end_date)
        ohlc_data_call = ohlc_call.json()
        ohlc_data_converted_call = [o for o in ohlc_data_call['result']]
        df_call = pd.DataFrame(ohlc_data_converted_call,columns=['close', 'high', 'low', 'open', 'time','volume'])
        df_call['time'] = pd.to_datetime(df_call['time'],unit='s')

        # df_call = df_call.set_index('time')
        # print('This is CALL DF')
        # print(df_call)

        df_call.to_csv('testing_ohlc_data_call.csv')

        ohlc_put = api.get_ohlc(symbol=self.option_symbol_put,resolution=self.resolution,start=self.start_date,end=self.end_date)
        ohlc_data_put = ohlc_put.json()

        ohlc_data_converted_put = [o for o in ohlc_data_put['result']]
        df_put = pd.DataFrame(ohlc_data_converted_put,columns=['close', 'high', 'low', 'open', 'time','volume'])
        df_put['time'] = pd.to_datetime(df_put['time'], unit='s')

        # df_put = df_put.set_index('time')

        df_put.to_csv('testing_ohlc_data_put.csv')

        # print('THis is PUT DF')
        # print(df_put)


        merged_df = pd.merge(df_call, df_put, on='time', suffixes=('_call', '_put'))

        merged_df['close_total'] = merged_df['close_call'] + merged_df['close_put']
        merged_df['open_total'] = merged_df['open_call'] + merged_df['open_put']
        merged_df['low_total'] = merged_df['low_call'] + merged_df['low_put']
        merged_df['high_total'] = merged_df['high_call'] + merged_df['high_put']

        result_df = merged_df[['time', 'close_total','open_total','low_total','high_total']]

        merged_df.to_csv('testing_merged_df.csv')

        return result_df

    def calculate_supertrend(self):
        df = self.fetch_ohlc()
        super_trend_calc = super_trend(df, period=self.period, atr_multiplier=self.multiplier,sp_val=self.sp1_val, sp_dir=self.sp1_dir)
        
        super_trend_calc.to_csv('final_df.csv')
        print(super_trend_calc)

def main():
    api_key = 'FyFjmvYAlbhFyU8Gt0PniA3bS3ucky'  # Fill in your API key
    api_secret = '4WNBHW6oJ4Qr80GKsEp4fmupQ05g7dJkm7w91iueg9gtt4LrGPQkSRXD0qXK'  # Fill in your API secret
    expiry_date = "2023-07-14T12:00:00Z"
    premium_price = 1500
    underlying_symbol = 'BTCUSDT'
    contract_unit_currency = 'BTC'
    period = 10
    multiplier = 3
    option_symbol_call = 'C-BTC-30500-300623'
    option_symbol_put = 'P-BTC-30500-300623'
    resolution = '5m'
    start_date = 1687342819
    end_date = 1687429219
    print(expiry_date)


    apis = GetProductDetailDelta(api_key=api_key, secret_key=api_secret,
                                 expiry_date=expiry_date,
                                 premium_price=premium_price,
                                 underlying_symbol=underlying_symbol,
                                 period=period, 
                                 multiplier=multiplier,
                                 option_symbol_call=option_symbol_call,
                                 option_symbol_put=option_symbol_put,
                                 resolution=resolution,
                                 start_date=start_date,
                                 end_date=end_date,
                                 contract_unit_currency=contract_unit_currency)
    apis.product()
    apis.ticker_for_product()
    # apis.calculate_supertrend()


main()