import re
from src.models.inps_model import Scaglioni, Detrazioni
from src.models.tax import Bracket, TaxResult
from functools import cache
from src.config.config import config_class as _default_config
import pandas as pd
import logging.config
logger = logging.getLogger("src.services.tax")
# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
 
_SANITIZE_RE = re.compile(
    r'(,(?=[0-9]*[^,]$))|([.](?=[0-9]{1,3}[.|,]))'
)
_BRACKET_RE = re.compile(
    r'((?:oltre [ A-Za-z,.]|(?:da euro [ A-Za-z,.]))*(?P<min_value>[0-9.,]+))'
    r'|(?:fino a [ A-Za-z,.]*(?P<max_value>[0-9.,]+))'
)
def _calcola_irpef(scaglioni: list[Scaglioni], ral):
    contributo_lavoratore : float = 0
    remaining_ral = ral
    for scaglione in scaglioni:
        if ral > scaglione.min and (ral <= scaglione.max or scaglione.max == -1):
            contributo_lavoratore+=remaining_ral*scaglione.aliquota
            remaining_ral -= scaglione.max-scaglione.min
            break
        elif ral > scaglione.max:
            contributo_lavoratore+=abs(scaglione.max-scaglione.min)*scaglione.aliquota
            remaining_ral -= abs(scaglione.max-scaglione.min)
    return contributo_lavoratore

def _calcola_detrazioni(detrazioni: list[Detrazioni], ral):
    detrazione =  next((detrazione for detrazione in detrazioni if ral <= detrazione.max), None)
    return detrazione.calcolo_detrazioni(ral) if detrazione else 0

def _aliquota_percentage_parser(aliquota: str):
    return float(aliquota.replace(",","."))/100
def _aliquota_comunale_cleaner(v: str) -> float:
    return float(v.replace('.', '').replace(',','.'))

def _format_decimals(match):
    char = match.group(0)
    return '.' if char  == ',' else '' 
def _parse_brackets_range(text: str):
    """
    Extract (low, high) bounds from a bracket description string.
 
    Returns (0.0, 0.0) when the pattern is not found (open-ended bracket).
    """
    m = _BRACKET_RE.finditer(text)
    if not m:
        return 0.0, 0.0
    results = {}
    for match in m:
        results.update({k: v for k, v in match.groupdict().items() if v is not None})
    else:
        return sanitize_values(results.get('min_value', '0')), sanitize_values(results.get('max_value', '0'))
@cache
def sanitize_values(value) -> float:
    if type(value) == float or type(value) != str:
        return value
    if not value or value == '0*':
        return 0.0
    return float(_SANITIZE_RE.sub(_format_decimals, value))
def _create_brackets(ser):
    raw_brackets: list[str] = []
    raw_rates: list[float] = []
    
    for col in ser.index:
        if col.startswith('FASCIA'):
            raw_brackets.append(str(ser[col]))
        elif col.startswith('ALIQUOTA'):
            raw_rates.append(sanitize_values(ser[col]))
    if len(raw_brackets) != len(raw_rates):
        if len(raw_rates) == 1 and raw_rates[0] == 0.0 and len(raw_brackets) == 0:
            return ['0.00', '0.00'], raw_rates
        raise ValueError(
            f"Mismatched FASCIA/ALIQUOTA columns: "
            f"{len(raw_brackets)} brackets vs {len(raw_rates)} rates"
        )
    return raw_brackets, raw_rates
def _build_brackets(ser: pd.Series, divide_rate_by: float = 100.0) -> tuple[Bracket, ...]:
    """Build a list of Bracket objects from a filtered Series."""
    raw_brackets, raw_rates = _create_brackets(ser)
    return list(
        Bracket(low=low, high=high, rate=rate / divide_rate_by)
        for (low, high), rate in zip(map(_parse_brackets_range, raw_brackets), raw_rates)
    )
