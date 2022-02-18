# script creates a csv file that can be subsequently used to map settlement date and settlement period
# data to utc and localtime using a format YYYY-MM-DD_SP where SP is the settlement period from 01 to 50
# there are:
# 48 settlement periods in a normal day,
# 46 in a short day (last Sunday in March)
# 50 in a long day (last Sunday in October)
# takes 30s to run on macbook pro 2.9Ghz intel core i7
# takes 7s to run on Macbook Pro M1 (2020)
# from Energy Informatics Group at the University of Birmingham, UK
# contact details: https://orcid.org/0000-0003-4083-597X


import os.path
import time
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

start_time = time.time()

home_folder = os.getenv('HOME')
output = f'{home_folder}/OneDrive - University of Birmingham/elexon_ng_espeni/'
os.chdir(output)

# the start and end dates for analysis are set here
# the startdate must be in non-daylight savings for the code to work
# i.e. the startdate must be between the 2am on the last sunday in October
# and 12midnight on the last saturday in March
# as this code creates data that is subsequently used to map values from date and settlement periods
# suggest setting the startdate to the first day of a year
startdate = '2001-01-01'
enddate = '2030-12-31'

# creates a utc column of dates between the start and end dates
# and an additional column with date localised to London
# this is needed so that the .dst() function can be called to test whether dst, daylight saving times are in place
# this flags True for a date that is in dst (summer) and False if not in dst (winter)
# note: False dst is a similar datetime to utc (or gmt), whereas True dst is an hour ahead of utc (or gmt)
# utc and gmt are in essence the same time, but utc is a standard whereas gmt is a timezone
df = pd.DataFrame()
df['utc'] = pd.date_range(start=startdate, end=enddate, freq='D', tz='UTC')
df['utc_date'] = df['utc'].apply(lambda x: str(x.date()))
# df['utc_date'] = df['utc'].dt.date.astype(str)
df['localtime'] = df['utc'].dt.tz_convert('Europe/London')
df['localtimeisdst'] = df['localtime'].apply(lambda x: bool(x.dst()))
df['clockchange'] = df['localtimeisdst'].diff()

# as the dates have a hour segment at 00:00:00, the dst flag actually starts the day after
# the dst happens at 01:00:00. Therefore, a day is taken away from the datetime date, using -pd.Timedelta(days=1)
# this gives the correct day for the date when dst clocks go forward and back
# these short and long dates are put into a df column to allow further dates to be checked against these using .isin
dfshortlongdays = pd.DataFrame()
dfshortlongdays['short_days'] = (df['utc'][df['clockchange'] == 1] - pd.Timedelta(days=1)).dt.date.reset_index(drop=True)
dfshortlongdays['long_days'] = (df['utc'][df['clockchange'] == -1] - pd.Timedelta(days=1)).dt.date.reset_index(drop=True)

# creates boolean colums that flag whether a date is a short_day, long_day or normal_day
def shortlongflags(dfname, datetimecol):
    dfname['short_day_flag'] = dfname[datetimecol].dt.date.isin(dfshortlongdays['short_days'])
    dfname['long_day_flag'] = dfname[datetimecol].dt.date.isin(dfshortlongdays['long_days'])
    dfname['normal_day_flag'] = (dfname['short_day_flag'] == True) | (dfname['long_day_flag'] == True)  # logical OR
    dfname['normal_day_flag'] = -dfname['normal_day_flag']  # the minus sign inverts the boolean series
    return (dfname)

shortlongflags(df, 'utc')

# the boolean columns are used to put settlement period count values
# 48 settlement periods in a normal day,
# 46 in a short day (last Sunday in March)
# 50 in a long day (last Sunday in October)
df.loc[df['normal_day_flag'] == True, 'settlement_period_count'] = 48
df.loc[df['short_day_flag'] == True, 'settlement_period_count'] = 46
df.loc[df['long_day_flag'] == True, 'settlement_period_count'] = 50
df['settlement_period_count'] = df['settlement_period_count'].astype('int')

# creates a long series from the df dataframe created above
# this has a list of dates between the start and end dates, and the corresponding number of
# settlement periods e.g. 48 normal_day, 46 short_day, 50 long_day
# this long list creates a settlement_day settlement_period list e.g. 2020-12-30_03
# which is subsequently used to map date settlement periods for data that has only
# date and settlement period information, with no time information
dftemplist = []
for i, row in df.iterrows():
    tempval = row['utc_date']
    # print(i, row['newcol'])
    for j in range(1, row['settlement_period_count'] + 1):
        dftemplist.append(tempval + '_' + str(j).zfill(2))

# creates a dfa from the dftemplist and creates str columns of the date and settlement_period
# then uses module to add short and long day flags
dfa = pd.DataFrame(dftemplist, columns=['datesp'])
dfa['settlementdate'] = dfa['datesp'].map(lambda x: x.split('_')[0])
dfa['settlementperiod'] = dfa['datesp'].map(lambda x: x.split('_')[1])


# dfa['settlementdate'] = dfa['datesp'].str[:10]
# dfa['settlementperiod'] = dfa['datesp'].str[-2:]
# creates a utc column of 30 minute values that starts at the same datetime as the startdate
# and has the same length as the dataframe
# this matches the settlement date, settlement period text e.g. 2020-12-30_03
# with a utc datetime value
# a localtime column for Great Britain is created from the utc column using dt.tz_convert('Europe/London')
dfa['utc'] = pd.date_range(start=startdate, periods=dfa.shape[0], freq='30min', tz='UTC')
dfa['localtime'] = dfa['utc'].dt.tz_convert('Europe/London')
dfa['localtimeisdst'] = dfa['localtime'].apply(lambda x: bool(x.dst()))


# the shortlongflags def is called on the dataframe to provide boolean columns for short, long and normal days
shortlongflags(dfa, 'localtime')

# for isoformat output
dfa['localtime'] = dfa['localtime'].map(lambda x: x.isoformat())
dfa['utc'] = dfa['utc'].map(lambda x: x.isoformat())
dfa.to_csv('masterlocaltime_iso8601.csv', encoding='Utf-8', index=False)
dfa.to_parquet('masterlocaltime_iso8601.parquet', index=False)

print("time elapsed: {:.2f}s".format(time.time() - start_time))