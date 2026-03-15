# tests/test_calculate_net_from_ral.py
import pytest
import pandas as pd
from unittest.mock import MagicMock
from project_builder_jhr.services.tax import calculate_net_from_ral


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_cfg(
    comunale_aliquota: float = 0.008,
    regionale_aliquota: float = 0.0123,
    comune: str = "ROMA",
    regione: str = "LAZIO",
):
    """Build a minimal mock ConfigClass for tests."""
    cfg = MagicMock()

    # --- dati (from YAML) ---
    cfg.dati.contributi_dipendente.aliquota_base = 0.0919
    cfg.dati.cuneo_fiscale = MagicMock()        # passed through to calcolo_cuneo_fiscale
    cfg.dati.tassazione_irpef.scaglioni = [     # adjust shape to match your Dati model
        MagicMock(fino_a=28000, aliquota=0.23),
        MagicMock(fino_a=50000, aliquota=0.33),
        MagicMock(fino_a=None,  aliquota=0.43),
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
    result = calculate_net_from_ral(40000, 12, "ROMA", "LAZIO", cfg)
    expected_inps = 40000 * 0.0919
    assert result.contributo_inps == pytest.approx(expected_inps, rel=1e-6)


# ---------------------------------------------------------------------------
# IRPEF bracket boundaries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ral, expected_bracket", [
    (20000, "first"),   # <= 28k → flat 23%
    (28000, "first"),   # boundary: exactly 28k -> imponibile will be less
    (28001, "first"),  # just above → 33% on excess
    (50000, "second"),  # boundary: exactly 50k ral -> imponibile will be less
    (50001, "second"),   # just above → 43% on excess -> imponibile will be less
    (80000, "third"), # last bracket
])
def test_irpef_bracket(ral, expected_bracket, cfg):
    result = calculate_net_from_ral(ral, 12, "ROMA", "LAZIO", cfg)
    imponibile = result.imponibile_fiscale

    if expected_bracket == "first":
        assert result.irpef == pytest.approx(imponibile * 0.23, rel=1e-4)
    elif expected_bracket == "second":
        assert result.irpef == pytest.approx(6440 + (imponibile - 28000) * 0.33, rel=1e-4)
    else:
        assert result.irpef == pytest.approx(13700 + (imponibile - 50000) * 0.43, rel=1e-4)


# ---------------------------------------------------------------------------
# Detrazioni capped at irpef lorda
# ---------------------------------------------------------------------------

def test_detrazioni_never_exceed_irpef_lorda(cfg):
    # Very low RAL → detrazioni likely exceed irpef lorda
    result = calculate_net_from_ral(5000, 12, "ROMA", "LAZIO", cfg)
    assert result.detrazioni <= result.irpef


# ---------------------------------------------------------------------------
# Addizionale comunale
# ---------------------------------------------------------------------------

def test_comune_not_found_raises(cfg):
    with pytest.raises(KeyError, match="UNKNOWN"):
        calculate_net_from_ral(40000, 12, "UNKNOWN", "LAZIO", cfg)

def test_comune_wrong_regione_raises(cfg):
    with pytest.raises(KeyError):
        calculate_net_from_ral(40000, 12, "ROMA", "SICILIA", cfg)


# ---------------------------------------------------------------------------
# Addizionale regionale
# ---------------------------------------------------------------------------

def test_regione_not_found_raises(cfg):
    with pytest.raises(KeyError, match="UNKNOWN_REGIONE"):
        calculate_net_from_ral(40000, 12, "ROMA", "UNKNOWN_REGIONE", cfg)

# ---------------------------------------------------------------------------
# Valid net calculation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ral, expected_net", [
    (35000, 25000),
    (55000, 35500), 
    (60000, 37500), 
])
def test_net_calculation(ral, expected_net, cfg):
    result = calculate_net_from_ral(ral, 12, "MILANO", "LOMBARDIA", cfg)
    imponibile = result.imponibile_fiscale
    assert result.netto == pytest.approx(expected_net, rel=2e-2)
