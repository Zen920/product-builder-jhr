from pydantic import BaseModel, field_validator, Field
from typing import Literal
from pydantic import BaseModel
from decimal import Decimal
class Bracket(BaseModel):
    """Classe generale per definire il concetto di fascia e range."""
    low:  Decimal
    high: Decimal   # 0.0 means open-ended (no upper bound)
    rate: Decimal = Field(default=Decimal())   # already divided by 100

    @property
    def is_open_ended(self) -> bool:
        return self.low == 0.0 and self.high == 0.0
    
    @property
    def is_upper_unlimited(self) -> bool:
        return self.high == 0
    
    @property
    def width(self) -> Decimal:
        return abs(self.high - self.low)
    
    def calcola_nel_bracket(self, imponibile, remaining_imponibile) -> tuple[Decimal,Decimal]:
        if self.is_upper_unlimited:
            return remaining_imponibile * self.rate, 0
        if imponibile > self.high:
            return self.width * self.rate, remaining_imponibile - self.width
        return remaining_imponibile * self.rate, 0
    
class Detrazioni(Bracket):
    base: Decimal = Field(default = Decimal())
    increment: int = Field(default = Decimal())
    increment_op: Literal['sum', 'multiply', 'flat', None] = Field(default=None)
    def calcolo_detrazioni(self, ral):
        match self.increment_op:
            case 'sum':
                return self.base + (self.increment * (self.high - ral) / self.width)
            case 'multiply':
                return self.base * (self.increment * (self.high - ral) / self.width)
            case _:
                return self.base
class CuneoFiscale(Bracket):
    flat_benefit: Decimal = Field(default = Decimal())
    reduction_rate : Decimal = Field(default = Decimal())
    
    def calcolo_cuneo_fiscale(self, ral):
        if self.reduction_rate  > 0.0:
            return (self.high - ral) * self.reduction_rate
        elif self.rate > 0:
            return ral * self.rate
        else:
            return ral * self.rate + self.flat_benefit
        return Decimal()


class Contributi(BaseModel):
    aliquota_base: Decimal
    aliquota_solidarieta: Decimal

class Tassazioni(BaseModel):
    anno_riferimento: int
    scaglioni: list[Bracket]

class Dati(BaseModel):
    tassazione_irpef: Tassazioni
    contributi_dipendente: Contributi    
    detrazioni: list[Detrazioni]
    cuneo_fiscale: list[CuneoFiscale]

