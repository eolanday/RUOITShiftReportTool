import pandas as pd
import numpy as np
from datetime import datetime

# USER INPUT #
START_DATE = datetime(2019, 8, 31)     #inclusive
END_DATE = datetime(2019, 9, 7)       #not inclusive
auditor_netid = "qh63.RAD.007"		   # insert sup netid here + machine login from CMD prompt (ex. epl43.RAD.000)
CSV_file = 'ReportTable_08-31--09-06'	# insert csv file name(ex. ReportTable_03-24--03-29)
output_file = '08-31--09-06_ExistenceAudit'
###################

st_path = "/Users/%s/Downloads/SRs/data/ShiftTable.csv"%(auditor_netid)
rt_path = "/Users/%s/Downloads/SRs/data/%s.csv"%(auditor_netid, CSV_file)
new_existen_path = '/Users/%s/Downloads/SRs/%s.csv'%(auditor_netid, output_file)


#read SHIFT TABLE into a dataframe st
# uses st_path

st = pd.read_csv(st_path, dtype='str')
st['StartTime']= pd.to_datetime(st['StartTime'])
st['EndTime']= pd.to_datetime(st['EndTime'])
#st.head()

# read REPORT TABLE into a dataframe rt
# uses rt_path

rt = pd.read_csv(rt_path, dtype='str',encoding = "ISO-8859-1" )
rt = rt.drop(['Path','Item Type'], axis=1)
#rt['NumLogs'] = rt['NumLogs'].astype(dtype='int')
rt['ShiftStart']= pd.to_datetime(rt['ShiftStart'])
rt['ShiftEnd']= pd.to_datetime(rt['ShiftEnd'])
#rt['NumLogs'].dtype
#rt.head()


# audit the SHIFT TABLE st for certain dates
# uses START_DATE and END_DATE

exist_st=st[(st['StartTime'] > START_DATE) & (st['StartTime'] < END_DATE)]
exist_st=exist_st[exist_st.Location != 'ARC-Sups']
exist_st=exist_st[exist_st.Location != 'BEST-Sups']
#print(len(exist_st))
#exist_st

# audit the REPORT TABLE rt for certain dates

exist_rt=rt[(rt['ShiftStart'] > START_DATE) & (rt['ShiftStart'] < END_DATE)]
#print(len(exist_rt))
#exist_rt

exists = exist_st.merge(exist_rt, how='left', left_on=['Location','StartTime','EndTime'], right_on=['Site','ShiftStart','ShiftEnd'])
#exists

missing = exists[exists.NetID.isnull()]
#print(len(missing))
#assert (len(testst)-len(testrt))==(len(missing))
missing = missing.drop(['ID','ShiftID_y','Site','ShiftDate','ShiftStart','ShiftEnd','RoundLogs','Comments','NumLogs'], axis=1)
missing = missing.set_index('ShiftID_x')
#missing

missing['Situation'] = ""
missing['Excused?'] = ""

missing.to_csv(new_existen_path)
#missing.to_excel(new_existen_path,engine='xlsxwriter')


print('_____ audit_exists all done, check SRs folder for output! _____')
