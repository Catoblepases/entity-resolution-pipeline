__title__ = "DIA"
__version__ = "0.0.0"

from .utils import DefaultERconfiguration, DATABASES_LOCATIONS, DATABSE_COLUMNS
from .main import *
from .matching import matching, blocking
from .clustering import clustering
import logging
