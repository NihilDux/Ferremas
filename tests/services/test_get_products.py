from unittest import TestCase
from unittest.mock import patch, MagicMock
from src.services.localApi import get_products


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
        