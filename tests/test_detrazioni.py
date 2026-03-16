import pytest
import pandas as pd
from unittest.mock import MagicMock
from product_builder_jhr.services.tax import calculate_net_from_ral, calcola_detrazioni
from product_builder_jhr.models.inps_model import Detrazioni
from decimal import Decimal
# ---------------------------------------------------------------------------
# Detrazioni overlap
# ---------------------------------------------------------------------------
@pytest.fixture
def detrazioni():
    return [
        Detrazioni(low=Decimal('0'), high=Decimal('15000'), base=Decimal('1955')),
        Detrazioni(low=Decimal('15000'), high=Decimal('28000'), base=Decimal('1910'), increment=Decimal('1190'), increment_op="sum"),
        Detrazioni(low=Decimal('28000'), high=Decimal('50000'), base=Decimal('1910'), increment=Decimal('1'), increment_op="multiply"),
        Detrazioni(low=Decimal('25000'), high=Decimal('35000'), base=Decimal('65'), increment_op="flat"),
    ]

# ---------------------------------------------------------------------------
# Detrazioni.calcolo_detrazioni — unit tests (formula correctness)
# ---------------------------------------------------------------------------

class TestCalcoloDetrazioni:
    def test_base_only(self):
        d = Detrazioni(low=Decimal('0'), high=Decimal('15000'), base=Decimal('1955'))
        assert d.calcolo_detrazioni(Decimal('5000')) == Decimal('1955')

    def test_sum_branch(self):
        d = Detrazioni(low=Decimal('15000'), high=Decimal('28000'), base=Decimal('1910'), increment=Decimal('1190'), increment_op="sum")
        ral = Decimal('20000')
        expected = Decimal('1910') + (Decimal('1190') * (Decimal('28000') - ral) / Decimal('13000'))
        assert d.calcolo_detrazioni(ral) == expected

    def test_multiply_branch(self):
        d = Detrazioni(low=Decimal('28000'), high=Decimal('50000'), base=Decimal('1910'), increment=Decimal('1'), increment_op="multiply")
        ral = Decimal('35000')
        expected = Decimal('1910') * (Decimal('1') * (Decimal('50000') - ral) / Decimal('22000'))
        assert d.calcolo_detrazioni(ral) == expected

    def test_flat_branch(self):
        d = Detrazioni(low=Decimal('25000'), high=Decimal('35000'), base=Decimal('65'), increment_op="flat")
        assert d.calcolo_detrazioni(Decimal('30000')) == Decimal('65')

# ---------------------------------------------------------------------------
# calcola_detrazioni — dispatch correctness (bracket selection)
# ---------------------------------------------------------------------------

class TestCalcolaDetrazioni:
    @pytest.mark.parametrize("ral", [Decimal('5000'), Decimal('10000'), Decimal('14999')])
    def test_dispatches_to_correct_bracket(self, ral, detrazioni):
        expected = next((d for d in detrazioni if d.low < ral <= d.high), None)
        expected_value = expected.calcolo_detrazioni(ral) if expected else 0
        assert calcola_detrazioni(detrazioni, ral) == pytest.approx(expected_value)

    def test_flat_bonus_added_in_range(self, detrazioni):
        ral = 30000  # falls in both multiply bracket and flat bonus
        multiply = next(d for d in detrazioni if d.increment_op == "multiply")
        flat = next(d for d in detrazioni if d.increment_op == "flat")
        expected = multiply.calcolo_detrazioni(ral) + flat.calcolo_detrazioni(ral)
        assert calcola_detrazioni(detrazioni, ral) == pytest.approx(expected)

    def test_flat_bonus_not_added_outside_range(self, detrazioni):
        ral = Decimal('20000')  # in sum bracket, outside flat bonus range
        result = calcola_detrazioni(detrazioni, ral)
        sum_bracket = next(d for d in detrazioni if d.increment_op == "sum")
        assert result == pytest.approx(sum_bracket.calcolo_detrazioni(ral))

    def test_above_all_brackets_returns_zero(self, detrazioni):
        assert calcola_detrazioni(detrazioni, Decimal('60000')) == pytest.approx(0)

    def test_below_all_brackets_returns_zero(self, detrazioni):
        assert calcola_detrazioni(detrazioni, 0) == pytest.approx(0)

    def test_empty_detrazioni_returns_zero(self):
        assert calcola_detrazioni([], Decimal('20000') ) == pytest.approx(0)

    def test_boundary_low(self, detrazioni):
        # exactly at low should NOT match (low < ral <= high)
        assert calcola_detrazioni(detrazioni, Decimal('15000')) != calcola_detrazioni(detrazioni, Decimal('15001'))

    def test_boundary_high(self, detrazioni):
        # exactly at high should match
        d = next(d for d in detrazioni if d.high == Decimal('15000'))
        assert calcola_detrazioni(detrazioni, Decimal('15000')) == pytest.approx(d.calcolo_detrazioni(Decimal('15000')))