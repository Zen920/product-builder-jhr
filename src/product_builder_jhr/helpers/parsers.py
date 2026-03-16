 
import re
from functools import cache
import logging.config
from decimal import Decimal
logger = logging.getLogger("helpers.parsers")
_SANITIZE_RE = re.compile(
    r'(,(?=[0-9]*[^,]$))|([.](?=[0-9]{1,3}[.|,]))'
)
_BRACKET_RE = re.compile(
    r'((?:oltre [ A-Za-z,.]|(?:da euro [ A-Za-z,.]))*(?P<min_value>[0-9.,]+))'
    r'|(?:fino a [ A-Za-z,.]*(?P<max_value>[0-9.,]+))'
)

def _format_decimals(match):
    """Ricerca il prossimo carattere valido tra '.' e ',' .
        Args:
            match: Valore corrispondente al tasso recuperato in elenco_comuni.csv.
        Returns:
            str: Valore formattato adeguatamente per essere convertito a Decimal.    
    """
    char = match.group(0)
    return '.' if char  == ',' else '' 
def parse_brackets_range(text: str):
    """
    Estrazione dei limiti numerici sottoforma di stringa.    
    Args:
        text: Testo da cui estrarre i limiti.
    Returns:
        (Decimal, Decimal): Tuple contenente i nuovi limiti recuperati. Se non presenti, si ritorna (0.0, 0.0) per definire l'assenza di limiti (nel caso di aliquota unica).
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
def sanitize_values(value) -> Decimal:
    """
    Conversione dei valori a Decimal.
    
    Args:
        value: Valore da convertire a Decimal.
    Returns:
        Decimal: Valore convertito a Decimal.
    Todo:
        Gestione migliorata dei tipi.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if not isinstance(value, str):
        return Decimal(str(value))
    if not value or value == '0*':
        return Decimal('0')
    return Decimal(_SANITIZE_RE.sub(_format_decimals, value))