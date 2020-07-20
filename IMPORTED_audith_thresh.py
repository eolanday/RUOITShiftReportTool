import pandas as pd
import numpy as np
from datetime import datetime
###################

# START USER INPUT HERE#
START_DATE = datetime(2019, 8, 31)      # inclusive
END_DATE = datetime(2019, 9, 7)       # not inclusive
auditor_netid = "epl43"		   # insert sup netid here + machine login from CMD prompt (ex. epl43.RAD.000)
CSV_file = 'ReportTable_08-31--09-06'	    # insert csv file name(ex. ReportTable_03-24--03-29.csv)
output_file = '08-31--09-06_ThreshAudit' 	# insert output file name (ex. 03-24--03-29_ThreshAudit)
# END USER INPUT HERE #

###################

st_path = "/Users/%s/Downloads/SRs/data/ShiftTable.csv"%(auditor_netid)
rt_path = "/Users/%s/Downloads/SRs/data/%s.csv"%(auditor_netid, CSV_file)
new_thresh_path = '/Users/%s/Downloads/SRs/%s.csv'%(auditor_netid, output_file)

#read SHIFT TABLE into a dataframe st
# uses st_path
st = pd.read_csv(st_path, dtype='str')
st['StartTime']= pd.to_datetime(st['StartTime'])
st['EndTime']= pd.to_datetime(st['EndTime'])
#st.head()

# read REPORT TABLE into a dataframe rt
# rt_path

rt = pd.read_csv(rt_path, dtype='str',encoding = "ISO-8859-1" )
rt = rt.drop(['Path','Item Type'], axis=1)
rt = rt[~rt['NumLogs'].isnull()] ########## remove Nans?
rt['NumLogs'] = rt['NumLogs'].astype(dtype='int')
rt['ShiftStart']= pd.to_datetime(rt['ShiftStart'])
rt['ShiftEnd']= pd.to_datetime(rt['ShiftEnd'])
#rt['NumLogs'].dtype
#rt.head()

# audit the REPORT TABLE rt for certain dates
# uses START_DATE and END_DATE

rt=rt[(rt['ShiftStart'] > START_DATE) & (rt['ShiftStart'] < END_DATE)]
rt = rt[rt['Site']!='RBHS-Cons']
rt = rt[rt['Site']!='ARC-Disp']
#rt.head()

# merge reportTable and shiftTable for Weekdays/ShiftTime

rt = rt.merge(st, how='left', left_on=['Site','ShiftStart','ShiftEnd'], right_on=['Location','StartTime','EndTime'])

rt = rt[['NetID','Site','WeekDay','ShiftDate','ShiftTime','ShiftStart','ShiftEnd','RoundLogs','Comments','NumLogs']]
#rt.head()

# calculate appropriate threshold

# rt['test'] = (rt['ShiftEnd']-rt['ShiftStart'])
# rt['test'] = rt['test'].apply(lambda x: float(x.item()/60000000000))
# rt['test'] = (rt['test'] /15)*0.5
# print(rt.dtypes)

# rt['ThreshLogs'] = (((rt['ShiftEnd']-rt['ShiftStart']) / np.timedelta64(1, 'm')) /15)*0.5     #50% threshold
# rt['MaxLogs'] = (((rt['ShiftEnd']-rt['ShiftStart']) / np.timedelta64(1, 'm')) /15)
# rt['PercentDone'] = rt['NumLogs']/rt['MaxLogs']*100

rt['ThreshLogs'] = (rt['ShiftEnd'].values-rt['ShiftStart'].values)
rt['ThreshLogs'] = rt['ThreshLogs'].astype('timedelta64[m]')

rt['ThreshLogs'] = (rt['ThreshLogs']/15)*0.5
rt['MaxLogs'] = (rt['ShiftEnd'].values-rt['ShiftStart'].values)
rt['MaxLogs'] = rt['MaxLogs'].astype('timedelta64[m]')
rt['MaxLogs'] = rt['MaxLogs'] / 15
rt['PercentDone'] = rt['NumLogs']/rt['MaxLogs']*100

# # select rows that are below threshold

rt = rt[rt['NumLogs']<rt['ThreshLogs']]

# add notation columns
rt['Excused?'] = ""
rt['Notes'] = ""

#print(len(rt))
#rt.head()

rt.to_csv(new_thresh_path)
#rt.to_excel(new_thresh_path, engine='xlsxwriter', index=False)

print('_____ audit_thresh all done, check SRs folder for output! _____')
