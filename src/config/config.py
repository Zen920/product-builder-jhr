from src.models.inps_model import Dati
from src.helpers.utils import load_yaml_config, read_csv
from setup import run_setup
class ConfigClass():
    def __init__(self, config):
        run_setup()
        self.yaml_file = load_yaml_config(config)
        self.dati = Dati(**self.yaml_file['yaml'])
        self.addizionali_comunali = read_csv("resources/cleaned/elenco_comuni.csv", None, None)
        self.addizionali_regionali = read_csv("resources/cleaned/addizionali_regionali.csv", None,  "REGIONE")
        #self.comuni = read_csv_panda("resources/elenco_comuni.csv", None, None, encoding='latin-1')

config_class = ConfigClass("inps_data.yaml")
