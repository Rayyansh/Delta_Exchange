import hashlib
import hmac
import base64
import requests
import datetime

class DeltaExchangeAPI:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://testnet-api.delta.exchange/v2"

    def generate_signature(self, secret, message):
        message = bytes(message, 'utf-8')
        secret = bytes(secret, 'utf-8')
        hash = hmac.new(secret, message, hashlib.sha256)
        return hash.hexdigest()

    def get_time_stamp(self):
        d = datetime.datetime.utcnow()
        epoch = datetime.datetime(1970, 1, 1)
        return str(int((d - epoch).total_seconds()))

    def get_open_positions(self, product_id):
        endpoint = f"/positions/"
        url = self.base_url + endpoint
        method = 'GET'
        timestamp = self.get_time_stamp()
        query_string = f'?product_id={product_id}'
        payload = ''
        signature_data = method + timestamp + endpoint + query_string + payload
        signature = self.generate_signature(self.api_secret, signature_data)

        req_headers = {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'User-Agent': 'rest-client',
            'Content-Type': 'application/json'
        }

        query = {"product_id": product_id}

        response = requests.get(
            url, params=query, timeout=(3, 27), headers=req_headers
        )
        return response
    
    def get_positions_margined(self, contract_types = None, product_id= None):
        endpoint = f"/positions/margined"
        url = self.base_url + endpoint
        method = 'GET'
        timestamp = self.get_time_stamp()
        if product_id == None and contract_types == None:
            query_string = f''
        elif product_id != None and contract_types != None:
            query_string = f'?product_id={product_id}&contract_types={contract_types}'
        elif product_id != None and contract_types == None:
            query_string = f'?product_id={product_id}'
        elif product_id == None and contract_types != None:
            query_string = f'?contract_types={contract_types}'
            
        payload = ''
        signature_data = method + timestamp + endpoint + query_string + payload
        signature = self.generate_signature(self.api_secret, signature_data)

        req_headers = {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'User-Agent': 'rest-client',
            'Content-Type': 'application/json'
        }
        if product_id == None and contract_types == None:
            query = f''
        elif product_id != None and contract_types != None:
            query = {"product_id": product_id,"contract_types":f"{contract_types}"}
        elif product_id != None and contract_types == None:
            query = {"product_id": product_id}
        elif product_id == None and contract_types != None:
            query = {"contract_types": f"{contract_types}"}

        response = requests.get(
            url, params=query, timeout=(3, 27), headers=req_headers
        )
        return response
    
    def get_product(self,contract_types= None):
        endpoint = f"/products"
        url = self.base_url + endpoint
        method = 'GET'
        timestamp = self.get_time_stamp()
        if contract_types == None:
            query_string = f''
        else:
            query_string = f'?contract_types={contract_types}'
        payload = ''
        signature_data = method + timestamp + endpoint + query_string + payload
        signature = self.generate_signature(self.api_secret, signature_data)

        req_headers = {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'User-Agent': 'rest-client',
            'Content-Type': 'application/json'
        }

        if contract_types == None:
            query = f''
        else:
            query = {"contract_types": f'{contract_types}'}

        response = requests.get(
            url, params=query, timeout=(3, 27)
        )
        return response

    def get_ticker_product(self):
        headers = {
        'Accept': 'application/json'
        }

        r = requests.get('https://api.delta.exchange/v2/tickers', params={

        }, headers = headers)

        return r
    
    def get_ticker_product_with_symbol(self,symbol):
        headers = {
        'Accept': 'application/json'
        }

        r = requests.get(f'https://api.delta.exchange/v2/tickers/{symbol}', params={

        }, headers = headers)

        return r


    def get_ohlc(self,symbol,resolution,start,end):
        headers = {
        'Accept': 'application/json'
        }

        r = requests.get('https://api.delta.exchange/v2/history/candles', params={
        'resolution': f'{resolution}',  'symbol': f'{symbol}',  'start': f'{start}',  'end': f'{end}'
        }, headers = headers)

        return r
# Usage


# api_key = 'FyFjmvYAlbhFyU8Gt0PniA3bS3ucky'  # Fill in your API key
# api_secret = '4WNBHW6oJ4Qr80GKsEp4fmupQ05g7dJkm7w91iueg9gtt4LrGPQkSRXD0qXK'  # Fill in your API secret

# api = DeltaExchangeAPI(api_key, api_secret)
# # open_positions = api.get_positions_margined()
# products = api.get_product()
# print(products.json())  