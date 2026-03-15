from pathlib import Path
import yaml
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — single source of truth for shared literals
# ---------------------------------------------------------------------------

DEFAULT_SEPARATOR = ";"
DEFAULT_ENCODING_IN = "latin-1"
DEFAULT_ENCODING_OUT = "utf-8"

# Column name constants to avoid magic strings across the codebase
COL_PROVINCE = "PR"
COL_CAR_CODE = "Sigla automobilistica"
COL_REGION_NAME = "Denominazione Regione"

# Special-case region overrides applied after the province merge
PROVINCE_REGION_OVERRIDES = {
    "TN": "TRENTO",
    "BZ": "BOLZANO",
}

REGION_NAME_OVERRIDES = {
    "VALLE D'AOSTA/VALLÉE D'AOSTE":"VALLE D'AOSTA"
}

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

PACKAGE_DIR = Path(__file__).absolute().parent.parent

def get_project_root() -> Path:
    """Return the absolute path to the project root (four levels above this file)."""
    return PACKAGE_DIR.parent.parent


def get_config_path(config_filename: str) -> Path:
    """Build the full path to a config file inside the package."""
    return PACKAGE_DIR / "config" / config_filename


def get_resources_path(filename: str) -> Path:
    """Build the full path to a file under the project-level resources/ folder."""
    return get_project_root() / "resources" / filename


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_yaml_config(config: str) -> dict:
    """
    Load and return a YAML config file by name.

    Args:
        config: Filename relative to src/config/ (e.g. 'settings.yaml').

    Returns:
        Parsed YAML content as a dict.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file cannot be parsed.
    """
    config_path = get_config_path(config)
    logger.debug("Loading YAML config from: %s", config_path)

    try:
        with open(config_path, "r") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        logger.info("Config '%s' loaded successfully.", config)
        return data
    except FileNotFoundError:
        logger.error("Config file not found: %s", config_path)
        raise
    except yaml.YAMLError as e:
        logger.error("Failed to parse config '%s': %s", config, e)
        raise


# ---------------------------------------------------------------------------
# CSV I/O helpers
# ---------------------------------------------------------------------------

def read_csv(
    file: str | Path,
    cols: list[str],
    index: str | None = None,
    encoding: str = DEFAULT_ENCODING_OUT,
    sep: str = DEFAULT_SEPARATOR,
) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame, optionally setting an index column.

    Args:
        file:     Path to the CSV file.
        cols:     List of column names to load.
        index:    Column name to use as the DataFrame index (optional).
        encoding: File encoding (default utf-8).
        sep:      Column separator (default ';').

    Returns:
        Loaded DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If any requested column is missing.
    """
    file = Path(file)
    logger.debug("Reading CSV '%s' — cols=%s, index=%s", file, cols, index)

    try:
        df = pd.read_csv(file, sep=sep, usecols=cols, encoding=encoding)
    except FileNotFoundError:
        logger.error("CSV file not found: %s", file)
        raise
    except ValueError as e:
        logger.error("Column error reading '%s': %s", file, e)
        raise

    if index:
        if index not in df.columns:
            raise ValueError(f"Index column '{index}' not found in {file}")
        df.set_index(index, inplace=True)

    logger.info("Loaded %d rows from '%s'.", len(df), file)
    return df


def write_csv(
    df: pd.DataFrame,
    output_path: str | Path,
    sep: str = DEFAULT_SEPARATOR,
    encoding: str = DEFAULT_ENCODING_OUT,
) -> None:
    """
    Write a DataFrame to a CSV file.

    Args:
        df:          DataFrame to save.
        output_path: Destination file path.
        sep:         Column separator (default ';').
        encoding:    File encoding (default utf-8).
    """
    output_path = Path(output_path)
    logger.debug("Writing CSV to '%s'.", output_path)

    try:
        df.to_csv(output_path, sep=sep, index=False, encoding=encoding)
        logger.info("Saved %d rows to '%s'.", len(df), output_path)
    except OSError as e:
        logger.error("Failed to write CSV to '%s': %s", output_path, e)
        raise


# ---------------------------------------------------------------------------
# Data cleaning helpers
# ---------------------------------------------------------------------------

def clean_region_name(name: str) -> str | float:
    """
    Normalise a region name: uppercase, strip whitespace, remove 'REGIONE ' prefix.

    Returns the original value unchanged if it is NaN.
    """
    if pd.isna(name):
        return name

    name = str(name).upper().strip()
    if name.startswith("REGIONE "):
        name = name[len("REGIONE "):]
    return name


def clean_column(
    df: pd.DataFrame,
    col: str,
    pattern: str,
    replacement: str = "",
    case: bool = False,
) -> pd.DataFrame:
    """
    Strip a regex pattern from a string column, then uppercase and strip whitespace.

    Args:
        df:          Source DataFrame (not mutated).
        col:         Column to clean.
        pattern:     Regex pattern to remove.
        replacement: Replacement string (default '').
        case:        Case-sensitive match (default False).

    Returns:
        A copy of df with the column cleaned.
    """
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in DataFrame.")

    df = df.copy()
    df[col] = (
        df[col]
        .str.replace(pat=pattern, repl=replacement, case=case, regex=True)
        .str.upper()
        .str.strip()
    )
    logger.debug("Cleaned column '%s' with pattern '%s'.", col, pattern)
    return df


def normalize_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Uppercase and strip whitespace for each column in cols.

    Args:
        df:   Source DataFrame (not mutated).
        cols: Columns to normalise.

    Returns:
        A copy of df with the specified columns normalised.
    """
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Columns not found in DataFrame: {missing}")

    df = df.copy()
    for col in cols:
        df[col] = df[col].str.upper().str.strip()
    logger.debug("Normalised columns: %s", cols)
    return df

