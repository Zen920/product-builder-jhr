from dataclasses import dataclass, field, asdict
import logging.config
logger = logging.getLogger("src.models.tax.py")
# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
 
@dataclass
class TaxResult:
    ral: float
    contributo_inps: float
    cuneo: float
    imponibile_fiscale: float
    irpef: float 
    addizionale_comunale: float
    addizionale_regionale: float
    imposta_lorda: float 
    detrazioni: float
    imposta_netta: float
    netto: float 
    netto_mensile: float
 
    def log_summary(self) -> None:  
        logger.info(
            "Tax calculation summary | RAL=%.2f | INPS=%.2f | cuneo=%.2f | "
            "imponibile=%.2f | IRPEF=%.2f | det.=%.2f | add.reg=%.2f | "
            "add.com=%.2f | imposta_netta=%.2f | netto=%.2f"
            "netto mensile=%.2f",
            self.ral,
            self.contributo_inps,
            self.cuneo,
            self.imponibile_fiscale,
            self.irpef,
            self.detrazioni,
            self.addizionale_regionale,
            self.addizionale_comunale,
            self.imposta_netta,
            self.netto,
            self.netto_mensile
        )
    
