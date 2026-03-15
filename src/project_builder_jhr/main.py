from project_builder_jhr.logger import setup_logging
import logging.config
from project_builder_jhr.pages.main_page import show_main_page
from project_builder_jhr.services.tax import calculate_net_from_ral

setup_logging()
logger = logging.getLogger(__name__)

def main():
    #show_main_page()
    calculate_net_from_ral(35000, 14, "MILANO", "LOMBARDIA")
if __name__ == '__main__':
    
    main()