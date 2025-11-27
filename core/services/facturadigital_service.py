from core.services.facturadigital import facturadigital_client
from django.core.exceptions import ValidationError
import base64
from core.models import Empresa


def timbrar_factura_venta(factura):
    """
    Timbra una factura de venta usando FacturaDigital.
    """
    try:
        empresa = Empresa.objects.first()
        if not empresa:
            raise ValidationError("No hay datos de la empresa configurados")

        # Validar que el cliente tenga datos fiscales
        if not factura.cliente.rfc or not factura.cliente.uso_cfdi or not factura.cliente.regimen_fiscal:
            raise ValidationError("El cliente no tiene datos fiscales completos")

        # Preparar los datos del receptor
        receptor = {
            "rfc": factura.cliente.rfc,
            "nombre": factura.cliente.nombre,
            "uso_cfdi": factura.cliente.uso_cfdi,
            "regimen_fiscal_receptor": factura.cliente.regimen_fiscal,
            "domicilio_fiscal_receptor": factura.cliente.codigo_postal
        }

        # Preparar los conceptos
        conceptos = []
        for detalle in factura.detalles.all():
            concepto = {
                "clave_prod_serv": "01010101",  # Predeterminado, ajustar según catálogo SAT
                "no_identificacion": detalle.material.codigo,
                "cantidad": str(detalle.cantidad),
                "clave_unidad": "E48",  # Unidad de servicio
                "unidad": "Servicio",
                "descripcion": detalle.material.nombre,
                "valor_unitario": str(detalle.precio_unitario),
                "importe": str(detalle.subtotal),
                "descuento": "0"
            }

            # Agregar impuestos si aplica
            if detalle.material.aplica_iva:
                concepto["impuestos"] = {
                    "traslados": [
                        {
                            "base": str(detalle.subtotal),
                            "impuesto": "002",  # IVA
                            "tipo_factor": "Tasa",
                            "tasa_o_cuota": "0.160000",
                            "importe": str(detalle.iva_monto)
                        }
                    ]
                }

            conceptos.append(concepto)

        # Preparar la factura CFDI
        cfdi_data = {
            "serie": "A",
            "folio": factura.folio,
            "fecha": factura.fecha.strftime("%Y-%m-%dT%H:%M:%S"),
            "sello": "",
            "no_certificado": "",
            "certificado": "",
            "subtotal": str(factura.subtotal),
            "total": str(factura.total),
            "moneda": "MXN",
            "tipo_cambio": "1",
            "tipo_de_comprobante": "I",  # Ingreso
            "metodo_pago": "PUE",
            "forma_pago": "99",
            "condiciones_de_pago": "CONTADO",
            "lugar_expedicion": empresa.domicilio_cp,
            "emisor": {
                "rfc": empresa.rfc,
                "nombre": empresa.razon_social,
                "regimen_fiscal": empresa.regimen_fiscal
            },
            "receptor": receptor,
            "conceptos": conceptos,
            "impuestos": {
                "total_impuestos_trasladados": str(factura.iva)
            }
        }

        # Timbrar la factura
        resultado = facturadigital_client.timbrar_factura(cfdi_data)

        # Guardar los datos del timbrado
        factura.uuid = resultado.get('uuid')
        factura.folio_fiscal = resultado.get('folio_fiscal')
        factura.fecha_timbrado = resultado.get('fecha_timbrado')
        factura.xml_timbrado = resultado.get('xml')
        factura.pdf_timbrado = base64.b64encode(resultado.get('pdf', b'')).decode('utf-8')
        factura.estado = 'timbrada'
        factura.save()

        return resultado

    except Exception as e:
        raise ValidationError(f"Error al timbrar la factura: {str(e)}")