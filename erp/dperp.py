import logging
from time import time
import numpy as np
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    udf,
    hash,
    col,
    substring,
    monotonically_increasing_id,
    expr,
)
from pyspark.sql.types import StringType
from erp.matching import (
    calculate_confusion_matrix,
    resultToString,
    calculate_combined_similarity,
)
import pandas as pd
from graphframes import GraphFrame
from erp.utils import (
    FILENAME_DP_MATCHED_ENTITIES,
    FILENAME_DP_CLUSTERING,
    RESULTS_FOLDER,
    jaccard_similarity,
    save_result,
    trigram_similarity,
    DEFAULT_ER_CONFIGURATION,
)


def DP_ER_pipline(
    filename1,
    filename2,
    ERconfiguration,
    baseline=False,
    cluster=True,
    matched_output=FILENAME_DP_MATCHED_ENTITIES,
    cluster_output=FILENAME_DP_CLUSTERING,
):
    conf = SparkConf().setAppName("YourAppName").setMaster("local[*]")
    sc = SparkContext(conf=conf)
    sc.setCheckpointDir("inbox")

    spark = SparkSession.builder.appName("Entity Resolution").getOrCreate()
    # Read the datasets from two databases
    start_time = time()
    df1 = spark.read.option("delimiter", ",").option("header", True).csv(filename1)
    df2 = spark.read.option("delimiter", ",").option("header", True).csv(filename2)
    df1 = df1.withColumn("index", monotonically_increasing_id())
    df2 = df2.withColumn("index", monotonically_increasing_id() + df1.count())
    pairs = blocking(df1, df2, ERconfiguration["blocking_method"])
    matched_pairs = matching(
        pairs, ERconfiguration["threshold"], output=matched_output
    )
    end_time = time()
    matching_time = end_time - start_time
    if cluster:
        clustering(df1, df2, matched_pairs, filename=cluster_output)
    end_time = time()
    matched_pairs.show(2)

    if baseline:
        baseline_matches = create_baseline(df1, df2)
        return resultToString(
            DEFAULT_ER_CONFIGURATION,
            -1,
            -1,
            -1,
            baseline_matches,
            matched_df=matched_pairs,
            suffix="_dp",
        )

    out = {
        "dp rate": round(matched_pairs.count() / (df1.count() + df2.count()), 4),
        "dp execution time": round((end_time - start_time) / 60, 2),
        "dp execution time(matching+blocking)": round(matching_time / 60, 2),
    }
    spark.stop()
    return out


def isNoneOrEmpty(str):
    return (str == None) or (str == "")


def calculate_combined_similarity_dp(
    title1, title2, author_names_df1, author_names_df2
):
    title_set1 = set(title1.split())
    title_set2 = set(title2.split())
    jaccard_similarity_title = jaccard_similarity(title_set1, title_set2)

    if isNoneOrEmpty(author_names_df1) or isNoneOrEmpty(author_names_df2):
        combined_similarity = jaccard_similarity_title
    else:
        trigram_similarity_author = trigram_similarity(
            author_names_df1, author_names_df2
        )
        combined_similarity = (
            0.7 * jaccard_similarity_title + 0.3 * trigram_similarity_author
        )
    return combined_similarity


process_udf = udf(calculate_combined_similarity_dp, StringType())


def blocking(df1, df2, blocking_method):
    blocking_function = globals()[f"create_{blocking_method}Blocking"]
    return blocking_function(df1, df2)


def create_cross_product_pyspark(df1, df2):
    bucket_df1 = df1.alias("df_copy")
    bucket_df2 = df2.alias("df_copy")
    # Rename columns for df1
    df1_columns = [col(col_name).alias(col_name + "_df1") for col_name in df1.columns]
    bucket_df1 = bucket_df1.select(df1_columns)

    # Rename columns for df2
    df2_columns = [col(col_name).alias(col_name + "_df2") for col_name in df2.columns]
    bucket_df2 = bucket_df2.select(df2_columns)
    pairs = bucket_df1.crossJoin(bucket_df2)
    return pairs


def create_FirstLetterTitleBlocking(df1, df2):
    df1 = df1.withColumn("bucket", substring(col("paper title"), 1, 1))
    df2 = df2.withColumn("bucket", substring(col("paper title"), 1, 1))
    pairs = create_cross_product_pyspark(df1, df2)
    pairs = pairs.filter(pairs.bucket_df1 == pairs.bucket_df2)
    return pairs


