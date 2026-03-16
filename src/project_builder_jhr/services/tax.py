from project_builder_jhr.models.inps_model import Detrazioni, CuneoFiscale
from project_builder_jhr.models.tax import TaxResult
from project_builder_jhr.config.config import config_class as _default_config
from project_builder_jhr.helpers.brackets import build_brackets, apply_brackets
from decimal import Decimal
import pandas as pd
import logging.config
logger = logging.getLogger("src.services.tax")
# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def calcola_detrazioni(detrazioni: list[Detrazioni], ral: Decimal) -> Decimal:
    """Calculate tax detractions.

        Args:
            detrazioni: Lista delle detrazioni presenti (lavoro dipendente)
            ral: Valore della ral
        Returns:
            Decimal: Valore lordo delle detrazioni per lavoro dipendente 
    """
    return sum(
        d.calcolo_detrazioni(ral)
        for d in detrazioni
        if d.low < ral <= d.high
    )

def calcola_addizionale(ser: pd.Series | pd.DataFrame, imponibile: Decimal) -> Decimal:
    #filtered = ser.filter(regex=r'^FASCIA|ALIQUOTA')
    """Wrapper per il calcolo dei valori di tipo Bracket
        Args:
            ser: Serie da cui estrarre le informazione
            imponibile: Valore dell'imponibile fiscale
        Returns:
            Decimal: Valore lordo delle detrazioni per lavoro dipendente 
    """
    brackets = build_brackets(ser, 100)
    return apply_brackets(brackets, imponibile)

def calcolo_cuneo_fiscale(ral: Decimal, cuneo_fiscale: list[CuneoFiscale]):
    """
    Calcolo del cuneo fiscale
    Args:
        ral: Valore della ral
        cuneo_fiscale: Lista delle fasce relative al cuneo fiscale
    Returns:
        TaxResult: Container con tutte i valori calcolati tra cui imponibile, irpef, tasse e netto annuale.
    """
    fascia_cuneo = next((f for f in cuneo_fiscale if f.low < ral <= f.high), None)
    if fascia_cuneo:
        return fascia_cuneo.calcolo_cuneo_fiscale(ral)
    return Decimal()

def calculate_net_from_ral(ral: Decimal, comune : str, regione : str, mesi : int = 12, config_class=_default_config) -> Decimal:
    """
    Calcolo di netto e tasse a partire dalla ral.
    Args:
        ral: Valore della ral
        comune: Comune di residenza
        regione: Regione di residenza
        mesi: Mensilità percepite (12-14)
        config_class: Oggetto di configurazione necessario al calcolo, definito a partire dai .csv
    Returns:
        TaxResult: Container con tutte i valori calcolati tra cui imponibile, irpef, tasse e netto annuale.
    """
    cfg = config_class.dati
    
    # --- Imponibile fiscale -----------------------------------------------------
    
    cuneo = calcolo_cuneo_fiscale(ral, cfg.cuneo_fiscale)
    contributo_inps = ral * Decimal(cfg.contributi_dipendente.aliquota_base)
    imponibile_fiscale = ral - contributo_inps + cuneo

    # --- Addizionale comune -----------------------------------------------------
    
    comuni_df = config_class.addizionali_comunali
    mask = (comuni_df["COMUNE"] == comune) & (comuni_df["Denominazione Regione"] == regione)
    matching = comuni_df.loc[mask]
    if matching.empty:
        raise KeyError(f"Comune '{comune}' in regione '{regione}' not found in addizionali comunali.")
    ser_comune = matching.iloc[0].dropna()
    addizionale_comunale = calcola_addizionale(ser_comune, imponibile_fiscale)
 
    # --- Addizionale regionale ------------------------------------------------------
    
    try:
        ser_reg = config_class.addizionali_regionali.loc[regione]
    except KeyError:
        raise KeyError(f"Regione '{regione}' not found in addizionali regionali.")
    ser_reg = ser_reg.dropna()
    addizionale_regionale = calcola_addizionale(ser_reg, imponibile_fiscale)
    
    # --- Irpef -----------------------------------------------------
    
    irpef_lorda = apply_brackets(cfg.tassazione_irpef.scaglioni, imponibile_fiscale)
    detrazioni = calcola_detrazioni(cfg.detrazioni, imponibile_fiscale)
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