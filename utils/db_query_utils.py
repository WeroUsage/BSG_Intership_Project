import os
from pathlib import Path

import pandas as pd
from cx_Oracle import Cursor

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)


class DBQueryCache:
    """Cache class to save the result of the queries run."""

    def __init__(self, initialCache: dict = {}):
        """Initializer

        Args:
            initialCache (dict, optional): Initial queries and result cache to inject. Defaults to {}.
        """
        self.cache = initialCache

    def put(self, query, result):
        """Write a query result in the cache.

        Args:
            query (_type_): Query script run.
            result (_type_): Result data obtained.
        """
        self.cache[query] = result

    def get(self, query):
        """Read query result from cache.

        Args:
            query (_type_): Query script run.

        Returns:
            _type_: Result data cached.
        """
        return self.cache.get(query)

    def clear(self):
        """Clear the content present in the cache."""
        self.cache = {}


class DBQuery:
    """Helper class to easily run a query in the DB."""

    def __init__(
        self,
        cursor: Cursor,
        file_name: str = None,
        query: str = None,
        base_folder: str = None,
        root_folder: str = None,
        by_steps: bool = True,
        limit: int = None,
        use_cache: bool = True,
        old_cache=None,
        transform: list = None,
    ):
        """Initializer.
            Load and preprocesse the query from a file or a given string,
            set the parameters needed to run the query,
            initialize the cache.

        Args:
            cursor (Cursor): Oracle DB connection reference.
            file_name (str, optional): Name of the file containing the query. Defaults to None.
            query (str, optional): String containing the query. Defaults to None.
            base_folder (str, optional): Base folder of the given file. Defaults to None.
            root_folder (str,  optional): Root folder of the given file (where path starts). Defaults to None.
            by_steps (bool, optional): If query must be run by steps/pieces. Defaults to True.
            limit (int, optional): Max amount of records to retrieve. Defaults to None.
            use_cache (bool, optional): If cache should be used to optimize queries. Defaults to True.
            old_cache (DBQueryCache|dict, optional): Initial cache instance. Defaults to None.
            transform (list, optional): List of data transformation to apply to the result. Defaults to None.
        """
        assert not (
            file_name is None and query is None
        ), "Either file_name or query must be provided."

        self.root_folder = root_folder


        self.by_file = file_name is not None
        if self.by_file:
            if base_folder is None:
                self.file_path = Path(os.getcwd()) / file_name
            else:
                self.file_path = Path(os.getcwd()) / Path(base_folder) / file_name
            self.raw_qry = None
        else:
            self.file_path = None
            self.raw_qry = query

        if root_folder is not None:
            self.file_path = Path(root_folder) / Path(base_folder) / file_name

        self.by_steps = by_steps
        self.qry = None
        self.__populate_query()

        self.cursor = cursor
        self.limit = limit
        self.transform = transform

        self.cache = None
        if use_cache and old_cache is not None and type(old_cache) is DBQueryCache:
            self.cache = old_cache
        elif use_cache and old_cache is not None and type(old_cache) is dict:
            self.cache = DBQueryCache(initialCache=old_cache)
        elif use_cache and old_cache is None:
            self.cache = DBQueryCache()

    def __populate_query(self):
        """Preprocess given file or query content to obtain a list of executable queries."""
        if self.by_file:
            with open(self.file_path, "r") as f:
                lines = f.readlines()
        else:
            lines = self.raw_qry.split("\n")

        if self.by_steps:
            self.qry = self.__process_subqueries(lines)
        else:
            self.qry = [["".join(lines)]]

    def __process_steps(self, q: list):
        """Preprocess query steps into executable query strings.

        Args:
            q (list): List of subquery steps.

        Returns:
            list: Preprocessed list of query steps.
        """
        steps = [i for i, e in enumerate(q) if "BASE_QUERY" in e or "QUERY_STEP" in e]

        if len(steps) > 0:
            base = steps[0]
            steps = [(base, s) for s in steps[1:] + [None]]
        else:
            steps = [(0, None)]

        steps = [q[a:b] for a, b in steps]
        steps = ["".join(s) for s in steps]

        return steps

    def __process_subqueries(self, qry: list):
        """Preprocess query parts into executable query strings.

        Args:
            qry (list): List of query parts.

        Returns:
            list: Preprocessed list of query parts.
        """
        sub_queries = [i for i, e in enumerate(qry) if "SUB_QUERY" in e]
        sub_queries = zip(sub_queries, sub_queries[1:] + [None])
        sub_queries = [qry[a:b] for a, b in sub_queries]

        qry = [self.__process_steps(q) for q in sub_queries]
        return qry

    def __apply_transform(self, result: pd.DataFrame):
        """Apply the given transformation to the given columns.

        Args:
            result (pd.DataFrame): Result dataframe obtained from the query.

        Returns:
            pd.DataFrame: Modified result dataframe.
        """
        for t in self.transform:
            col_name, func = t[0], t[1]
            result[col_name] = result[col_name].apply(func)

        return result

    def __run_query_step(
        self,
        query: str,
        num_rows: int = None,
        use_cache: bool = True,
        apply_transform: bool = True,
    ):
        """Execute the query step in the DB and return result as a dataframe.

        Args:
            query (str): Query step string to execute.
            num_rows (int, optional): Max number of records. Defaults to None.
            use_cache (bool, optional): Whether to use cache to store the result. Defaults to True.
            apply_transform (bool, optional): Whether to apply the transformation steps to the result. Defaults to True.

        Returns:
            pd.DataFrame: Result dataframe.
        """
        if use_cache and self.cache is not None and self.cache.get(query) is not None:
            res = self.cache.get(query)
            print("Using cached result...")
        else:
            self.cursor.execute(query)

            cols = [a[0] for a in self.cursor.description]

            if num_rows is None:
                data = self.cursor.fetchall()
            else:
                data = self.cursor.fetchmany(num_rows)

            res = pd.DataFrame(data, columns=cols)

            if apply_transform and self.transform is not None:
                res = self.__apply_transform(res)

            if use_cache and self.cache is not None:
                self.cache.put(query, res)

        return res

    def run(self, use_cache: bool = True, apply_transform: bool = True):
        """Double check if the query has changed, reload it and run all the query steps.

        Args:
            use_cache (bool, optional): Whether to use cache to store the result. Defaults to True.
            apply_transform (bool, optional): Whether to apply the transformation steps to the result. Defaults to True.

        Returns:
            list: Result list of result dataframes for each step.
        """
        self.__populate_query()

        return [
            self.__run_query_step(
                s,
                num_rows=self.limit,
                use_cache=use_cache,
                apply_transform=apply_transform,
            )
            for q in self.qry
            for s in q
        ]