def create_FirstOrLastLetterTitleBlocking(df1, df2):
    df1 = df1.withColumn("bucket1", substring(col("paper title"), 1, 1))
    df1 = df1.withColumn("bucket2", substring(col("paper title"), -1, 1))
    df2 = df2.withColumn("bucket1", substring(col("paper title"), 1, 1))
    df2 = df2.withColumn("bucket2", substring(col("paper title"), -1, 1))
    pairs = create_cross_product_pyspark(df1, df2)
    pairs.show(2)
    pairs = pairs.filter(
        (pairs.bucket1_df1 == pairs.bucket1_df2)
        | (pairs.bucket2_df1 == pairs.bucket2_df2)
    )
    return pairs


# Assuming similarity_udf is defined elsewhere in your code
def matching(
    pairs,
    threshold=DEFAULT_ER_CONFIGURATION["threshold"],
    output=FILENAME_DP_MATCHED_ENTITIES,
):
    pairs = pairs.withColumn(
        "similarity_score",
        process_udf(
            col("paper title_df1"),
            col("paper title_df2"),
            col("author names_df1"),
            col("author names_df2"),
        ),
    )
    pairs = pairs.filter(pairs.similarity_score > threshold)
    save_result(pairs.toPandas(), output)

    return pairs


def create_baseline(df1, df2, threshold=DEFAULT_ER_CONFIGURATION["threshold"]):
    t_df1 = df1.select(
        [col(col_name).alias(col_name + "_df1") for col_name in df1.columns]
    )
    t_df2 = df2.select(
        [col(col_name).alias(col_name + "_df2") for col_name in df2.columns]
    )

    baseline_pairs = (
        t_df1.crossJoin(t_df2)
        .withColumn(
            "similarity_score",
            process_udf(
                col("paper title_df1"),
                col("paper title_df2"),
                col("author names_df1"),
                col("author names_df2"),
            ),
        )
        .filter(col("similarity_score") > threshold)
    )

    return baseline_pairs


def calculate_confusion_score(
    matched_df,
    baseline_matches,
    filename_matched=FILENAME_DP_MATCHED_ENTITIES,
    filename_baseline="DP_baseline_matches.csv",
):
    matched_df_pd = matched_df.toPandas()
    matched_df_pd["ID"] = matched_df_pd["paper ID_df1"] + matched_df_pd["paper ID_df2"]

    # Write matched pairs to CSV file
    save_result(matched_df_pd, filename_matched)
    baseline_matches_pd = baseline_matches.toPandas()
    baseline_matches_pd["ID"] = (
        baseline_matches_pd["paper ID_df1"] + baseline_matches_pd["paper ID_df2"]
    )
    save_result(baseline_matches_pd, filename_baseline)

    baseline_matches_pd = pd.read_csv(RESULTS_FOLDER + filename_baseline, sep=",")
    matched_pairs_pd = pd.read_csv(RESULTS_FOLDER + filename_matched, sep=",")

    tp, fn, fp, precision, recall, f1 = calculate_confusion_matrix(
        baseline_matches_pd, matched_pairs_pd
    )

    logging.info("Precision:", precision)
    logging.info("Recall:", recall)
    logging.info("F1-score:", f1)


def clustering(df1, df2, matched_df, filename=FILENAME_DP_CLUSTERING):
    df = df1.union(df2)
    vertices = df.withColumnRenamed("index", "id")
    vertices = vertices.select("id")
    # Create edges DataFrame
    edges = matched_df.select("index_df1", "index_df2")
    edges = edges.withColumnRenamed("index_df1", "src")
    edges = edges.withColumnRenamed("index_df2", "dst")

    # Create a GraphFrame
    graph = GraphFrame(vertices, edges)
    # graph = GraphFrame(
    #     vertices, edges.union(edges.selectExpr("dst as src", "src as dst"))
    # )

    # Find connected components
    connected_components = graph.connectedComponents()
    # logging.info(connected_components.count(), vertices.count(), edges.count())

    # Select the first vertex in every connected component
    first_vertices_df = connected_components.groupBy("component").agg({"id": "max"})

    # Rename the column to "first_vertex"
    first_vertices_df = first_vertices_df.withColumnRenamed("max(id)", "id")

    # Construct the DataFrame
    first_vertices_df = first_vertices_df.orderBy("component")
    save_result(first_vertices_df.toPandas(), filename)
    logging.info("finish clustering")
