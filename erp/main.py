import logging
import random
from time import time
import numpy as np
import pandas as pd
from erp.dperp import DP_ER_pipline
from erp.matching import *
from erp.clustering import clustering_basic, run_clustering
from erp.preparing import prepare_data
from erp.utils import (
    FILENAME_LOCAL_MATCHED_ENTITIES,
    FILENAME_DP_MATCHED_ENTITIES,
    test_and_create_folder,
    DefaultERconfiguration,
    DATABSE_COLUMNS,
    DATABASES_LOCATIONS,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
import string
import matplotlib.pyplot as plt

ERconfiguration = {
    "matching_method": "Jaccard",
    "blocking_method": "Year",
    "threshold": 0.5,
    "clustering_method": "basic",
    "output_filename": "results/clustering_results.csv",
}


def ER_pipline(
    dfilename1,
    dfilename2,
    ERconfiguration,
    baseline=False,
    matched_output=FILENAME_LOCAL_MATCHED_ENTITIES,
    cluster=True,
):
    # import database
    df1 = pd.read_csv(dfilename1, sep=",", engine="python")
    df2 = pd.read_csv(dfilename2, sep=",", engine="python")

    df1["index"] = np.arange(len(df1))
    df2["index"] = np.arange(len(df2)) + len(df1)

    similarity_threshold = ERconfiguration["threshold"]
    start_time = time()
    result_df = blocking(df1, df2, ERconfiguration["blocking_method"])
    result_df = matching(
        result_df,
        similarity_threshold,
        ERconfiguration["matching_method"],
        outputfile=matched_output,
    )
    end_time = time()
    matching_time = end_time - start_time
    c_df = []
    if cluster:
        c_df = run_clustering(result_df, df1, df2, ERconfiguration["clustering_method"])
    end_time = time()

    if baseline:
        baseline_df = calculate_baseline(
            df1,
            df2,
            baseline_config={
                "method": ERconfiguration["matching_method"],
                "threshold": ERconfiguration["threshold"],
            },
        )

        return resultToString(
            ERconfiguration,
            -1,
            -1,
            -1,
            baseline_df,
            matched_df=result_df,
            suffix="_local",
        )
    return {
        "local rate": round(len(c_df) / (len(df1) + len(df2)), 4),
        "local excution time": round((end_time - start_time) / 60, 2),
        "local excution time(matching+blocking)": round(matching_time / 60, 2),
    }
    
def add_random_characters_to_string(str, number):
    characters = string.ascii_lowercase
    new_string = list(str)

    for _ in range(number):
        random_char = random.choice(characters)
        new_string[random.randint(0, len(str) - 1)] = random_char

    return "".join(new_string)


DATABASE_CHANGES_CHOICE = ["year", "author", "title"]


def databaseWithMinimalChanges(filename, option="title", num=3):
    """minimal modification to database

    Args:
        database (_type_): _description_
        option (str, optional): "year"|"author"|"title".
        num (int): number of changes
    """
    database = pd.read_csv(filename)
    if option == "author":
        database[DATABSE_COLUMNS[2]] = database.apply(
            lambda x: add_random_characters_to_string(str(x[DATABSE_COLUMNS[2]]), num),
            axis=1,
        )
    elif option == "title":
        database[DATABSE_COLUMNS[1]] = database.apply(
            lambda x: add_random_characters_to_string(str(x[DATABSE_COLUMNS[1]]), num),
            axis=1,
        )
    elif option == "year":
        database[DATABSE_COLUMNS[-1]] += random.randint(-int(num / 2), -int(num / 2))
    return database


def create_databaseWithChanges(L_filename, num=3, cnum=3):
    L_datanames = []
    for filename in L_filename:
        for i in range(num):
            option = DATABASE_CHANGES_CHOICE[i % len(DATABASE_CHANGES_CHOICE)]
            df = databaseWithMinimalChanges(filename, option, cnum)
            new_filename = filename[5:-4] + "_" + option[:4] + str(cnum) + ".csv"
            new_folder = filename[:-4]
            test_and_create_folder(new_folder)
            df.to_csv(new_folder + "/" + new_filename)
            L_datanames.append(new_folder + "/" + new_filename)
    return L_datanames


def plot_scability_figures(results):
    results["d1-d2"] = [str(i) for i in results["d1-d2"]]
    plt.figure(figsize=(10, 4), dpi=100)
    plt.title("resulting execution time")
    plt.bar(
        results["d1-d2"],
        results["dp excution time(matching+blocking)"],
        label="dp excution time",
        alpha=0.6,
    )
    plt.bar(
        results["d1-d2"],
        results["local excution time(matching+blocking)"],
        label="local excution time",
        alpha=0.6,
    )
    plt.xticks(fontsize=7)
    plt.legend(loc="upper right")
    plt.savefig("results/scability.png")


def part1():
    for data in ["data/citation-acm-v8.txt", "data/dblp.txt"]:
        prepare_data(data)


def part2(thresholds=[0.5, 0.7]):
    # import database
    df1 = pd.read_csv("data/citation-acm-v8_1995_2004.csv", sep=",", engine="python")
    df1["index"] = np.arange(len(df1))
    df2 = pd.read_csv("data/dblp_1995_2004.csv", sep=",", engine="python")
    df2["index"] = np.arange(len(df2)) + len(df1)
    # Run all blocking methods for each baseline and record results
    run_all_blocking_matching_methods(
        df1, df2, thresholds, MATCHING_METHODS, BLOCKING_METHODS
    )


def part3(ERconfiguration=DefaultERconfiguration, num_duplicates=3, num_changes=4):
    L_filenames = create_databaseWithChanges(
        DATABASES_LOCATIONS, num_duplicates, num_changes
    )
    D = [(d1, d2) for d1 in L_filenames[:3] for d2 in L_filenames[3:]]
    results = []

    for d1, d2 in D:
        result = ER_pipline(d1, d2, ERconfiguration, baseline=False, cluster=False)
        result["d1-d2"] = (d1[-9:-4], d2[-9:-4])
        result2 = DP_ER_pipline(
            d1, d2, threshold=ERconfiguration["threshold"], cluster=False
        )
        results.append({**result2, **result})
    results = pd.DataFrame(results)
    save_result(results, "scability_results.csv")
    plot_scability_figures(results)


def naive_DPvsLocal(fdp, flocal):
    DP_ER_pipline(DATABASES_LOCATIONS[0], DATABASES_LOCATIONS[1], cluster=False)
    ER_pipline(
        DATABASES_LOCATIONS[0],
        DATABASES_LOCATIONS[1],
        ERconfiguration=DefaultERconfiguration,
        cluster=False,
    )
    df_dp = pd.read_csv(fdp)
    df_local = pd.read_csv(flocal)
    tp, fn, fp, precision, recall, f1 = calculate_confusion_matrix(df_dp, df_local)

    # print the number of matched pairs in each DataFrame
    logging.info(f"Number of matched pairs in df_dp: {len(df_dp)}")
    logging.info(f"Number of matched pairs in df_local: {len(df_local)}")

    # print the results
    logging.info(f"Number of differences: {fn+fp}")
    logging.info(f"Number of shared elements: {tp}")
    logging.info(f"Number of elements in df_dp but not in df_local: {fn}")
    logging.info(f"Number of elements in df_local but not in df_dp: {fp}")
