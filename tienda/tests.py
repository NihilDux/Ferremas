# tests/test_services.py
from unittest import TestCase
from django.test import RequestFactory
from django.urls import reverse
from datetime import datetime, timedelta
from unittest.mock import patch, call, MagicMock
from src.services.localApi import get_products, get_money
from .views import checkout
from transbank.webpay.webpay_plus.transaction import Transaction, TransbankError

class UtilsTestCase(TestCase):

    @patch('src.services.localApi.requests.get')
    def test_get_products(self, mock_get):
        # Respuesta simulada para requests.get
        response_200 = MagicMock()
        response_200.status_code = 200
        response_200.json.return_value = {
            "Productos": [
                {
                    "categoria": "Equipos de Seguridad",
                    "codigo": "FER-19876",
                    "descripcion": "Uso: Agrícola, Construcción, General, Jardín, Logística, Transporte, Otros.",
                    "id": 1,
                    "imagen": "627b742de5bc3024774264894d13359b.png",
                    "marca": "BAUKER",
                    "nombre": "Zapato de Trabajo",
                    "precio": 29990,
                    "relevante": True,
                    "stock": 200
                },
                {
                    "categoria": "Equipos de Seguridad",
                    "codigo": "FER-67891",
                    "descripcion": "Casco de seguridad blanco Modelo V guard MSA, diseñado para proteger la cabeza del impacto de objetos que caen libremente, fabricado en polietileno, se distingue por su clásico diseño y excelente terminación, modelo ajustable en la parte trasera.",
                    "id": 2,
                    "imagen": "ef35f39184b48daf7a84f04e498f45cc.png",
                    "marca": "MSA",
                    "nombre": "Casco de seguridad",
                    "precio": 11990,
                    "relevante": True,
                    "stock": 250
                }
            ]
        }

        # Configurar el mock para devolver la respuesta simulada
        mock_get.return_value = response_200

        # Llamar a la función que estamos probando
        result = get_products()

        # Verificar que la función devuelva el valor esperado
        expected_result = {
            "Productos": [
                {
                    "categoria": "Equipos de Seguridad",
                    "codigo": "FER-19876",
                    "descripcion": "Uso: Agrícola, Construcción, General, Jardín, Logística, Transporte, Otros.",
                    "id": 1,
                    "imagen": "627b742de5bc3024774264894d13359b.png",
                    "marca": "BAUKER",
                    "nombre": "Zapato de Trabajo",
                    "precio": 29990,
                    "relevante": True,
                    "stock": 200
                },
                {
                    "categoria": "Equipos de Seguridad",
                    "codigo": "FER-67891",
                    "descripcion": "Casco de seguridad blanco Modelo V guard MSA, diseñado para proteger la cabeza del impacto de objetos que caen libremente, fabricado en polietileno, se distingue por su clásico diseño y excelente terminación, modelo ajustable en la parte trasera.",
                    "id": 2,
                    "imagen": "ef35f39184b48daf7a84f04e498f45cc.png",
                    "marca": "MSA",
                    "nombre": "Casco de seguridad",
                    "precio": 11990,
                    "relevante": True,
                    "stock": 250
                }
            ]
        }
        self.assertEqual(result, expected_result)

        # Verificar que requests.get fue llamado con la URL correcta
        products_url = 'http://localhost:5000/get/products'
        mock_get.assert_called_once_with(products_url)
        
    @patch('src.services.localApi.requests.get')
    @patch('src.services.localApi.datetime')
    @patch('src.services.localApi.os.getenv')
    def test_get_money(self, mock_getenv, mock_datetime, mock_get):
        # Configurar mock para os.getenv
        mock_getenv.return_value = 'fake_api_key'

        # Configurar mock para datetime
        fixed_now = datetime(2023, 6, 20)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.strptime.side_effect = lambda *args, **kwargs: datetime.strptime(*args, **kwargs)
        mock_datetime.strftime.side_effect = lambda date, fmt: date.strftime(fmt)

        # Respuestas simuladas para requests.get
        response_200 = MagicMock()
        response_200.status_code = 200
        response_200.json.return_value = {"Dolares": [{"Valor": "934,92", "Fecha": "2024-06-17"}]}

        response_404 = MagicMock()
        response_404.status_code = 404

        # Configurar secuencia de respuestas del mock
        mock_get.side_effect = [response_404, response_200]

        # Llamar a la función que estamos probando
        result = get_money()

        # Verificar que la función devuelva el valor esperado
        self.assertEqual(result, {"Dolares": [{"Valor": "934,92", "Fecha": "2024-06-17"}]})

        # Verificar que requests.get fue llamado con las URLs correctas
        api_key = 'fake_api_key'
        formato = 'json'
        
        # Generar las URLs dinámicamente
        date_first_call = fixed_now.strftime('%Y/%m/dias/%d')
        date_second_call = (fixed_now - timedelta(days=1)).strftime('%Y/%m/dias/%d')
        
        moneyApu_url = f'https://api.cmfchile.cl/api-sbifv3/recursos_api/dolar/{date_first_call}?apikey={api_key}&formato={formato}'
        moneyApiBack_url = f'https://api.cmfchile.cl/api-sbifv3/recursos_api/dolar/{date_second_call}?apikey={api_key}&formato={formato}'

        calls = [call(moneyApu_url), call(moneyApiBack_url)]
        mock_get.assert_has_calls(calls)

