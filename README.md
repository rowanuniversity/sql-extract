# sql-extract
Exports the results of Oracle sql code contained in a .sql file out to a csv file. 

## Usage
```shell script
# with input file
sql-extract in_sql_file.sql -o output_file.csv

# with quick text
sql-extract -t "select 1 from dual" -o output_file.csv

# with named bind parameters
sql-extract -t "select * from phonebook where first_name=:fn and last_name=:ln" -b fn=Dennis ln=Nedry -o output_file.csv

# additional help
sql-extract -h
```

## Parameters
| Name            | Description                         | Type   | Required |
|-----------------|-------------------------------------|--------|----------|
| filename        | input ```.sql``` file name                | string | yes      |
| -o, --outfile   | output ```.csv``` file name               | string | no       |
| -d, --delimiter | ```.csv``` delimiter                       | string | no       |
| -c, --quotechar | ```.csv``` quote character                 | string | no       |
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
