# tests/test_cuneo_fiscale
import pytest
import pandas as pd
from unittest.mock import MagicMock
from project_builder_jhr.services.tax import calcolo_cuneo_fiscale
from project_builder_jhr.models.inps_model import CuneoFiscale
from decimal import Decimal

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cuneo_fiscale():
    return [
        CuneoFiscale(low=Decimal('0'), high=Decimal('8500'), rate=Decimal('0.071')),
        CuneoFiscale(low=Decimal('8500'), high=Decimal('15000'), rate=Decimal('0.053')),
        CuneoFiscale(low=Decimal('15000'), high=Decimal('20000'), rate=Decimal('0.048')),
        CuneoFiscale(low=Decimal('20000'), high=Decimal('32000'), flat_benefit=Decimal('1000')),
        CuneoFiscale(low=Decimal('32000'), high=Decimal('40000'), flat_benefit=Decimal('1000'), reduction_rate =Decimal('0.125')),
    ]

@pytest.mark.parametrize("ral, expected", [
    (Decimal('5000'),  Decimal('5000')  * Decimal('0.071')),
    (Decimal('10000'), Decimal('10000') * Decimal('0.053')),
    (Decimal('19999'), Decimal('19999') * Decimal('0.048')),
    (Decimal('20000'), Decimal('20000') * Decimal('0.048')),
    (Decimal('20001'), Decimal('1000')),
    (Decimal('25000'), Decimal('1000')),
    (Decimal('35000'), (Decimal('40000') - Decimal('35000')) * Decimal('0.125')),
    (Decimal('50001'), Decimal('0')),
])
def test_calcolo_cuneo_fiscale(ral, expected, cuneo_fiscale):
    result = calcolo_cuneo_fiscale(ral, cuneo_fiscale)
    assert result == expected