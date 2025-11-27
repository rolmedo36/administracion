import facturama
from django.conf import settings
from django.core.exceptions import ValidationError

# Configurar Facturama
# facturama._api_url = settings.FACTURAMA_URL
# facturama.api_key = settings.FACTURAMA_API_KEY
# facturama.api_secret = settings.FACTURAMA_API_SECRET
facturama._api_url = 'http://facturama.com.mx'
facturama.api_key = '121212121212'
facturama.api_secret = '121212121212'


def timbrar_factura_venta(factura):
    """
    Timbra una factura de venta usando Facturama.
    """
    try:
        # Preparar los datos del cliente (receptor)
        receptor = {
            "Rfc": factura.cliente.rfc,
            "Name": factura.cliente.nombre,
            "CfdiUse": factura.cliente.uso_cfdi,
            "FiscalRegime": factura.cliente.regimen_fiscal,
            "TaxZipCode": factura.cliente.codigo_postal
        }

        # Preparar los conceptos (detalles)
        conceptos = []
        for detalle in factura.detalles.all():
            concepto = {
                "ProductCode": detalle.material.codigo,
                "IdentificationNumber": detalle.material.codigo,
                "Description": detalle.material.nombre,
                "Unit": "E48",  # Servicio
                "UnitCode": "E48",
                "Quantity": str(detalle.cantidad),
                "UnitPrice": str(detalle.precio_unitario),
                "Subtotal": str(detalle.subtotal),
                "Taxes": []
            }

            # Agregar IVA si aplica
            if detalle.material.aplica_iva:
                concepto["Taxes"].append({
                    "Total": str(detalle.iva_monto),
                    "Name": "IVA",
                    "Base": str(detalle.subtotal),
                    "Rate": "0.160000",
                    "IsRetention": False
                })

            conceptos.append(concepto)

        # Preparar la factura CFDI
        cfdi = {
            "Folio": factura.folio,
            "Currency": "MXN",
            "CfdiType": "I",  # Ingreso
            "PaymentForm": "99",  # Por definir
            "PaymentMethod": "PUE",  # Pago en una sola exhibición
            "ExpeditionPlace": "00000",  # Código postal de emisión
            "Receptor": receptor,
            "Items": conceptos,
            "Complements": []
        }

        # Timbrar la factura
        resultado = facturama.Cfd.create(cfdi)

        # Guardar el UUID y otros datos en la factura
        factura.uuid = resultado['Id']
        factura.folio_fiscal = resultado['Complemento']['TimbreFiscalDigital']['UUID']
        factura.cadena_original = resultado['Complemento']['TimbreFiscalDigital']['SelloCFD']
        factura.fecha_timbrado = resultado['Complemento']['TimbreFiscalDigital']['FechaTimbrado']
        factura.xml_timbrado = resultado['Xml']
        factura.pdf_timbrado = resultado['Pdf']
        factura.estado = 'timbrada'
        factura.save()

        return resultado

    except Exception as e:
        raise ValidationError(f"Error al timbrar la factura: {str(e)}")