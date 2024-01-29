## Entity Resolution of Publication Data

### :books: Table of Contents

* [Abstract](#Abstract)
* [Quick Overview and User Instructions](#Quick-Overview-and-User-Instruction)
* [Data Acquisition and Preparation (Part 1)](#data-acquisition-and-preparation-part-1)
* [Entity Resolution Pipeline (Part 2)](#entity-resolution-pipeline-part-2)
* [Data Parallel Entity Resolution Pipeline (Part 3)](#data-parallel-entity-resolution-pipeline-part-3)

### :test_tube: Abstract

in this project we were ex

**Motivation:** Our pipeline compares two datasets to group together related papers based on information like paper ID, title, author names, and publication venue. This process ensures we have a clean and accurate dataset, making it easier to study scholarly publications effectively.

### Quick Overview and User Instruction

<details>
<summary>
Click here to expand!
</summary>

</summary>

### Installation

```shell
cd path-to-this-project
pip install -e .
```

### Sample to Run Exercise

[part1/2](./sample.py)

```python
from LocalERP import part1, part2
part1() # cleaned data stored in "data"
part2() # results of all methods stored in "method_results.csv"
```

for part3

```shell
python -u PySpark/DPREP.py
python -u PySpark/DPvsLocal.py
```

### Quick Introduction

- part1 : `LocalERP.preparing.prepare_data("path_to_txt_file")`
- part2 :
  - Blocking: `LocalERP.blocking(df1,df2,blocking_method)`
    - Parameters:
      - df1,df2 (pandas.DataFrame) : input databases
      - blocking_method(str) : {"Year", "TwoYear", "numAuthors", "FirstLetter"}
  - Matching: `LocalERP.matching(blocking_df,similarity_threshold, matching_method)`
    - Parameters:
      - blocking_df(pandas.DataFrame)
      - similarity_threshold (float from 0.0 to 1.0)
      - matching_method (String) : {"Jaccard", "Combined"}
  - Clustering: `LocalERP.run_clustering(matched_entities, df1, df2, clustering_method)`
    - Parameters:
      - matched_entities(pandas.DataFrame)
      - df1,df2 (pandas.DataFrame) : input databases
      - clustering_method (String) :{'basic'}
  - ER_pipline : `LocalERP.ER_pipline(df1,df2,ERconfiguration)`
    - Parameters:
      - df1,df2 (pandas.DataFrame) : input databases
      - ERconfiguration : sample`{ "matching_method": "Jaccard", "blocking_method": "Year","clustering_method":"basic", "threshold": 0.7, "output_filename": "results/clustering_results.csv",}`
- part 3 :

## Added by Nevo:


---

## Quick Project Overview

The project involves implementing an Entity Resolution Pipelining on citation networks from ACM and DBLP datasets.

### Data Source

The project starts with two large dataset text files you need to download:

- [DBLP-Citation-network V8]
- [ACM-Citation-network V8]

(Can be found [here](https://www.aminer.org/citation))

Below is the structure of the project:

- 📁 **project**
  - 📁 **LocalERP**: Contains Python scripts for the entity resolution pipeline.
    - 📄 `__init__.py`
    - 📄 `clustering.py`
    - 📄 `main.py`
    - 📄 `matching.py`
    - 📄 `preparing.py`
    - 📄 `testMatching.py`
    - 📄 `utils.py`
  - 📁 **PySpark**: Utilizes Apache Spark for comparison.
    - 📄 `DPREP.py`
  - 📁 **data**: Stores datasets and instruction files.
    - 📄 `DIA_2023_Exercise.pdf`
    - 📄 `citation-acm-v8_1995_2004.csv`
    - 📄 `dblp_1995_2004.csv`
    - 📄 `test.txt`
    - 📄 `test_1995_2004.csv`
  - 📄 `.gitignore`
  - 📄 `requirements.txt`
  - 📄 `setup.txt`
  - 📄 `README.md`

## LocalERP Folder

The LocalERP folder contains scripts for the entity resolution pipeline with specific configurations:

- **Preparing Data**: Run `preparing.prepare_data("path_to_txt_file")` for both text files. This will clean and extract the relevant data (1995-2004 citations by "SIGMOD" or "VLDB" venues). The resulting csv files will show in `data` folder.
- **Running Pipeline**: Execute `main.py` with ER configurations.
- **Configuration Options**:
  - `blocking_method`(String): Methods to reduce execution time {"Year", "TwoYear", "numAuthors", "FirstLetter"}.
  - `matching_method`(String): Algorithms for entity matching {"Jaccard", "Combined"}.
  - `clustering_method`(String): Altogirthm for clustering {"basic"}.
  - `threshold`(float): A value between 0.0-1.0 for the matching similarity threshold.
  - `output_filename`(String): path and file name of results to be saved.

**Selected Configuration**:

ERconfiguration: 

```
{"matching_method": "Combined",
 "blocking_method": "FirstLetter",
 "clustering_method":"basic", 
 "threshold": 0.5, 
 "output_filename": "results/clustering_results.csv"}
```

**Results**:

- The steps above will produce the results. They are saved according to your `output_filename` configuration. In our ERconfiguration shown above, it will be saved as `clustering_results.csv` within the `results` folder.

## PySpark Folder

The PySpark folder contains `DPREP.py` to compare our ER results with the Apache Spark framework.

## Data Folder

The data folder includes the prepared and cleaned datasets and additional samples:

- `citation-acm-v8_1995_2004.csv`: ACM citation network dataset.
- `dblp_1995_2004.csv`: DBLP citation network dataset.
- `DIA_2023_Exercise.pdf`: Project instruction file.



**Note**: Check `requirements.txt` for compatibility before running the code.

</details>

</details>

---

### Data Acquisition and Preparation (Part 1)

In this section, we acquire datasets related to research publications. These
datasets, available in text format, can be reached by
[clicking here](https://www.aminer.org/citation).

As a prerequisite for Entity Resolution and Model Training, we have
generated a dataset containing the following attributes:


> - Paper ID, paper title, author names, publication venue, year of publication
> 
> - Publications published between 1995 and 2004
> 
> - Publications from VLDB and SIGMOD venues

We utilized Pandas DataFrame, to convert the datasets from TXT to CSV. Our code
iterates through the text file, extracting entries separated by double newlines
and filtering based on the specified criteria. The resulting cleaned dataframes
are exported to the local `data` folder.

> The code for this section can be found in the file named `preparing.py` under 
> the function called `prepare_data`. Additionally, the resulting CSV files are
> available in the local `data` folder with the suffix `__1995_2004.csv`.

### Entity Resolution Pipeline (Part 2)

We aim to apply an entity resolution pipeline to the aforementioned datasets,
following the scheme depicted below:

![Entity Resolution Pipeline](https://i.ibb.co/bNBH9Xc/Screenshot-2024-01-29-at-15-15-09.png)

_Image Source: Prof. Matthias Boehm, Data Integration and Large-Scale Analysis Course, TU Berlin._

## Prepare Data

Continuing from the previous section, we employ various data cleaning techniques.
It converts all characters to lowercase, ensures uniformity, and eliminates
special characters, retaining only alphanumeric characters, spaces, and commas.
This process standardizes and cleans the textual data for easier comparison
and analysis.

> The code for this part is available in the file named `preparing.py` under
> the function called `prepare_data`.

## Blocking

Blocking is employed to reduce the number of comparisons by using effective
partitioning strategies. In each 'bucket', we run the comparisons
(see section below). Our blocking is achieved through partitioning based on attributes:

1. **Year :** Articles that were published in the same year would be in the same bucket.

2. **Two Year :** Articles that were published in the same year or in the adjacent year would be in the same bucket.

3. **Num Authors :** Articles with a similar number of authors (up to 2 difference) would be in the same bucket.

4. **First Letter :** Articles with the same first letter of title would be in the same bucket.

> The code for blocking is in the file named `matching.py`, with functions
> named `blocking_x`, where x is the respective blocking method.

## Matching

Before discussing comparison methods, some terms related to our pipeline are
introduced:

- Baseline - We establish a baseline by comparing every pair between datasets, given a certain
similarity function applied. This is our 'ground truth'.
- Prediction - Our model prediction is generated by comparing each pair within a bucket, given the
same similarity function applied to the respective baseline.

**Jaccard -** The Jaccard similarity function is employed to measure the
extent to which two sets share common elements. It does so by calculating
the ratio of the shared elements to the total elements in both sets.
Thresholds of 0.5 and 0.7 are used in the comparison of the 'paper title'
attribute.

**Combined -** This function calculates a combined similarity score
between two papers based on their titles and author names. It utilizes
Jaccard similarity for title comparison and, if available, trigram
similarity for author name comparison. The final combined similarity
score is a weighted sum of title and author name similarities, with
70% weight assigned to the title and 30% to the author names. If author
names are missing for either paper, the function defaults to using
only the Jaccard similarity of titles.

For the blocking methods mentioned above:

**Jaccard** similarity function with **Year** partitioning identifies matching
articles with similar titles published in the same year.

**Jaccard** and **Two-year** partitioning identifies matching articles
with similar titles published in the same year or in the adjacent year.

**Jaccard** and **Num Authors** partitioning identifies matching articles
with similar titles and a similar number of authors.

**Jaccard** and **First Letter** partitioning identifies matching articles
with similar titles and the same first letter of the paper title.

Likewise, the **Combined** similarity will yield results for the
different blocking methods, with only difference being that it takes
into account the number of authors in the comparison.

> The code for this part is available in the file named `matching.py`, with
functions named `calculate_x`, where x is the respective similarity method.
CSV files for each similarity function and blocking method will be exported
> to a local `results` folder.


Testing different combinations yields the results shown below:

![Matching Results](https://i.ibb.co/yd5DPGq/Screenshot-2024-01-29-at-15-09-24.png)

## Clustering

In the final part of the pipeline, we chose to cluster the matched entities
based on the combination of the **'First Letter'** blocking and the **Combined**
similarity function, for two main reasons:

1. The Combined similarity function has proven to yield more reliable results
for matched entities upon close inspection of the data.
2. First Letter has seemed to outperform all the other methods, both in 
execution time reduction and in other measures, such as Precision, Recall
and F1 Score.

We use the Numpy package to create a graph, organizing related items
into clusters of similar entities in our clustering process
(clustering_basic). Each item is represented as a point in the graph.
Connections between similar items, as identified in our matching output,
are drawn in the graph. We then employ depth-first search (DFS) to
traverse these connections, updating values as we explore and
contributing to the organization of clusters in the final results.

The code for clustering is available in the file named `clustering.py`,
and the resulting CSV file is located in the `results` folder under
the name `clustering_results`.

## Data Parallel Entity Resolution Pipeline (Part 3)

kakii
