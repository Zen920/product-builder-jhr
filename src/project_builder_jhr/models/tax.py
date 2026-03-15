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
    
@dataclass(frozen=True, slots=True)
class Bracket:
    """A single income bracket with its associated flat rate."""
    low:  float
    high: float   # 0.0 means open-ended (no upper bound)
    rate: float   # already divided by 100

    @property
    def is_open_ended(self) -> bool:
        return self.low == 0.0 and self.high == 0.0

    @property
    def width(self) -> float:
        return abs(self.high - self.low)
    
    def calcola_addizionale(self, imponibile, remaining_imponibile) -> tuple[float,float]:
        addizionale = 0
        if imponibile > self.high:
            if self.low == 0 and self.high == 0:
                addizionale += remaining_imponibile*self.rate
                remaining_imponibile = 0
            else:
                addizionale +=self.width*self.rate
                remaining_imponibile -= self.width
        else:
            #aliquota_comunale += abs(b.width-remaining_imponibile)*b.rate
            addizionale += remaining_imponibile*self.rate
            remaining_imponibile = 0
        return addizionale, remaining_imponibile