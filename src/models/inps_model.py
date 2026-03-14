from pydantic import BaseModel, field_validator, Field
from typing import Literal
class Esonero(BaseModel):
    soglia: int
    detrazione: float
class Range(BaseModel):
    min: int
    max: int
    @field_validator("max")
    def check_max(max: int):
        if max >= -1:
            return max
        raise ValueError(f"Value {max} is invalid. Ensure that it is a positive number or -1 if it has no maximum value.")
class Detrazioni(Range):
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
                return self.base + (self.incremento * (self.max - ral)/self.denominatore) + bonus
            case 'multiply':
                return self.base * (self.incremento * (self.max - ral)/self.denominatore) + bonus
            case _:
                return self.base
class CuneoFiscale(Range):
    fascia : int
    percentage_benefit: float = Field(default = 0.0)
    flat_benefit: int = Field(default = 0.0)
    diminishing_factor : float = Field(default = 0.0)
    
    def calcolo_cuneo_fiscale(self, ral):
        if self.diminishing_factor > 0.0:
            return (self.max - ral) * self.diminishing_factor
        elif self.percentage_benefit > 0:
            return ral * self.percentage_benefit
        else:
            return ral * self.percentage_benefit + self.flat_benefit
        return 0
class Scaglioni(Range):
    nome: str
    aliquota: float
    
    @field_validator("nome")
    def check_name(name: str):
        if name and name.isalpha():
            return name
        return name
        #raise ValueError(f"Value {name} is not a proper name.")


class Contributi(BaseModel):
    aliquota_base: float
    aliquota_solidarieta: float

class Tassazioni(BaseModel):
    anno_riferimento: int
    scaglioni: list[Scaglioni]

class Dati(BaseModel):
    esonero: list[Esonero]
    tassazione_irpef: Tassazioni
    contributi_dipendente: Contributi    
    detrazioni: list[Detrazioni]
    cuneo_fiscale: list[CuneoFiscale]
    

class AliquotaRegione(BaseModel):
    name: str
    
