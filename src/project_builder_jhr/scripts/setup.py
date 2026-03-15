"""
setup.py — Run once at application startup to ensure all cleaned CSV files
exist under resources/cleaned/. If any are missing, they are generated from
the raw sources in resources/.
"""

import logging
from pathlib import Path
from src.project_builder_jhr.helpers.utils import get_project_root
from src.project_builder_jhr.helpers.utils import (
    clean_csv_file,
    normalize_csv_file,
    import_region_name,
    read_csv,
    write_csv,
    normalize_columns,
    remove_char_from_columns
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RESOURCES_DIR = Path("resources")
CLEANED_DIR   = RESOURCES_DIR / "cleaned"
LOGS_DIR   = Path(get_project_root()) / "logs"
# Raw sources
RAW_ADDREG         = "addreg2026.csv"
RAW_COMUNI         = "Elenco-comuni-italiani.csv"
RAW_ADD_COMUNALE   = "Add_comunale_irpef2025.csv"

# Cleaned outputs
OUT_ADDREG  = CLEANED_DIR / "addizionali_regionali.csv"
OUT_COMUNI  = CLEANED_DIR / "elenco_comuni.csv"

# Regex

REGEX_ADDIZIONALI_REGIONALI = r'(REGIONE |PROVINCIA AUTONOMA DI )+'
# ---------------------------------------------------------------------------
# Per-file setup routines
# ---------------------------------------------------------------------------

def setup_addizionali_regionali() -> None:
    """Clean addreg2026.csv → cleaned/addizionali_regionali.csv."""
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
    Merge Elenco-comuni-italiani.csv + Add_comunale_irpef2025.csv
    → cleaned/elenco_comuni.csv.
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
        #normalize_regions('Elenco-comuni-italiani.csv', ['Denominazione Regione', "Denominazione dell'Unità territoriale sovracomunale \n(valida a fini statistici)"], 'resources/elenco_comuni')
    #import_region_name(config_class.addizionali_comunali, 
    #config_class.comuni[['Sigla automobilistica', 'Denominazione Regione']].drop_duplicates(), 'resources/cleaned/elenco_comuni')
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

def run_setup() -> None:
    """
    Ensure resources/cleaned/ exists and all required cleaned files are present.
    Call this once before instantiating ConfigClass.
    """
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Starting setup — cleaned dir: '%s'", CLEANED_DIR)

    setup_addizionali_regionali()
    setup_elenco_comuni()

    logger.info("Setup complete. All required files are ready.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_setup()