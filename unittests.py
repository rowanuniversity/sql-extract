#!/usr/bin/env python3
"""
Some basic unit tests. Needs some expanding.

./unittests.py
"""
import unittest
import csv
import pathlib
from sql_extract import SqlExtractHandler, get_sql_extract_argparser, main
from profpy.db import with_cx_oracle_connection

test_path = str(pathlib.Path("/tmp/test.csv"))
ap = get_sql_extract_argparser()

@with_cx_oracle_connection()
def test_run(cnxn, args):
    parsed = ap.parse_args(args)
    SqlExtractHandler(cnxn, parsed.filename, parsed.outfile,
                      in_delim=parsed.delimiter, in_quot=parsed.quotechar,
                      in_positionals=parsed.positional_variables, in_named=parsed.bind_variables, 
                      in_text=parsed.text)


class TestBase(unittest.TestCase):

    def test_basic_query(self):
        args = [
            "-t", "select 1 as column_1 from dual;", "-o", test_path
        ]
        test_run(args)
        with open(test_path, "r") as csv_file:
            r = csv.reader(csv_file)
            header = next(r)
            self.assertTrue(header == ["COLUMN_1"])
            valid = True 
            try:
                self.assertTrue(str(next(r)[0]) == "1")
            except IndexError:
                valid = False
            self.assertTrue(valid)

    def test_column_name_case(self):
        args = [
            "-t", "select 1 as \"ColumnName\" from dual;", "-o", test_path
        ]
        test_run(args)
        with open(test_path, "r") as csv_file:
            self.assertTrue(next(csv.reader(csv_file)) == ["ColumnName"])

    def test_no_semicolon(self):
        args = [
            "-t", "select 1 as test_run from dual", "-o", test_path
        ]
        valid = True
        try:
            test_run(args)
        except:
            valid = False
        self.assertTrue(valid)


    def test_bind_params(self):
        args = [
           "-t", "select :0 as col_1, :1 as col_2, :2 as col_3 from dual;", "-o", test_path, 
           "-b", "0=A", "1=B", "2=C"
        ]
        test_run(args)
        with open(test_path, "r") as csv_file:
            r = csv.reader(csv_file)
            next(r)
            self.assertEqual(next(r), ["A", "B", "C"])
    

if __name__ == "__main__":
    unittest.main()
