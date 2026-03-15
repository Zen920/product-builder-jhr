from pydantic import BaseModel, field_validator, Field
from typing import Literal
from pydantic import BaseModel
class Bracket(BaseModel):
    """A single income bracket with its associated flat rate."""
    low:  float
    high: float   # 0.0 means open-ended (no upper bound)
    rate: float = Field(default=0.0)   # already divided by 100

    @property
    def is_open_ended(self) -> bool:
        return self.low == 0.0 and self.high == 0.0

    @property
    def width(self) -> float:
        return abs(self.high - self.low)
    
    def calcola_addizionale(self, imponibile, remaining_imponibile) -> tuple[float,float]:
        addizionale = 0
        if imponibile > self.high:
            if self.high == 0:
                if self.low == 0:
                    addizionale += remaining_imponibile*self.rate
                    remaining_imponibile = 0 
                else:
                    addizionale += remaining_imponibile*self.rate
            else:
                addizionale +=self.width*self.rate
                remaining_imponibile -= self.width
        else:
            #aliquota_comunale += abs(b.width-remaining_imponibile)*b.rate
            addizionale += remaining_imponibile*self.rate
            remaining_imponibile = 0
        return addizionale, remaining_imponibile
class Esonero(BaseModel):
    soglia: int
    detrazione: float
class Detrazioni(Bracket):
    fascia: int
    base: float = Field(default = 0.0)
    incremento: int = Field(default = 0)
    denominatore: float = Field(default = 1.0)
    increment_op: Literal['sum', "multiply", None] = Field(default=None)
    @field_validator("denominatore")
    def check_denominatore(denominatore: int | None):
        if denominatore and denominatore > 0:
            return denominatore
        if not denominatore:
            return 1
        raise ValueError("Denominatore must be either 1 or a positive number")
    def calcolo_detrazioni(self, ral):
        bonus = 65 if ral > 25000 and ral <= 35000 else 0
        match(self.increment_op):
            case 'sum':
                return self.base + (self.incremento * (self.high - ral)/self.denominatore) + bonus
            case 'multiply':
                return self.base * (self.incremento * (self.high - ral)/self.denominatore) + bonus
            case _:
                return self.base
class CuneoFiscale(Bracket):
    fascia : int
    flat_benefit: int = Field(default = 0.0)
    diminishing_factor : float = Field(default = 0.0)
    
    def calcolo_cuneo_fiscale(self, ral):
        if self.diminishing_factor > 0.0:
            return (self.high - ral) * self.diminishing_factor
        elif self.rate > 0:
            return ral * self.rate
        else:
            return ral * self.rate + self.flat_benefit
        return 0


class Contributi(BaseModel):
    aliquota_base: float
    aliquota_solidarieta: float

class Tassazioni(BaseModel):
    anno_riferimento: int
    scaglioni: list[Bracket]

class Dati(BaseModel):
    esonero: list[Esonero]
    tassazione_irpef: Tassazioni
    contributi_dipendente: Contributi    
    detrazioni: list[Detrazioni]
    cuneo_fiscale: list[CuneoFiscale]
    

class AliquotaRegione(BaseModel):
    name: str
    
