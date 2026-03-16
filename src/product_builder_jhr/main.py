from product_builder_jhr.logger import setup_logging
import logging.config
from product_builder_jhr.pages.main_page import show_main_page
from product_builder_jhr.services.tax import calculate_net_from_ral
import streamlit as st
setup_logging()
logger = logging.getLogger(__name__)
st.set_page_config(layout="wide")

def main():
    pg = st.navigation([st.Page(show_main_page, title="ProductBuilderJHR")], position="hidden")
    pg.run()
if __name__ == '__main__':
    main()