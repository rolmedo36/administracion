import requests
from decouple import config  # ← Importar desde decouple
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class FacturaDigitalClient:
    def __init__(self):
        self.api_key = config('FACTURADIGITAL_API_KEY')  # ← Usar config()
        self.base_url = config('FACTURADIGITAL_URL')  # ← Usar config()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def timbrar_factura(self, cfdi_data):
        """
        Timbra una factura CFDI usando la API de FacturaDigital.
        """
        try:
            url = f"{self.base_url}/cfdi33"
            response = requests.post(url, json=cfdi_data, headers=self.headers, timeout=30)

            if response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                raise ValidationError(f"Error de validación: {error_data.get('message', 'Error desconocido')}")
            elif response.status_code == 401:
                raise ValidationError("Error de autenticación: API Key inválida")
            else:
                raise ValidationError(f"Error del servidor: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            raise ValidationError("Timeout: El servidor de FacturaDigital no responde")
        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Error de conexión: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado al timbrar con FacturaDigital: {str(e)}")
            raise ValidationError(f"Error al timbrar la factura: {str(e)}")


# Instancia global
facturadigital_client = FacturaDigitalClient()