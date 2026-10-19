import pandas as pd


def analyze_data_quality(dataframe):
    """
    Analyze the quality of a Pandas DataFrame.

    This function does not modify the original dataset.
    """

    # ==========================================
    # BASIC INFORMATION
    # ==========================================

    total_rows = len(dataframe)
    total_columns = len(dataframe.columns)

    total_cells = (
        total_rows * total_columns
    )

    # ==========================================
    # MISSING VALUES
    # ==========================================

    missing_by_column = {}
    total_missing = 0

    for column in dataframe.columns:

        missing_count = int(
            dataframe[column]
            .isna()
            .sum()
        )

        missing_by_column[
            str(column)
        ] = missing_count

        total_missing += missing_count

    # ==========================================
    # DUPLICATE ROWS
    # ==========================================

    duplicate_rows = int(
        dataframe
        .duplicated()
        .sum()
    )

    # ==========================================
    # EMPTY COLUMNS
    # ==========================================

    empty_columns = []

    for column in dataframe.columns:

        if dataframe[column].isna().all():

            empty_columns.append(
                str(column)
            )

    # ==========================================
    # DATA TYPES
    # ==========================================

    numeric_columns = []
    text_columns = []
    date_columns = []
    other_columns = []

    for column in dataframe.columns:

        dtype = dataframe[column].dtype

        if pd.api.types.is_numeric_dtype(dtype):

            numeric_columns.append(
                str(column)
            )

        elif pd.api.types.is_datetime64_any_dtype(dtype):

            date_columns.append(
                str(column)
            )

        elif pd.api.types.is_object_dtype(dtype):

            text_columns.append(
                str(column)
            )

        else:

            other_columns.append(
                str(column)
            )

    # ==========================================
    # COLUMN DETAILS
    # ==========================================

    column_details = []

    for column in dataframe.columns:

        series = dataframe[column]

        missing = int(
            series.isna().sum()
        )

        unique = int(
            series.nunique(
                dropna=True
            )
        )

        if pd.api.types.is_numeric_dtype(series):

            data_type = "numeric"

        elif pd.api.types.is_datetime64_any_dtype(series):

            data_type = "date"

        elif pd.api.types.is_object_dtype(series):

            data_type = "text"

        else:

            data_type = "other"

        column_details.append({

            "name": str(column),

            "type": data_type,

            "pandas_type": str(
                series.dtype
            ),

            "missing": missing,

            "unique": unique,

            "empty": bool(
                series.isna().all()
            )

        })

    # ==========================================
    # QUALITY SCORE
    # ==========================================

    if total_cells == 0:

        quality_score = 0

    else:

        missing_ratio = (
            total_missing /
            total_cells
        )

        duplicate_ratio = (
            duplicate_rows /
            total_rows
            if total_rows > 0
            else 0
        )

        empty_column_ratio = (
            len(empty_columns) /
            total_columns
            if total_columns > 0
            else 0
        )

        missing_penalty = (
            missing_ratio * 50
        )

        duplicate_penalty = (
            duplicate_ratio * 30
        )

        empty_column_penalty = (
            empty_column_ratio * 20
        )

        quality_score = (
            100
            - missing_penalty
            - duplicate_penalty
            - empty_column_penalty
        )

        quality_score = max(
            0,
            min(
                100,
                quality_score
            )
        )

    quality_score = round(
        quality_score,
        2
    )

    # ==========================================
    # RECOMMENDATIONS
    # ==========================================

    recommendations = []

    if total_missing > 0:

        recommendations.append({

            "type": "missing_values",

            "message":
                "Missing values were detected.",

            "count":
                total_missing

        })

    if duplicate_rows > 0:

        recommendations.append({

            "type": "duplicates",

            "message":
                "Duplicate rows were detected.",

            "count":
                duplicate_rows

        })

    if len(empty_columns) > 0:

        recommendations.append({

            "type": "empty_columns",

            "message":
                "Completely empty columns were detected.",

            "count":
                len(empty_columns)

        })

    # ==========================================
    # FINAL REPORT
    # ==========================================

    return {

        "quality_score":
            quality_score,

        "summary": {

            "rows":
                total_rows,

            "columns":
                total_columns,

            "total_cells":
                total_cells,

            "missing_values":
                total_missing,

            "duplicate_rows":
                duplicate_rows,

            "empty_columns":
                len(empty_columns)

        },

        "missing_values":
            missing_by_column,

        "empty_column_names":
            empty_columns,

        "column_types": {

            "numeric":
                numeric_columns,

            "text":
                text_columns,

            "date":
                date_columns,

            "other":
                other_columns

        },

        "columns":
            column_details,

        "recommendations":
            recommendations

    }