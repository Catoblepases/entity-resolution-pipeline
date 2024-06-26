###################################################################################################
# Purpose: This script performs as a sample to reproduce our results
# Please install the necessary packages before using this script
# spark == 3.5.0
# scala == 2.12.x
# graphframes == 0.8.3-spark3.5-s_2.12
# ```shell
# cd path-to-this-project
# pip install -e .
# pyspark --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12
# ```
###################################################################################################
import logging
from erp import part1, part2, part3, ER_pipeline
from erp.utils import (
    DATABASES_LOCATIONS,
    DEFAULT_ER_CONFIGURATION,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
# part1()  # cleaned data stored in "data" as "data/citation-acm-v8_1995_2004.csv" and "data/dblp_1995_2004.csv"
# part2()  # results of all methods stored in "results/method_results.csv"
part3()  # scability test results stored in "results/scability_results.csv" and "results/scability.png"
ER_pipeline(
    DATABASES_LOCATIONS[0], DATABASES_LOCATIONS[1], DEFAULT_ER_CONFIGURATION
)  # test the entire local pipeline including clustering
ER_pipeline(
    DATABASES_LOCATIONS[0], DATABASES_LOCATIONS[1], DEFAULT_ER_CONFIGURATION, isdp=True
)  # test the entire parallel pipeline including clustering
