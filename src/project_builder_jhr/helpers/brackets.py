import pandas as pd
from project_builder_jhr.helpers.parsers import sanitize_values, parse_brackets_range
from project_builder_jhr.models.inps_model import Bracket
import logging.config
from decimal import Decimal
logger = logging.getLogger("helpers.brackets")
def _create_brackets(ser):
    raw_brackets: list[str] = []
    raw_rates: list[Decimal] = []
    
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
def build_brackets(ser: pd.Series | pd.DataFrame, divide_rate_by: Decimal = 100.0) -> list[Bracket]:
    if isinstance(ser, pd.DataFrame):
        return [
            bracket
            for _, row in ser.iterrows()
            for bracket in build_brackets(row, divide_rate_by)
        ]
    raw_brackets, raw_rates = _create_brackets(ser)
    return [
        Bracket(low=low, high=high, rate=rate / divide_rate_by)
        for (low, high), rate in zip(map(parse_brackets_range, raw_brackets), raw_rates)
    ]    
def apply_brackets(brackets: list[Bracket], imponibile: Decimal) -> Decimal:
    if not brackets:
        logger.warning("No brackets found; returning 0.")
        return Decimal('0')

    discovered_esenzione = next(
        ((index, b.high) for index, b in enumerate(brackets) if b.rate == 0.0),
        None
    )
    if discovered_esenzione is not None:
        index, threshold = discovered_esenzione
        if imponibile <= threshold:
            logger.debug("Below esenzione=%.2f; returning 0.", threshold)
            return Decimal('0')
        brackets.pop(index)

    result = Decimal()
    remaining_imponibile = imponibile
    for b in brackets:
        addizionale, remaining_imponibile = b.calcola_nel_bracket(
            imponibile=imponibile,
            remaining_imponibile=remaining_imponibile,
        )
        result += addizionale
        if remaining_imponibile <= 0:
            break
    return result