import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

localApi_url = 'http://localhost:5000'


def get_users():
    response = requests.get(f'{localApi_url}/get/users')
    #print(response.json())
    return response.json()

def get_categories():
    response = requests.get(f'{localApi_url}/get/categories')
    #print(response.json())
    return response.json()

def get_money():
    tipoCambio = 'dolar'
    api_key = os.getenv("Cmf-Api-Key")
    formato = 'json'
    moneyApu_url = 'https://api.cmfchile.cl/api-sbifv3/recursos_api/'#dolar?apikey=0084b1f3fa7085b34c197465c9198b983ca1a685&formato=json
    moneyApiBack_url = 'https://api.cmfchile.cl/api-sbifv3/recursos_api/'#dolar/2024/06/dias/19?apikey=0084b1f3fa7085b34c197465c9198b983ca1a685&formato=json

    today = datetime.now().strftime('%Y/%m/dias/%d')
    date = today

    intentos = 0
    max_intentos = 4

    while intentos < max_intentos:
        key = f'?apikey={api_key}&formato={formato}'
        url = f'{moneyApu_url}{tipoCambio}/{date}{key}'

        response = requests.get(url)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            date = (datetime.strptime(date, '%Y/%m/dias/%d') - timedelta(days=1)).strftime('%Y/%m/dias/%d')
            url = f'{moneyApiBack_url}{tipoCambio}/{date}{key}'
            response = requests.get(url)

            if response.status_code == 200:
                return response.json()

        date = (datetime.strptime(date, '%Y/%m/dias/%d') - timedelta(days=1)).strftime('%Y/%m/dias/%d')
        intentos += 1
        
    return None

def get_products():
    response = requests.get(f'{localApi_url}/get/products')
    return response.json()

def get_product_by_id(producto_id):
    response = requests.get(f'{localApi_url}/get/product/{producto_id}')
    #print(response.json())
    return response.json()