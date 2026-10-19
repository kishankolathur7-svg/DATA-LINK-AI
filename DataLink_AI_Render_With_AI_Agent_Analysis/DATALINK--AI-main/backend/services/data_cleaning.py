import os
import pandas as pd


# ==========================================
# MISSING VALUE CLEANING
# ==========================================

def clean_missing_values(
    dataframe,
    strategy,
    custom_value=None
):
    """
    Handle missing values without modifying
    the original dataframe.

    Supported strategies:
    - mean
    - median
    - mode
    - custom
    - drop_rows
    """

    cleaned_dataframe = dataframe.copy()

    original_rows = len(cleaned_dataframe)

    original_missing = int(
        cleaned_dataframe.isna()
        .sum()
        .sum()
    )

    if strategy == "mean":

        numeric_columns = (
            cleaned_dataframe
            .select_dtypes(include="number")
            .columns
        )

        for column in numeric_columns:

            value = cleaned_dataframe[
                column
            ].mean()

            if pd.notna(value):

                cleaned_dataframe[column] = (
                    cleaned_dataframe[column]
                    .fillna(value)
                )

    elif strategy == "median":

        numeric_columns = (
            cleaned_dataframe
            .select_dtypes(include="number")
            .columns
        )

        for column in numeric_columns:

            value = cleaned_dataframe[
                column
            ].median()

            if pd.notna(value):

                cleaned_dataframe[column] = (
                    cleaned_dataframe[column]
                    .fillna(value)
                )

    elif strategy == "mode":

        for column in cleaned_dataframe.columns:

            mode_values = (
                cleaned_dataframe[column]
                .mode(dropna=True)
            )

            if not mode_values.empty:

                cleaned_dataframe[column] = (
                    cleaned_dataframe[column]
                    .fillna(mode_values.iloc[0])
                )

    elif strategy == "custom":

        if custom_value is None:

            raise ValueError(
                "Custom value is required"
            )

        cleaned_dataframe = (
            cleaned_dataframe
            .fillna(custom_value)
        )

    elif strategy == "drop_rows":

        cleaned_dataframe = (
            cleaned_dataframe
            .dropna()
            .reset_index(drop=True)
        )

    else:

        raise ValueError(
            "Invalid missing-value strategy"
        )

    final_rows = len(
        cleaned_dataframe
    )

    final_missing = int(
        cleaned_dataframe.isna()
        .sum()
        .sum()
    )

    return {
        "dataframe": cleaned_dataframe,

        "summary": {
            "strategy": strategy,
            "original_rows": original_rows,
            "final_rows": final_rows,
            "removed_rows": (
                original_rows - final_rows
            ),
            "original_missing": original_missing,
            "remaining_missing": final_missing,
            "fixed_missing": (
                original_missing - final_missing
            )
        }
    }


# ==========================================
# DUPLICATE CLEANING
# ==========================================

def clean_duplicate_rows(dataframe):
    """
    Remove duplicate rows from a copy
    of the original dataframe.

    The first occurrence of a row is kept.
    """

    cleaned_dataframe = dataframe.copy()

    original_rows = len(
        cleaned_dataframe
    )

    duplicate_rows = int(
        cleaned_dataframe
        .duplicated()
        .sum()
    )

    cleaned_dataframe = (
        cleaned_dataframe
        .drop_duplicates(
            keep="first"
        )
        .reset_index(drop=True)
    )

    final_rows = len(
        cleaned_dataframe
    )

    return {
        "dataframe": cleaned_dataframe,

        "summary": {
            "original_rows": original_rows,
            "final_rows": final_rows,
            "duplicates_removed": (
                duplicate_rows
            )
        }
    }


# ==========================================
# EMPTY COLUMN CLEANING
# ==========================================

def find_empty_columns(dataframe):
    """
    Find columns where every value is missing.

    A column is considered empty when 100%
    of its values are NaN/None/NaT.
    """

    empty_columns = []

    total_rows = len(
        dataframe
    )

    for column in dataframe.columns:

        missing_count = int(
            dataframe[column]
            .isna()
            .sum()
        )

        if total_rows == 0:

            is_empty = True

        else:

            is_empty = (
                missing_count == total_rows
            )

        if is_empty:

            empty_columns.append({
                "name": str(column),
                "missing": missing_count,
                "percentage": 100.0
            })

    return empty_columns


def clean_empty_columns(dataframe):
    """
    Remove columns where all values are missing.

    The original dataframe is never modified.
    """

    cleaned_dataframe = dataframe.copy()

    original_columns = len(
        cleaned_dataframe.columns
    )

    empty_columns = find_empty_columns(
        cleaned_dataframe
    )

    columns_to_remove = [
        item["name"]
        for item in empty_columns
    ]

    if columns_to_remove:

        cleaned_dataframe = (
            cleaned_dataframe
            .drop(
                columns=columns_to_remove
            )
        )

    final_columns = len(
        cleaned_dataframe.columns
    )

    return {
        "dataframe": cleaned_dataframe,

        "summary": {
            "original_columns": original_columns,
            "final_columns": final_columns,
            "empty_columns_found": len(
                empty_columns
            ),
            "columns_removed": len(
                columns_to_remove
            ),
            "removed_column_names": (
                columns_to_remove
            )
        }
    }


# ==========================================
# SAVE CLEANED DATASET
# ==========================================

def save_cleaned_dataset(
    dataframe,
    original_name,
    output_folder,
    suffix="cleaned"
):
    """
    Save a cleaned dataset as a new CSV file.

    The original uploaded file is never
    overwritten.
    """

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    base_name = os.path.splitext(
        original_name
    )[0]

    cleaned_name = (
        f"{base_name}_{suffix}.csv"
    )

    output_path = os.path.join(
        output_folder,
        cleaned_name
    )

    counter = 1

    while os.path.exists(
        output_path
    ):

        cleaned_name = (
            f"{base_name}_{suffix}_{counter}.csv"
        )

        output_path = os.path.join(
            output_folder,
            cleaned_name
        )

        counter += 1

    dataframe.to_csv(
        output_path,
        index=False
    )

    return {
        "filename": cleaned_name,
        "path": output_path
    }