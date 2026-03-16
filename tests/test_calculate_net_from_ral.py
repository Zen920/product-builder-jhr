# tests/test_calculate_net_from_ral.py
import pytest
import pandas as pd
from unittest.mock import MagicMock
from project_builder_jhr.services.tax import calculate_net_from_ral, calcola_detrazioni
from project_builder_jhr.models.inps_model import Detrazioni
from decimal import Decimal

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_cfg(
    comunale_aliquota: Decimal = Decimal('0.008'),
    regionale_aliquota: Decimal = Decimal('0.0123'),
    comune: str = "ROMA",
    regione: str = "LAZIO",
):
    cfg = MagicMock()

    # --- dati (from YAML) ---
    cfg.dati.contributi_dipendente.aliquota_base = Decimal('0.0919')
    cfg.dati.cuneo_fiscale = MagicMock()
    cfg.dati.tassazione_irpef.scaglioni = [
        MagicMock(fino_a=Decimal('28000'), aliquota=Decimal('0.23')),
        MagicMock(fino_a=Decimal('50000'), aliquota=Decimal('0.33')),
        MagicMock(fino_a=None, aliquota=Decimal('0.43')),
    ]
    cfg.dati.detrazioni = MagicMock()

    # --- addizionali_comunali ---
    cfg.addizionali_comunali = pd.DataFrame([{
        "COMUNE": comune,
        "Denominazione Regione": regione,
        "aliquota": comunale_aliquota,
    }])

    # --- addizionali_regionali ---
    cfg.addizionali_regionali = pd.DataFrame(
        [{"aliquota": regionale_aliquota}],
        index=pd.Index([regione], name="REGIONE"),
    )

    return cfg


@pytest.fixture
def cfg():
    return _make_cfg()


# ---------------------------------------------------------------------------
# INPS contribution
# ---------------------------------------------------------------------------

def test_inps_is_9_19_percent_of_ral(cfg):
    result = calculate_net_from_ral(Decimal('40000'),  "ROMA", "LAZIO", cfg)
    expected_inps = Decimal('40000') * Decimal('0.0919')
    assert result.contributo_inps == pytest.approx(expected_inps, rel=Decimal('1e-6'))


# ---------------------------------------------------------------------------
# IRPEF bracket boundaries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ral, expected_bracket", [
    (Decimal('20000'), "first"),
    (Decimal('28000'), "first"),
    (Decimal('28001'), "first"),
    (Decimal('50000'), "second"),
    (Decimal('50001'), "second"),
    (Decimal('80000'), "third"),
])
def test_irpef_bracket(ral, expected_bracket, cfg):
    result = calculate_net_from_ral(ral,  "ROMA", "LAZIO", cfg)
    imponibile = result.imponibile_fiscale

    if expected_bracket == "first":
        assert result.irpef == pytest.approx(imponibile * Decimal('0.23'), rel=Decimal('1e-4'))
    elif expected_bracket == "second":
        assert result.irpef == pytest.approx(Decimal('6440') + (imponibile - Decimal('28000')) * Decimal('0.33'), rel=Decimal('1e-4'))
    else:
        assert result.irpef == pytest.approx(Decimal('13700') + (imponibile - Decimal('50000')) * Decimal('0.43'), rel=Decimal('1e-4'))


# ---------------------------------------------------------------------------
# Detrazioni capped at irpef lorda
# ---------------------------------------------------------------------------

def test_detrazioni_never_exceed_irpef_lorda_low_ral(cfg):
    result = calculate_net_from_ral(Decimal('5000'),  "ROMA", "LAZIO", cfg)
    assert result.detrazioni <= result.irpef

def test_detrazioni_never_exceed_irpef_lorda_mid_ral(cfg):
    result = calculate_net_from_ral(Decimal('30000'),  "ROMA", "LAZIO", cfg)
    assert result.detrazioni <= result.irpef


# ---------------------------------------------------------------------------
# Addizionale comunale
# ---------------------------------------------------------------------------

def test_comune_not_found_raises(cfg):
    with pytest.raises(KeyError, match="UNKNOWN"):
        calculate_net_from_ral(Decimal('40000'),  "UNKNOWN", "LAZIO", cfg)

def test_comune_wrong_regione_raises(cfg):
    with pytest.raises(KeyError):
        calculate_net_from_ral(Decimal('40000'),  "ROMA", "SICILIA", cfg)


# ---------------------------------------------------------------------------
# Addizionale regionale
# ---------------------------------------------------------------------------

def test_regione_not_found_raises(cfg):
    with pytest.raises(KeyError, match="UNKNOWN_REGIONE"):
        calculate_net_from_ral(Decimal('40000'), "ROMA", "UNKNOWN_REGIONE", cfg)


# ---------------------------------------------------------------------------
# Valid net calculation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ral, expected_net", [
    (Decimal('35000'), Decimal('25000')),
    (Decimal('55000'), Decimal('35500')),
    (Decimal('60000'), Decimal('37500')),
])
def test_net_calculation(ral, expected_net, cfg):
    result = calculate_net_from_ral(ral, "MILANO", "LOMBARDIA", cfg)
    assert result.netto == pytest.approx(expected_net, rel=Decimal('2e-2'))