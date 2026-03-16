from product_builder_jhr.logger import setup_logging
import logging.config
from product_builder_jhr.pages.main_page import show_main_page
from product_builder_jhr.services.tax import calculate_net_from_ral
from decimal import Decimal
setup_logging()
logger = logging.getLogger(__name__)

def main():
    show_main_page()
if __name__ == '__main__':
    main()