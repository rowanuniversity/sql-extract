# sql-extract
Exports the results of Oracle sql code contained in a .sql file out to a csv file. 

## Usage
```bash
# run 
sql-extract in_sql_file.sql -o output_file.csv

# additional help
sql-extract -h
```


## Parameters
| Name            | Description                         | Type   | Required |
|-----------------|-------------------------------------|--------|----------|
| filename        | input .sql file name                | string | yes      |
| -o, --outfile   | output .csv file name               | string | no       |
| -d, --delimiter | csv delimiter                       | string | no       |
| -c, --quotechar | csv quote character                 | string | no       |
| -l, --login | Oracle login string                 | string | no       |
| -p, --password | Oracle password                 | string | no       |
| bind_vars       | any bind variables in the .sql file | list   | no       |

### Configuration
Store your Oracle login and password in ```full_login``` and ```db_password``` environment variables, respectively. Otherwise,
you must use ```--login``` and ```--password``` to pass in your credential(s). You can alternatively store your login as 
an environment variable but not your password (or vice versa).
