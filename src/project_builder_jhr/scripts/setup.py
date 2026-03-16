"""
setup.py — Run once at application startup to ensure all cleaned CSV files
exist under resources/cleaned/. If any are missing, they are generated from
the raw sources in resources/.
"""

import logging
from pathlib import Path
from project_builder_jhr.helpers.utils import get_project_root
from project_builder_jhr.helpers.utils import (
    clean_csv_file,
    normalize_csv_file,
    import_region_name,
    read_csv,
    write_csv,
    normalize_columns,
    remove_char_from_columns
)

logger = logging.getLogger(__name__)

PACKAGE_DIR   = Path(__file__).parent.parent  # → site-packages/project_builder_jhr/
RESOURCES_DIR = PACKAGE_DIR / "data" / "raw"          # raw files inside the package
CLEANED_DIR   = Path.cwd() / "resources" / "cleaned"  # → user's working directory

RAW_ADDREG       = RESOURCES_DIR / "addreg2026.csv"
RAW_COMUNI       = RESOURCES_DIR / "Elenco-comuni-italiani.csv"
RAW_ADD_COMUNALE = RESOURCES_DIR / "Add_comunale_irpef2025.csv"
# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

LOGS_DIR   = Path(get_project_root()) / "logs"
# Raw sources

# Cleaned outputs
OUT_ADDREG  = CLEANED_DIR / "addizionali_regionali.csv"
OUT_COMUNI  = CLEANED_DIR / "elenco_comuni.csv"

# Regex

REGEX_ADDIZIONALI_REGIONALI = r'(REGIONE |PROVINCIA AUTONOMA DI )+'
# ---------------------------------------------------------------------------
# Per-file setup routines
# ---------------------------------------------------------------------------

def setup_addizionali_regionali() -> None:
    """Pulizia e normalizzazione del file addreg2026.csv.
    Returns:
        file: Creazione del nuovo file cleaned/addizionali_regionali.csv"""
    if OUT_ADDREG.exists():
        logger.info("'%s' already exists — skipping.", OUT_ADDREG)
        return

    logger.info("Generating '%s' …", OUT_ADDREG)
    df = clean_csv_file(
        filename=RAW_ADDREG,
        col="REGIONE",          # adjust to the actual column name if different
        pattern=REGEX_ADDIZIONALI_REGIONALI,     # adjust pattern to match your cleaning needs
        output_path=OUT_ADDREG,
    )
    df = remove_char_from_columns(df, ['REGIONE'], '-')
    write_csv(df, OUT_ADDREG)
    logger.info("'%s' created.", OUT_ADDREG)

def setup_elenco_comuni() -> None:
    """
    Unione dei file Elenco-comuni-italiani.csv + Add_comunale_irpef2025.csv
    Returns:
        file: cleaned/elenco_comuni.csv.
    """
    if OUT_COMUNI.exists():
        logger.info("'%s' already exists — skipping.", OUT_COMUNI)
        return

    logger.info("Generating '%s' …", OUT_COMUNI)

    comuni_src     = RESOURCES_DIR / RAW_COMUNI
    comunale_src   = RESOURCES_DIR / RAW_ADD_COMUNALE

    for path in (comuni_src, comunale_src):
        if not path.exists():
            raise FileNotFoundError(
                f"Raw source file not found: '{path}'. "
                "Cannot generate cleaned output."
            )

    comuni_df    = read_csv(comuni_src,   cols=None, encoding="latin-1")
    comunale_df  = read_csv(comunale_src, cols=None, encoding="latin-1")
    merged_df = import_region_name(
        left_df=comunale_df,
        right_df=comuni_df[['Sigla automobilistica', 'Denominazione Regione']].drop_duplicates(),
        output_path=OUT_COMUNI,
    )
    write_csv(merged_df, OUT_COMUNI)
    logger.info("'%s' created — %d rows.", OUT_COMUNI, len(merged_df))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Configura l'ambiente per la corretta esecuzione dell'applicazione.
    """
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Starting setup — cleaned dir: '%s'", CLEANED_DIR)

    setup_addizionali_regionali()
    setup_elenco_comuni()

    logger.info("Setup complete. All required files are ready.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()