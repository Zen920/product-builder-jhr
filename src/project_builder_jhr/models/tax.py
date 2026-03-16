from dataclasses import dataclass, field, asdict
from decimal import Decimal
import logging.config
logger = logging.getLogger("src.models.tax.py")
# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
 
@dataclass
class TaxResult:
    ral: Decimal
    contributo_inps: Decimal
    cuneo: Decimal
    imponibile_fiscale: Decimal
    irpef: Decimal 
    addizionale_comunale: Decimal
    addizionale_regionale: Decimal
    imposta_lorda: Decimal 
    detrazioni: Decimal
    imposta_netta: Decimal
    netto: Decimal 
    netto_mensile: Decimal
 
    def log_summary(self) -> None:  
        logger.info(
            "Tax calculation summary | RAL=%.2f | INPS=%.2f | cuneo=%.2f | "
            "imponibile=%.2f | IRPEF=%.2f | det.=%.2f | add.reg=%.2f | "
            "add.com=%.2f | imposta_netta=%.2f | netto=%.2f | "
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
    
