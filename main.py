import pandas as pd
import numpy as np
from datetime import datetime
def getUserInput(minDate, maxDate):
    #get start and end date
    invalidInput=True;
    start="";
    end="";
    while(invalidInput):
        try:
            startIn = input("\nInput Start Date for Audit (Month/Day/Year)\n")
            start = datetime.strptime(startIn, '%m/%d/%Y');
        except ValueError  as delta:
            print("ERROR: ", delta)
        else:
            invalidInput = False;
        if not invalidInput:
            if start < minDate:
                print("ERROR: Date out of range of ReportTable")
                print("Earliest date is ",minDate.strftime('%m/%d/%Y'))
                invalidInput = True;
    invalidInput=True;
    while(invalidInput):
        try:
            endIn = input("\nInput End Date for Audit (Month/Day/Year)\n")
            end = datetime.strptime(endIn, '%m/%d/%Y');
        except ValueError  as delta:
            print("ERROR: ", delta)
        else:
            invalidInput = False;
        if not invalidInput:
            if end > maxDate:
                print("ERROR: Date out of range of ReportTable")
                print("Latest date is ",maxDate.strftime('%m/%d/%Y'))
                invalidInput = True;
    return start,end;

def existence(st, rt, START_DATE, END_DATE):
    # audit the SHIFT TABLE st for certain dates
    # uses START_DATE and END_DATE

    exist_st = st[(st['StartTime'] > START_DATE) & (st['StartTime'] < END_DATE)]
    exist_st = exist_st[exist_st.Location != 'ARC-Sups']
    exist_st = exist_st[exist_st.Location != 'BEST-Sups']
    # print(len(exist_st))
    # exist_st

    # audit the REPORT TABLE rt for certain dates

    exist_rt = rt[(rt['ShiftStart'] > START_DATE) & (rt['ShiftStart'] < END_DATE)]
    # print(len(exist_rt))
    # exist_rt

    exists = exist_st.merge(exist_rt, how='left', left_on=['Location', 'StartTime', 'EndTime'],
                            right_on=['Site', 'ShiftStart', 'ShiftEnd'])
    # exists

    missing = exists[exists.NetID.isnull()]
    # print(len(missing))
    # assert (len(testst)-len(testrt))==(len(missing))
    missing = missing.drop(
        ['ID', 'ShiftID_y', 'Site', 'ShiftDate', 'ShiftStart', 'ShiftEnd', 'RoundLogs', 'Comments', 'NumLogs'], axis=1)
    missing = missing.set_index('ShiftID_x')
    # missing

    missing['Situation'] = ""
    missing['Excused?'] = ""

    missing.to_csv("./existenceAuditReport_"+START_DATE.strftime('%m_%d')+"--"+END_DATE.strftime('%m_%d')+".csv")
    # missing.to_excel(new_existen_path,engine='xlsxwriter')

    print('_____ audit_exists all done, check SRs folder for output! _____')
    return;

def threshold(st,rt,START_DATE,END_DATE):
    # audit the REPORT TABLE rt for certain dates
    # uses START_DATE and END_DATE
    rt['NumLogs'] = rt['NumLogs'].astype(dtype='int')
    rt['NumLogs'] = rtm['NumLogs'].astype(dtype='int')
    rt = rt[(rt['ShiftStart'] > START_DATE) & (rt['ShiftStart'] < END_DATE)]
    rt = rt[rt['Site'] != 'RBHS-Cons']
    rt = rt[rt['Site'] != 'ARC-Disp']
    # rt.head()

    # merge reportTable and shiftTable for Weekdays/ShiftTime

    rt = rt.merge(st, how='left', left_on=['Site', 'ShiftStart', 'ShiftEnd'],
                  right_on=['Location', 'StartTime', 'EndTime'])

    rt = rt[['NetID', 'Site', 'WeekDay', 'ShiftDate', 'ShiftTime', 'ShiftStart', 'ShiftEnd', 'RoundLogs', 'Comments',
             'NumLogs']]
    # rt.head()

    # calculate appropriate threshold

    # rt['test'] = (rt['ShiftEnd']-rt['ShiftStart'])
    # rt['test'] = rt['test'].apply(lambda x: float(x.item()/60000000000))
    # rt['test'] = (rt['test'] /15)*0.5
    # print(rt.dtypes)

    # rt['ThreshLogs'] = (((rt['ShiftEnd']-rt['ShiftStart']) / np.timedelta64(1, 'm')) /15)*0.5     #50% threshold
    # rt['MaxLogs'] = (((rt['ShiftEnd']-rt['ShiftStart']) / np.timedelta64(1, 'm')) /15)
    # rt['PercentDone'] = rt['NumLogs']/rt['MaxLogs']*100

    rt['ThreshLogs'] = (rt['ShiftEnd'].values - rt['ShiftStart'].values)
    rt['ThreshLogs'] = rt['ThreshLogs'].astype('timedelta64[m]')

    rt['ThreshLogs'] = (rt['ThreshLogs'] / 15) * 0.5
    rt['MaxLogs'] = (rt['ShiftEnd'].values - rt['ShiftStart'].values)
    rt['MaxLogs'] = rt['MaxLogs'].astype('timedelta64[m]')
    rt['MaxLogs'] = rt['MaxLogs'] / 15
    rt['PercentDone'] = rt['NumLogs'] / rt['MaxLogs'] * 100

    # # select rows that are below threshold

    rt = rt[rt['NumLogs'] < rt['ThreshLogs']]

    # add notation columns
    rt['Excused?'] = ""
    rt['Notes'] = ""

    # print(len(rt))
    # rt.head()

    rt.to_csv("./thresholdAuditReport_"+START_DATE.strftime('%m_%d')+"--"+END_DATE.strftime('%m_%d')+".csv")
    # rt.to_excel(new_thresh_path, engine='xlsxwriter', index=False)

    print('_____ audit_thresh all done, check SRs folder for output! _____')

    return;

def readCSV():
    stm = pd.read_csv("./ShiftTable.csv", dtype='str')
    stm['StartTime'] = pd.to_datetime(stm['StartTime'])
    stm['EndTime'] = pd.to_datetime(stm['EndTime'])
    rtm = pd.read_csv("./ReportTable.csv", dtype='str', encoding="ISO-8859-1")
    rtm = rtm.drop(['Path', 'Item Type'], axis=1)
    rtm['ShiftStart'] = pd.to_datetime(rtm['ShiftStart'])
    rtm['ShiftEnd'] = pd.to_datetime(rtm['ShiftEnd'])
    rtm.dropna(axis=0, how='all', inplace=True);
    stm.dropna(axis=0, how='all', inplace=True);
    return stm, rtm

if __name__ == '__main__':
    print("Reading CSV...")
    [stm,rtm]=readCSV();
    maxDateRTM = (datetime.strptime(max(rtm["ShiftDate"]),'%m/%d/%Y'))
    minDateRTM = (datetime.strptime(min(rtm["ShiftDate"]),'%m/%d/%Y'))
    [start,end]=getUserInput(minDateRTM,maxDateRTM);
    existence(stm,rtm,start,end)