def remove_char_from_columns(df: pd.DataFrame, cols: list[str], char: str) -> pd.DataFrame:
    """
    Uppercase and strip whitespace for each column in cols.

    Args:
        df:   Source DataFrame (not mutated).
        cols: Columns to normalise.

    Returns:
        A copy of df with the specified columns normalised.
    """
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Columns not found in DataFrame: {missing}")

    df = df.copy()
    
    for col in cols:
        df[col] = (
            df[col]
            .str.replace(char, " ", regex=False)
            .str.upper()
            .str.strip()
    )
    logger.debug("Normalised columns: %s", cols)
    return df

# ---------------------------------------------------------------------------
# File-level cleaning utilities
# (thin wrappers: load → clean/normalise → save)
# ---------------------------------------------------------------------------

def clean_csv_file(
    filename: str,
    col: str,
    pattern: str,
    output_path: str | Path,
    input_encoding: str = DEFAULT_ENCODING_IN,
) -> None:
    """
    Load a CSV from resources/, clean one column, and save the result.

    Args:
        filename:       Source filename inside resources/.
        col:            Column to clean.
        pattern:        Regex pattern to remove from the column.
        output_path:    Destination file path for the cleaned CSV.
        input_encoding: Encoding of the source file (default latin-1).
    """
    src = get_resources_path(filename)
    logger.info("Cleaning column '%s' in '%s'.", col, src)

    df = pd.read_csv(src, sep=DEFAULT_SEPARATOR, encoding=input_encoding)
    df = clean_column(df, col, pattern)
    return df
    


def normalize_csv_file(
    filename: str,
    cols: list[str],
    output_path: str | Path,
    input_encoding: str = DEFAULT_ENCODING_IN,
) -> None:
    """
    Load a CSV from resources/, normalise the specified columns, and save.

    Args:
        filename:       Source filename inside resources/.
        cols:           Columns to normalise.
        output_path:    Destination file path.
        input_encoding: Encoding of the source file (default latin-1).
    """
    src = get_resources_path(filename)
    logger.info("Normalising columns %s in '%s'.", cols, src)

    df = pd.read_csv(src, sep=DEFAULT_SEPARATOR, encoding=input_encoding)
    df = normalize_columns(df, cols)
    write_csv(df, output_path)


# ---------------------------------------------------------------------------
# Region merge
# ---------------------------------------------------------------------------

def import_region_name(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    output_path: str | Path,
) -> pd.DataFrame:
    """
    Merge region names from right_df into left_df on province code, apply
    special-case overrides, and save the result to a CSV.

    Args:
        left_df:     DataFrame containing a province-code column (COL_PROVINCE).
        right_df:    Reference DataFrame with car-code and region-name columns.
        output_path: Destination file path for the merged CSV.

    Returns:
        The merged DataFrame.

    Raises:
        KeyError: If required join columns are absent.
    """
    for col, df_name in [(COL_PROVINCE, "left_df"), (COL_CAR_CODE, "right_df"), (COL_REGION_NAME, "right_df")]:
        source = left_df if df_name == "left_df" else right_df
        if col not in source.columns:
            raise KeyError(f"Required column '{col}' missing from {df_name}.")

    logger.info("Merging region names into left_df (%d rows).", len(left_df))

    merged_df = pd.merge(
        left_df,
        right_df,
        left_on=COL_PROVINCE,
        right_on=COL_CAR_CODE,
        how="left",
    )

    # Apply special-case province → region overrides
    for province_code, region_name in PROVINCE_REGION_OVERRIDES.items():
        mask = merged_df[COL_CAR_CODE] == province_code
        merged_df.loc[mask, COL_REGION_NAME] = region_name
        logger.debug("Override applied: %s → %s", province_code, region_name)
    merged_df= remove_char_from_columns(merged_df, [COL_REGION_NAME], '-')
    for current_region_name, new_region_name in REGION_NAME_OVERRIDES.items():
        mask = merged_df[COL_REGION_NAME] == current_region_name
        merged_df.loc[mask, COL_REGION_NAME] = new_region_name
        logger.debug("Override applied: %s → %s", current_region_name, new_region_name)
    logger.info("Region merge complete — %d rows saved to '%s'.", len(merged_df), output_path)

    return merged_df
    write_csv(merged_df, output_path)
    