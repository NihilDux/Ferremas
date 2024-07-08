from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import MagicMock, patch
from transbank.webpay.webpay_plus.transaction import Transaction, TransbankError
from django.contrib.sessions.middleware import SessionMiddleware

from tienda.views import checkout

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

    def add_session_to_request(self, request):
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

    @patch('tienda.views.requests.post')  # Simula la función requests.post
    def test_checkout_get_authorized(self, mock_post):
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

        mock_post.return_value.status_code = 200  # Simula una respuesta exitosa de la API

        with patch('tienda.views.Transaction') as MockTransaction:
            mock_transaction = MockTransaction.return_value
            mock_transaction.commit = mock_commit

            url = reverse('checkout')
            token = 'dummy_token'
            request = self.factory.get(url, {'token_ws': token})
            self.add_session_to_request(request)
            # Estructura del carrito según lo esperado por la vista
            request.session['carrito'] = {
                '1': {'nombre': 'Producto 1', 'precio_unitario': 1000, 'cantidad': 2, 'imagen': 'imagen1.jpg'},
                '2': {'nombre': 'Producto 2', 'precio_unitario': 2000, 'cantidad': 1, 'imagen': 'imagen2.jpg'}
            }

            response = checkout(request)
            #Resultados
            self.assertEqual(response.status_code, 200)
            self.assertIn('El estado de la transacción es: AUTHORIZED', response.content.decode('utf-8'))

            # Verifica que la simulación de la API fue llamada correctamente
            mock_post.assert_called_once_with(
                'http://127.0.0.1:5000/post/productos/subtract_stock',
                json={'productos': [
                    {'producto_id': '1', 'cantidad': 2},
                    {'producto_id': '2', 'cantidad': 1}
                ]}
            )



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