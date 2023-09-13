import random

import numpy as np
import pandas as pd


def generate_dummy_data(n=50):
    # Sample data
    age = np.random.randint(18, 65, n)  # age of the customers
    cities = ["Tbilisi", "Kutaisi", "Batumi"]
    city = [random.choice(cities) for _ in range(n)]  # city of residence

    sex = [random.choice(["M", "F"]) for _ in range(n)]
    arpu = np.random.uniform(150, 600, n)  # Average Revenue Per User
    data_consumption = np.random.uniform(1, 100, n)  # data consumption in GB
    data_consumption_stratified = np.random.uniform(
        1,
        100,
        n,
    )  # voice consumption in Minutes

    # Creation of DataFrame
    telecom_customer_data = pd.DataFrame(
        {
            "age": age,
            "city": city,
            "sex": sex,
            "arpu": arpu,
            "data_consumption": data_consumption,
            "data_consumption_stratified": data_consumption_stratified,
        },
    )

    # Print the DataFrame
    return telecom_customer_data


def proportional_stratified_sample(
    df,
    stratify_cols,
    n_splits=3,
    num_variables_default_buckets=10,
):
    """Split the sample in the input df in n different groups, stratified on
        some given numeric or categorical variables


    Args:
        df (pd.DataFrame): input dataframe with the sample you want to
            split into groups
        stratify_cols (list): a list of columns you want to stratify the split on
        n_splits (int, optional): number of output groups. Defaults to 3.
        num_variables_default_buckets (int, optional): number of buckets to
            split the numerical variables in. Defaults to 10.


    Returns:
        _type_: _description_
    """
    # Check that the input df doesnt already have a "group" column
    assert "group" not in df.columns, "input df already has a 'group' column."
    # For each column, we convert them to a categorical type
    transformed_stratify_cols = []
    for col in stratify_cols:
        if df[col].dtype.kind in "biufc":
            df[col + "_stratify"] = pd.qcut(df[col], q=num_variables_default_buckets)
            df[col + "_stratify"] = df[col + "_stratify"].astype(str)
        else:
            df[col + "_stratify"] = df[col].astype(str)
        transformed_stratify_cols.append(col + "_stratify")

    # Bucket size check
    # make sure each strata has at least N customers
    # Where N is the number of groups
    bucket_counts = df[transformed_stratify_cols].value_counts()
    assert bucket_counts.min() >= n_splits, (
        f"At least one strata has too few datapoints ({bucket_counts.min()})"
        f" to be split into {n_splits} groups."
        f"\nTry reducing the number of stratify variables (currently {len(stratify_cols)}), "
        "or reduce the number of buckets for each numerical variable"
        f" (currently {num_variables_default_buckets})"
    )

    # split into stratified groups
    df = df.reset_index(drop=True)
    df["group"] = None

    for i in range(n_splits):
        df_ungroupped = df[df["group"].isna()]
        group_i_indices = (
            df_ungroupped.groupby(transformed_stratify_cols, group_keys=False)
            .apply(lambda x: x.sample(frac=1 / (n_splits - i)))
            .index
        )
        df.loc[group_i_indices, "group"] = i

    assert not df["group"].isna().any(), "Some datapoints were not assigned a group"

    # drop _stratify columns
    df = df.drop(columns=transformed_stratify_cols)
    return df


df = generate_dummy_data(n=50000)

df_w_groups = proportional_stratified_sample(
    df,
    stratify_cols=["data_consumption_stratified"],
    n_splits=10,
    num_variables_default_buckets=50,
)

d_res = df_w_groups.groupby(by="group").agg(
    {"data_consumption_stratified": "mean", "data_consumption": "mean"},
)

print(d_res)
print("std")
print(d_res.std())
