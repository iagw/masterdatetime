# masterdatetime.py

script creates a csv file that can be subsequently used to map date and settlement period
data to utc and localtime uses the format YYYY-MM-DD_SP where SP is the half-hourly settlement period from 01 to 50
there are:
48 settlement periods in a normal day,
46 in a short day (last Sunday in March)
50 in a long day (last Sunday in October)
takes 30s to run on macbook pro 2.9Ghz intel core i7

is used to provide ISO 8601 compatible datetime data from the settlement date and settlement period data that are typical
of Elexon and National Grid electrical generation and interconnector data