class TestCheckoutFunction(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_checkout_post_success(self):
        mock_create = MagicMock()
        mock_create.return_value = {'token': 'dummy_token', 'url': 'http://dummyurl.com'}

        with patch.object(Transaction, 'create', mock_create):
            url = reverse('checkout')
            data = {'total_carrito': '100'}
            request = self.factory.post(url, data)
            response = checkout(request)

            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('http://dummyurl.com?token_ws=dummy_token'))


    def test_checkout_get_authorized(self):
        mock_commit = MagicMock()
        mock_commit.return_value = {
            'status': 'AUTHORIZED',
            'vci': 'TSY',
            'amount': 339980,
            'buy_order': 'ordenCompra123456',
            'session_id': 'sesion1234557545',
            'card_detail': {'card_number': '6623'},
            'accounting_date': '0620',
            'transaction_date': '2024-06-21T02:03:19.068Z',
            'authorization_code': '1213',
            'payment_type_code': 'VD',
            'response_code': 0,
            'installments_number': 0
        }

        with patch('tienda.views.Transaction') as MockTransaction:
            mock_transaction = MockTransaction.return_value
            mock_transaction.commit = mock_commit

            url = reverse('checkout')
            token = 'dummy_token'
            request = self.factory.get(url, {'token_ws': token})
            response = checkout(request)

            self.assertEqual(response.status_code, 200)
            self.assertIn('El estado de la transacción es: AUTHORIZED', response.content.decode('utf-8'))



    def test_checkout_get_failed(self):
        mock_commit = MagicMock()
        mock_commit.return_value = {
            'vci': 'TSY',
            'amount': 339980,
            'status': 'FAILED',
            'buy_order': 'ordenCompra123456',
            'session_id': 'sesion1234557545',
            'card_detail': {'card_number': '6623'},
            'accounting_date': '0620',
            'transaction_date': '2024-06-21T02:03:19.068Z',
            'authorization_code': '',
            'payment_type_code': '',
            'response_code': 0,
            'installments_number': 0
        }

        with patch.object(Transaction, 'commit', mock_commit):
            url = reverse('checkout')
            token = 'dummy_token'
            request = self.factory.get(url, {'token_ws': token})
            response = checkout(request)

            self.assertEqual(response.status_code, 200)
            
            self.assertIn('El estado de la transacción es: FAILED', response.content.decode('utf-8'))  


    def test_checkout_post_transbank_error(self):
        mock_create = MagicMock()
        mock_create.side_effect = TransbankError('Error simulado', 456)

        with patch.object(Transaction, 'create', mock_create):
            url = reverse('checkout')
            data = {'total_carrito': '100'}
            request = self.factory.post(url, data)
            response = checkout(request)

            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.content.decode(), 'Error al procesar la transacción')

    def test_checkout_get_no_token(self):
        url = reverse('checkout')
        request = self.factory.get(url)

        response = checkout(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), 'Token_ws no recibido')

    def test_checkout_invalid_method(self):
        url = reverse('checkout')
        request = self.factory.put(url)

        response = checkout(request)

        self.assertEqual(response.status_code, 405)
