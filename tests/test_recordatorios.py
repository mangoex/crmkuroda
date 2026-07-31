"""Unit tests for RecordatorioSeguimiento model and functionality."""

from __future__ import annotations

import unittest
from datetime import date, datetime
from uuid import uuid4
from types import SimpleNamespace

from app.models.recordatorio_seguimiento import RecordatorioSeguimiento


class RecordatorioSeguimientoTest(unittest.TestCase):
    def test_recordatorio_instantiation(self):
        cot_id = uuid4()
        vend_id = uuid4()
        today = date.today()

        recordatorio = RecordatorioSeguimiento(
            id=uuid4(),
            cotizacion_id=cot_id,
            vendedor_id=vend_id,
            fecha_programada=today,
            nota="Llamar al cliente para darle seguimiento al descuento",
            completado=False,
        )

        self.assertEqual(recordatorio.cotizacion_id, cot_id)
        self.assertEqual(recordatorio.vendedor_id, vend_id)
        self.assertEqual(recordatorio.fecha_programada, today)
        self.assertFalse(recordatorio.completado)
        self.assertIn("descuento", recordatorio.nota)


if __name__ == "__main__":
    unittest.main()