def _calcola_nel_bracket():
    for b in brackets:
        if imponibile > b.high:
            if b.low == 0 and b.high == 0:
                aliquota_comunale += remaining_imponibile*b.rate
                break 
            aliquota_comunale +=b.width*b.rate
            remaining_imponibile -= b.width
        else:
            #aliquota_comunale += abs(b.width-remaining_imponibile)*b.rate
            aliquota_comunale += remaining_imponibile*b.rate
            break
    return aliquota_comunale
def _calcola_addizionale_comunale(ser, imponibile):
    filtered = ser.filter(regex=r'^FASCIA|ALIQUOTA(_[0-9]+)*')
    esenzione_raw = float(sanitize_values(ser.get('IMPORTO_ESENTE', None)))
    try:
        esenzione = float(esenzione_raw) if esenzione_raw is not None else None
    except (ValueError, TypeError):
        logger.warning("Could not parse IMPORTO_ESENTE value: %r", esenzione_raw)
        esenzione = None
    #raw_brackets, raw_rates = _create_brackets(filtered)
    brackets = _build_brackets(filtered, 100)
    """brackets = list(
        Bracket(low=low, high=high, rate=rate / 100)
        for (low, high), rate in zip(
            map(_parse_brackets_range, raw_brackets), raw_rates
        )
    )"""
    discovered_esenzione = next(((index, b.high) for index, b in enumerate(brackets) if b.rate == 0.0), None)
    esenzione = max(esenzione, discovered_esenzione[1])
    if esenzione is not None:
        if imponibile <= esenzione:
            logger.debug("Addizionale comunale: 0 (below esenzione=%.2f)", esenzione)
            return 0.0
        brackets.pop(discovered_esenzione[0])
    aliquota_comunale = 0
    remaining_imponibile = imponibile
    for b in brackets:
        addizionale, remaining_imponibile = b.calcola_addizionale(imponibile=imponibile, remaining_imponibile=remaining_imponibile)
        aliquota_comunale+=addizionale
        if remaining_imponibile <= 0:
            break
    return aliquota_comunale
def _apply_brackets(brackets: list[Bracket], imponibile: float) -> float:
    """
    Core bracket iteration: handles esenzione check and accumulation.
    Shared by both comunale and regionale calculations.
    """
    if not brackets:
        logger.warning("No brackets found; returning 0.")
        return 0.0

    discovered_esenzione = next(
        ((index, b.high) for index, b in enumerate(brackets) if b.rate == 0.0),
        None
    )
    if discovered_esenzione is not None:
        index, threshold = discovered_esenzione
        if imponibile <= threshold:
            logger.debug("Below esenzione=%.2f; returning 0.", threshold)
            return 0.0
        brackets.pop(index)

    result = 0.0
    remaining_imponibile = imponibile
    for b in brackets:
        addizionale, remaining_imponibile = b.calcola_addizionale(
            imponibile=imponibile,
            remaining_imponibile=remaining_imponibile,
        )
        result += addizionale
        if remaining_imponibile <= 0:
            break
    return result


def _calcola_addizionale_comunale(ser: pd.Series, imponibile: float) -> float:
    filtered = ser.filter(regex=r'^FASCIA|ALIQUOTA(_[0-9]+)*')

    esenzione_raw = sanitize_values(ser.get('IMPORTO_ESENTE', None))
    try:
        esenzione = float(esenzione_raw) if esenzione_raw is not None else None
    except (ValueError, TypeError):
        logger.warning("Could not parse IMPORTO_ESENTE: %r", esenzione_raw)
        esenzione = None
    brackets = _build_brackets(filtered, 100)
    bracket_esenzione = next((b.high for b in brackets if b.rate == 0.0), None)
    if esenzione is not None and bracket_esenzione is not None:
        esenzione = max(esenzione, bracket_esenzione)
    elif bracket_esenzione is not None:
        esenzione = bracket_esenzione

    if esenzione is not None and imponibile <= esenzione:
        logger.debug("Addizionale comunale: 0 (below esenzione=%.2f)", esenzione)
        return 0.0

    return _apply_brackets(brackets, imponibile)


