#!/usr/bin/env python3
"""
Utility functions and class for sql-extract
"""
import sys
import os
import re
import csv
import openpyxl
import logging
import argparse
from profpy.db import get_cx_oracle_connection
from cx_Oracle import DatabaseError


class SqlExtractHandler(object):
    """
    Helper class that handles the actual parsing of the csv file from the input sql and variables.
    """
    def __init__(self, conn, in_sql_file=None, in_out_file_location=None, in_delim=",", in_quot="\"", in_positionals=None, in_named=None, in_text=None):
        """
        Constructor
        :param conn:                 Oracle connection                        (cx_Oracle.Connection)
        :param in_sql_file:          The sql file                             (str)
        :param in_out_file_location: The location of the output csv           (str)
        :param in_delim:             The csv delimiter                        (str)
        :param in_quot:              The csv quote character                  (str)
        :param in_positions:         Any pos. variables for the sql statement (list)
        :param in_named:             Any named bind parameters                (list)
        :param in_text:              SQL query text (in place of file)        (str)
        """

        # configure the appropriate bind variables and sql string
        self.sql = self.configure_sql(in_sql_file, in_text)
        self.binds = self.configure_bind_vars(in_named, in_positionals)
        self.row_count = 0
        self.csv_file = in_out_file_location if in_out_file_location else os.path.splitext(in_sql_file)[0] + ".csv"
        self.cnxn = conn
        self.cursor = self.cnxn.cursor()
        self.columns = []

        # create a new dialect for local use
        self.dialect = csv.excel # use Excel dialect defaults
        self.dialect.delimiter = "," if in_delim is None else str(in_delim)[0]
        self.dialect.escapechar = None
        
        # set up the appropriate quoting
        if in_quot is None:
            self.dialect.quote_character = "\""
            self.quoting = csv.QUOTE_NONE
            self.dialect.escapechar = "\\"
        else:
            self.dialect.quote_character = in_quot
            self.quoting = csv.QUOTE_NONNUMERIC

        # register the dialect
        csv.register_dialect("local_custom", delimiter=self.dialect.delimiter, quotechar=self.dialect.quote_character, escapechar=self.dialect.escapechar)
        
        # run the actual extract program
        self.run_query()
        self.write_results()
        self.close()


    def write_results(self):
        """
        Writes the results of the query to file
        """
        with open(self.csv_file, 'w') as csv_handler:
            writer = csv.DictWriter(csv_handler, fieldnames=self.columns, quoting=self.quoting,
                                            dialect="local_custom")
            writer.writeheader()
            for csv_row in self.row_generator():
                writer.writerow(csv_row)
                self.row_count += 1    


    def run_query(self):
        """
        Runs the query.
        """
        try:
            if self.binds:
                self.execute(self.sql, self.binds)
            else:
                self.execute(self.sql)
            self.columns = [str(c[0]) for c in self.cursor.description]
            
        except Exception as e:
            logging.debug(str(e))
            logging.debug(self.sql)
            self.close()
            raise e

    def close(self):
        """
        Cleanup any database objects, connection is handled by caller that creates this class
        """
        self.cursor.close()

    def execute(self, sql, params=None):
        """
        Encapsulated logic for executing SQL queries, with or without params
        """
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)

    def row_generator(self, num_rows=1000):
        """
        Yield rows from the executed sql statement
        :return:
        """
        while True:
            rows = self.cursor.fetchmany(num_rows)
            if not rows:
                break
            else:
                for row in rows:
                    yield dict(zip(self.columns, row))


    def configure_sql(self, in_sql_file, in_text):
        """
        Appropriately configure incoming SQL text/file
        """
        out_sql = ""
        # make sure we received some sql
        if not (in_sql_file or in_text):
            raise IOError("You must provide either a SQL file or text query to execute.")
        else:
            # read in sql from file
            if in_sql_file:
                with open(in_sql_file, "r") as sql_file:
                    out_sql = sql_file.read()
            
            # read in sql from cmd line
            else:
                out_sql = _read_input_sql(in_text)

            # clean up string, remove semicolon if needed
            out_sql = out_sql.strip()
            out_sql = out_sql[:-1] if out_sql[-1:] == ";" else out_sql
        return out_sql

    def configure_bind_vars(self, named, positionals):
        binds = dict()
        if named and positionals:
            raise IOError("You cannot use named and positional bind parameters.")
        else:
            if positionals:
                binds = self.parse_positional_binds(positionals)
            elif named:
                binds = self.parse_named_binds(named)   
        return binds  

    def parse_positional_binds(self, in_binds):
        """
        Handle positional bind parameters correctly.
        """
        out_binds = {}
        for i, v in enumerate(in_binds):
            out_binds[str(i)] = v
        return out_binds


    def parse_named_binds(self, in_binds):
        """
        Handles named input bind parameters
        :return: dict containing named bind parameters and their attached values
        """
        out_binds = dict()
        if in_binds:
            pattern = re.compile(r"^[a-zA-Z_0-9]+=.+$")
            for param_input in in_binds:
                if not pattern.match(param_input):
                    raise IOError(f"Invalid bind parameter format ({param_input}). Must be param=value.")
                else:
                    parts = param_input.split("=")
                    out_binds[parts[0]] = "=".join(parts[1:]) # in case there is an "=" actually in the value as well
        return out_binds


