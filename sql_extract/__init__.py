"""
_sql_extract.py
Utility functions and class for sql-extract
"""
import sys
import os
import csv
import logging
import argparse
from profpy.db import get_cx_oracle_connection
from cx_Oracle import DatabaseError


class SqlExtractHandler(object):
    """
    Helper class that handles the actual parsing of the csv file from the input sql and bind variables.
    """
    def __init__(self, conn, in_sql_file, in_out_file_location=None, in_delim=",", in_quot="\"", in_bind_vars=None):
        """
        Constructor
        :param conn:                 Oracle connection                        (cx_Oracle.Connection)
        :param in_sql_file:          The sql file                             (str)
        :param in_out_file_location: The location of the output csv           (str)
        :param in_delim:             The csv delimiter                        (str)
        :param in_quot:              The csv quote character                  (str)
        :param in_bind_vars:         Any bind variables for the sql statement (list)
        """

        self.row_count = 0
        self.csv_file = in_out_file_location if in_out_file_location else os.path.splitext(in_sql_file)[0] + ".csv"
        self.cur = conn.cursor()

        # create a new dialect for local use
        self.dialect = csv.excel # use Excel dialect defaults
        self.dialect.delimiter = "," if in_delim is None else str(in_delim)[0]
        self.dialect.escapechar = None
        if in_quot is None:
            self.dialect.quote_character = "\""
            self.quoting = csv.QUOTE_NONE
            self.dialect.escapechar = "\\"
        else:
            self.dialect.quote_character = in_quot
            self.quoting = csv.QUOTE_NONNUMERIC

        csv.register_dialect("local_custom", delimiter=self.dialect.delimiter, quotechar=self.dialect.quote_character,
                             escapechar=self.dialect.escapechar)
        self.bind_vars = in_bind_vars if in_bind_vars else []

        with open(in_sql_file, 'r') as sql:
            try:
                self.cur.execute(sql.read(), self.bind_vars)
            except Exception as e:
                logging.error("Unable to execute statement.")
                logging.warning(str(e))
                logging.debug(self.cur.statement)
                self.close()
                sys.exit(2)
            self.columns = [i[0] for i in self.cur.description]
            with open(self.csv_file, 'w') as csv_handler:
                self.writer = csv.DictWriter(csv_handler, fieldnames=self.columns, quoting=self.quoting,
                                             dialect="local_custom")
                self.writer.writeheader()
                for csv_row in self.row_generator():
                    self.writer.writerow(csv_row)
                    self.row_count += 1
        self.close()

    def close(self):
        """
        Cleanup any database objects, connection is handled by caller that creates this class
        :return:
        """
        self.cur.close()
        self.cur = None

    def row_generator(self):
        """
        Yield rows from the executed sql statement
        :return:
        """
        for row in self.cur:
            yield dict(zip(self.columns, row))


def _validate_quote_char(in_quote_char):
    """
    Validator function for the quote character command line argument
    :param in_quote_char: The input quote character (str)
    :return:              The quote character       (str)
    """
    if in_quote_char is not None and in_quote_char.lower() == "none":
        return None
    else:
        return in_quote_char


def _validate_sql_file(in_sql_file):
    """
    Validator function for the input sql file command line argument
    :param in_sql_file: The input sql file      (str)
    :return:            The validated file name (str)
    """
    if os.path.splitext(in_sql_file)[1] != ".sql":
        raise ValueError("Input file must a .sql file.")
    else:
        return in_sql_file


def with_cmd_line_args(f):
    """
    Decorator that passes in command line arguments for the sql-extract tool to the decorated function
    :param f: The function that will receive the command line arguments (function)
    :return:  The decorated function                                    (function)
    """
    def wrapper(*args, **kwargs):
        p = argparse.ArgumentParser()
        p.add_argument("filename", type=_validate_sql_file, help="SQL query to be exported as CSV")
        p.add_argument("-o", "--outfile", help="output file name")
        p.add_argument("-d", "--delimiter", help="CSV delimiter character")
        p.add_argument("-c", "--quotechar", type=_validate_quote_char, help="CSV quoting character")
        p.add_argument("-l", "--login", type=str, default=os.environ.get("full_login"), help="Optional Oracle login string, defaults to look for an environment variable called \"full_login\".")
        p.add_argument("-p", "--password", type=str, default=os.environ.get("db_password"), help="Optional Oracle password, defaults to look for an environment variable called \"db_password\".")
        p.add_argument("bind_vars", nargs="*", help="Bind variables to be passed to SQL file")
        return f(p.parse_args(), *args, **kwargs)
    return wrapper


@with_cmd_line_args
def main(cmd_line_args):
    if not (cmd_line_args.login and cmd_line_args.password):
        logging.error("Missing Oracle credentials. You must set \"full_login\" and \"db_password\". Alternatively, "
                      "you can pass your credentials to this script with the --login and --password parameters.")
    else:
        connection = get_cx_oracle_connection(cmd_line_args.login, cmd_line_args.password)
        try:
            logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())
            handler = SqlExtractHandler(connection, cmd_line_args.filename, cmd_line_args.outfile,
                                        in_delim=cmd_line_args.delimiter, in_quot=cmd_line_args.quotechar,
                                        in_bind_vars=cmd_line_args.bind_vars)
            logging.info(
                "{0} {1} {2}".format(
                    os.path.splitext(cmd_line_args.filename)[0].ljust(35),
                    str(handler.row_count).rjust(7),
                    "records processed"
                )
            )
        except DatabaseError as e:
            logging.error(e)
            connection.rollback()
        finally:
            connection.close()
            del connection
