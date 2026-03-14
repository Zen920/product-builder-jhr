from root_logger import setup_logging
import logging.config
from src.services.tax import calculate_net_from_ral
setup_logging()
logger = logging.getLogger("app.py")
from src.pages.main_page import show_main_page
from setup import run_setup
if __name__ == '__main__':
    show_main_page()
