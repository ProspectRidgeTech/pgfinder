"""Package initialisation"""
import logging
import yaml
from pkgutil import get_data
from pgfinder.pgio import read_yaml
from pgfinder.logs.logs import setup_logger, LOGGER_NAME
from pgfinder.utils import dict_to_decimal

LOGGER = setup_logger()
LOGGER = logging.getLogger(LOGGER_NAME)


PARAMETERS_FILE = "config/parameters.yaml"
PARAMETERS = get_data(__package__, PARAMETERS_FILE)
PARAMETERS = yaml.safe_load(PARAMETERS)
LOGGER.info(f"Loaded parameters from file : {PARAMETERS_FILE}")
PARAMETERS = dict_to_decimal(PARAMETERS)
LOGGER.info("All parameters converted to decimal")
MULTIMERS = PARAMETERS["multimer"]
MOD_TYPE = PARAMETERS["mod_type"]
MASS_TO_CLEAN = PARAMETERS["mass_to_clean"]

from . import _version
__version__ = _version.get_versions()['version']