def _calcola_addizionale_regionale(ser: pd.Series, imponibile: float) -> float:
    filtered = ser.filter(regex=r'^FASCIA|ALIQUOTA')

    if isinstance(filtered, pd.DataFrame):
        brackets = [
            Bracket(low=low, high=high, rate=rate / 100)
            for _, row in filtered.iterrows()
            for (low, high), rate in zip(
                map(_parse_brackets_range, *_create_brackets(row)[0:1]),
                _create_brackets(row)[1]
            )
        ]
    else:
        brackets = list(_build_brackets(filtered))

    return _apply_brackets(brackets, imponibile)
def calcolo_cuneo_fiscale(ral, cuneo_fiscale):
    fascia_cuneo = next((f for f in cuneo_fiscale if f.min <= ral <= f.max), None)
    if fascia_cuneo:
        return fascia_cuneo.calcolo_cuneo_fiscale(ral)
    return 0
#@st.cache_data        
def calculate_net_from_ral(ral: float, months: int, comune : str, regione : str, mesi : int = 12, config_class=_default_config) -> float:
    """
    https://www.agenziaentrate.gov.it/portale/imposta-sul-reddito-delle-persone-fisiche-irpef-/aliquote-e-calcolo-dell-irpef
    x <= fino a euro 28.000 | 23% | 23% sull’intero importo

    28.000 < x <= 50.000 | 33% | 6.440 euro + 33% sul reddito che supera i 28.000 euro fino a 50.000 euro

    x > 50000 | 43% | 13.700 euro + 43% sul reddito che supera i 50.000 euro
    Contributi INPS = 9.19%
    :return:
    """
    cfg = config_class.dati
    
    # --- Imponibile fiscale -----------------------------------------------------
    
    cuneo = calcolo_cuneo_fiscale(ral, cfg.cuneo_fiscale)
    contributo_inps = ral * float(cfg.contributi_dipendente.aliquota_base)
    imponibile_fiscale = ral - contributo_inps + cuneo
    
    # --- Addizionale comune -----------------------------------------------------
    
    comuni_df = config_class.addizionali_comunali
    mask = (comuni_df["COMUNE"] == comune) & (comuni_df["Denominazione Regione"] == regione)
    matching = comuni_df.loc[mask]
    if matching.empty:
        raise KeyError(f"Comune '{comune}' in regione '{regione}' not found in addizionali comunali.")
    ser_comune = matching.iloc[0].dropna()
    addizionale_comunale = _calcola_addizionale_comunale(ser_comune, imponibile_fiscale)
 
    # --- Addizionale regionale ------------------------------------------------------
    
    try:
        ser_reg = config_class.addizionali_regionali.loc[regione]
    except KeyError:
        raise KeyError(f"Regione '{regione}' not found in addizionali regionali.")
    ser_reg = ser_reg.dropna()
    addizionale_regionale = _calcola_addizionale_regionale(ser_reg, imponibile_fiscale)
    
    # --- Irpef -----------------------------------------------------
    
    irpef_lorda = _calcola_irpef(cfg.tassazione_irpef.scaglioni, imponibile_fiscale)
    detrazioni = _calcola_detrazioni(cfg.detrazioni, imponibile_fiscale)
    if detrazioni > irpef_lorda:
        detrazioni = irpef_lorda
    imposta_lorda = irpef_lorda - detrazioni + addizionale_comunale + addizionale_regionale
    imposta_netta = imposta_lorda
    netto = imponibile_fiscale - imposta_netta
    result = TaxResult(ral = ral,
        contributo_inps = contributo_inps,
        cuneo= cuneo,
        imponibile_fiscale= imponibile_fiscale,
        irpef= irpef_lorda,
        addizionale_comunale= addizionale_comunale,
        addizionale_regionale= addizionale_regionale,
        imposta_lorda= imposta_lorda, # (irpef + addizionali)
        detrazioni= detrazioni,
        imposta_netta= imposta_lorda,
        netto= netto,
        netto_mensile= netto/mesi
    )
    result.log_summary()
    return result