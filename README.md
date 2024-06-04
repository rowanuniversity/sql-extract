# sql-extract
Exports the results of Oracle sql code contained in a .sql file out to a csv file. 

## Usage
```bash
# with input file
sql-extract in_sql_file.sql -o output_file.csv

# with quick text
sql-extract -t "select 1 from dual" -o output_file.csv

# with named bind parameters
sql-extract -t "select * from phonebook where first_name=:fn and last_name=:ln" -b fn=Dennis ln=Nedry -o output_file.csv

# additional help
sql-extract -h
```

*Note: if you do not provide an output file with -o, the tool will simply output the* 
*data to a .csv file with the same base file name as the input file (test.sql -> test.csv).*
*If -t is used, and no output file path is provided, the results will be sent to stdout.*

## Parameters
| Name            | Description                         | Type   | Required |
|-----------------|-------------------------------------|--------|----------|
| filename        | input ```.sql``` file name                | string | yes      |
| -o, --outfile   | output ```.csv``` file name               | string | no       |
| -d, --delimiter | ```.csv``` delimiter                       | string | no       |
| -c, --quotechar | ```.csv``` quote character                 | string | no       |
| -i, --heading   | ```.csv``` include column headings Y/N     | string | no       |
| -l, --login | Oracle login string                 | string | no       |
| -p, --password | Oracle password                 | string | no       |
| -t, --text | SQL query text (instead of file) | string | no |
| -b, --bind-variables | Any named bind parameters in the ```.sql``` file, must follow param=value convention | list | no |
| positional_variables       | any positional variables in the ```.sql``` file | list   | no       |

## Unit Testing

```shell script
./unittests.py
```

### Configuration
Store your Oracle login and password in ```full_login``` and ```db_password``` environment variables, respectively. Otherwise,
you must use ```--login``` and ```--password``` to pass in your credential(s). You can alternatively store your login as 
an environment variable but not your password (or vice versa).

### Additional examples 

```bash
# this will print out comma-sep data, rather than write it to disk
sql-extract -t "select * from general.people where first_name=:p_name;" -b p_name=Dennis

# this will write to disk
sql-extract -t "select * from general.people where first_name=:p_name;" -b p_name=Dennis -o /some/path/to/file.csv

# this will write to disk at given -o location
sql-extract /some/input/file.sql -b p_name=Dennis -o /some/path/to/file.csv

# this will write to disk at /some/input/file.csv
sql-extract /some/input/file.sql -b p_name=Dennis
```