class CsvToXlsxHandler(object):
    """
    Class to handle converting CSV to XLSX.
    """
    def __init__(self, in_csv_file, out_xlsx_file=None):
        self.row_count = 0
        self.xlsx_file = out_xlsx_file if out_xlsx_file else os.path.splitext(in_csv_file)[0] + ".xlsx"
        self.wb = openpyxl.Workbook()
        ws = self.wb.active
        with open(in_csv_file, 'r') as csvf:
            reader = csv.reader(csvf)
            for r, row in enumerate(reader, start=1):
                for c, val in enumerate(row, start=1):
                    ws.cell(row=r, column=c).value = val
                self.row_count += 1
        self.wb.save(self.xlsx_file)


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

def _read_input_sql(input_sql):
    """
    Read SQL input from the command line
    """
    if input_sql:
        if len(input_sql) > 1:
            return " ".join(input_sql)
        else:
            return input_sql[0]
    else:
        return ""


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


def get_sql_extract_argparser():
    """
    Create an argparser for sql-extract
    """
    p = argparse.ArgumentParser()
    p.add_argument("filename", nargs="?", type=_validate_sql_file, help="SQL query to be exported as CSV")
    p.add_argument("-o", "--outfile", help="output file name")
    p.add_argument("-d", "--delimiter", help="CSV delimiter character")
    p.add_argument("-c", "--quotechar", type=_validate_quote_char, help="CSV quoting character")
    p.add_argument("-l", "--login", type=str, default=os.environ.get("full_login"), help="Optional Oracle login string, defaults to look for an environment variable called \"full_login\".")
    p.add_argument("-p", "--password", type=str, default=os.environ.get("db_password"), help="Optional Oracle password, defaults to look for an environment variable called \"db_password\".")
    p.add_argument("-b", "--bind-variables", nargs="*", help="Optional named bind parameters. Enter as param1=value1 param2=value2")
    p.add_argument("-t", "--text", nargs="+", help="SQL query as text (instead of file). If a filename is specified, this argument will be ignored.")
    p.add_argument("positional_variables", nargs="*", help="Positional bind parameters to be passed to SQL file. If named bind variables (-b) are specified, this argument will be ignored.")
    return p

def with_cmd_line_args(f):
    """
    Decorator that passes in command line arguments for the sql-extract tool to the decorated function
    :param f: The function that will receive the command line arguments (function)
    :return:  The decorated function                                    (function)
    """
    def wrapper(*args, **kwargs):
        p = get_sql_extract_argparser()
        return f(p.parse_args(), *args, **kwargs)
    return wrapper

@with_cmd_line_args
def main(cmd_line_args):
    """
    Main logic of the program.
    """
    if not (cmd_line_args.login and cmd_line_args.password):
        logging.error("Missing Oracle credentials. You must set \"full_login\" and \"db_password\". Alternatively, "
                      "you can pass your credentials to this script with the --login and --password parameters.")
    else:
        conn = get_cx_oracle_connection(login=cmd_line_args.login, password=cmd_line_args.password)
        try:
            logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())
            handler = SqlExtractHandler(conn, cmd_line_args.filename, cmd_line_args.outfile,
                                        in_delim=cmd_line_args.delimiter, in_quot=cmd_line_args.quotechar,
                                        in_positionals=cmd_line_args.positional_variables, in_named=cmd_line_args.bind_variables, 
                                        in_text=cmd_line_args.text)
            in_display_path = os.path.splitext(cmd_line_args.filename)[0].ljust(35) if cmd_line_args.filename else _read_input_sql(cmd_line_args.text)
            logging.info(
                "{0} {1} {2}".format(
                    in_display_path,
                    str(handler.row_count).rjust(7),
                    "records processed"
                )
            )
        except DatabaseError as e:
            logging.error(e)
        finally:
            conn.rollback()
            conn.close()
            del conn

def with_xlsx_cmd_line_args(f):
    """
    Decorator that passes in command line arguments for the sql-extract tool to the decorated function
    :param f: The function that will receive the command line arguments (function)
    :return:  The decorated function                                    (function)
    """
    def wrapper(*args, **kwargs):
        p = argparse.ArgumentParser()
        p.add_argument("filename", help="CSV to be converted to XLSX")
        p.add_argument("-o", "--outfile", help="Output XLSX file name", default=None)
        return f(p.parse_args(), *args, **kwargs)
    return wrapper

@with_xlsx_cmd_line_args
def csv2xlsx(cmd_line_args):
    if not (cmd_line_args.filename):
        logging.error("Must specify input CSV file.")
    else:
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())
        handler = CsvToXlsxHandler(cmd_line_args.filename, cmd_line_args.outfile)
        logging.info(
            f"{os.path.splitext(cmd_line_args.filename)[0].ljust(35)} " +
            f"{str(handler.row_count).rjust(7)} records processed"
        )


if __name__ == "__main__":
    main()