from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, call, MagicMock
from src.services.localApi import get_money

class UtilsTestCase(TestCase):

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
