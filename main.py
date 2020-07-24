import pandas as pd
import numpy as np
from datetime import datetime, MINYEAR, MAXYEAR
from tempfile import NamedTemporaryFile
import csv
import webbrowser
import shutil
import sys


def getUserInput(minDate, maxDate):
    # get start and end date
    invalidInput = True;
    start = "";
    end = "";
    while (invalidInput):
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
                print("Earliest date is ", minDate.strftime('%m/%d/%Y'))
                invalidInput = True;
    invalidInput = True;
    while (invalidInput):
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
                print("Latest date is ", maxDate.strftime('%m/%d/%Y'))
                invalidInput = True;
            if start > end:
                print("ERROR: End date is larger than start date")
                invalidInput = True;
    return start, end;


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
    missing['Checked'] = ""

    missing.to_csv(
        "./existenceAuditReport_" + START_DATE.strftime('%m_%d') + "--" + END_DATE.strftime('%m_%d') + ".csv")
    # missing.to_excel(new_existen_path,engine='xlsxwriter')

    print('_____ audit_exists all done, check SRs folder for output! _____')
    return;


def threshold(st, rt, START_DATE, END_DATE):
    # audit the REPORT TABLE rt for certain dates
    # uses START_DATE and END_DATE
    rt = rt[~rt['NumLogs'].isnull()]
    rt['NumLogs'] = rt['NumLogs'].astype(dtype='int')
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
    rt['Checked'] = ""

    # print(len(rt))
    # rt.head()

    rt.to_csv("./thresholdAuditReport_" + START_DATE.strftime('%m_%d') + "--" + END_DATE.strftime('%m_%d') + ".csv")
    # rt.to_excel(new_thresh_path, engine='xlsxwriter', index=False)

    print('_____ audit_thresh all done, check SRs folder for output! _____')

    return;


def readCSV():
    try:
        stm = pd.read_csv("./ShiftTable.csv", dtype='str')
    except FileNotFoundError:
        raise FileNotFoundError('ShiftTable.csv')
    except Exception as e:
        raise Exception(e)
    stm['StartTime'] = pd.to_datetime(stm['StartTime'])
    stm['EndTime'] = pd.to_datetime(stm['EndTime'])
    try:
        rtm = pd.read_csv("./ReportTable.csv", dtype='str', encoding="ISO-8859-1")
    except FileNotFoundError:
        raise FileNotFoundError('ReportTable.csv')
    except Exception as e:
        raise Exception(e)
    rtm = rtm.drop(['Path', 'Item Type'], axis=1)
    rtm['ShiftStart'] = pd.to_datetime(rtm['ShiftStart'])
    rtm['ShiftEnd'] = pd.to_datetime(rtm['ShiftEnd'])
    rtm.dropna(axis=0, how='all', inplace=True);
    stm.dropna(axis=0, how='all', inplace=True);
    return stm, rtm

def zedLocationID(loc):
    if loc in ["Busch","ARC-Cons"]:
        return "115"
    if loc in ["ARC-Disp"]:
        return "119"
    if loc in ["BEST-Cons"]:
        return "113"
    if loc in ["RBHS-Cons",'KES-Cons']:
        return "118"
    if loc in ["LSM-Cons"]:
        return "117"
    print ("UNKNOWN LOCATION")
    return "115"

def openWebsites(date1,netID):
    option = "-1";
    while option == "-1":
        option = input("Check Websites (Press ? for help): ")
        if option == "?":
            print('Zed and PTS: 1')
            print('Zed: 2')
            print('PTS: 3')
            print('Connect: 4')
            print('Slack: 5')
            print('All Sites: 6')
            print('Continue without opening websites: 0\n')
            option = "-1"
        if option == "1":
            webbrowser.open("https://zed.rutgers.edu/scheduling/employee/" + netID + "/?start_date=" + date1.strftime("%Y-%m-%d"))
            webbrowser.open(
                "https://sc-apps.rutgers.edu/pts/index.php?q=pts&action=View+User&user_netid=" + netID)
        elif option == "2":
            webbrowser.open("https://zed.rutgers.edu/scheduling/employee/" + netID + "/?start_date=" + date1.strftime("%Y-%m-%d"))
        elif option == "3":
            webbrowser.open(
                "https://sc-apps.rutgers.edu/pts/index.php?q=pts&action=View+User&user_netid=" + netID)
        elif option == '4':
            webbrowser.open("https://connect.rutgers.edu/")
        elif option == '5':
            webbrowser.open_new_tab("https://rutgers.slack.com/")
        elif option == '6':
            webbrowser.open("https://zed.rutgers.edu/scheduling/employee/" + netID + "/?start_date=" + date1.strftime("%Y-%m-%d"))
            webbrowser.open(
                "https://sc-apps.rutgers.edu/pts/index.php?q=pts&action=View+User&user_netid=" + netID)
            webbrowser.open("https://connect.rutgers.edu/")
            webbrowser.open_new_tab("https://rutgers.slack.com/")
        elif option == "0":
            print("", end="")
        else:
            option = "-1"
    option = "-1"

def verifyExistence(start, end):
    print('-----------------------------------------------------------------------------------------------')
    print('SR EXISTENCE AUDIT VERIFICATION')
    print("\nPlease verify each potential incident and PTS accordingly")
    tempCons = NamedTemporaryFile(mode='w',newline="", delete=False)
    fields=['ShiftID_x','Location','WeekDay','StartTime','EndTime','ShiftTime','NetID','Situation','Excused?','Checked']
    forceExit= -1
    tempNetID=""
    ans="que"
    explain=""
    with open(".\\existenceAuditReport_" + start.strftime('%m_%d') + "--" + end.strftime('%m_%d') + ".csv",'r') as csvRead,tempCons:
        existRead = csv.DictReader(csvRead, fieldnames=fields);
        existWrite = csv.DictWriter(tempCons, fieldnames=fields);
        for row in existRead:
            if row['ShiftID_x'] == "ShiftID_x":
                existWrite.writerow(row)
                continue;
            if row['ShiftID_x'] == "":
                print("\nNo Further Existence Incidents to Investigate")
                input("Press ENTER to continue");
                break;
            if forceExit == 0:
                row = {'ShiftID_x': row['ShiftID_x'], 'Location': row['Location'], 'WeekDay': row['WeekDay'],
                       'StartTime': row['StartTime'], 'EndTime': row['EndTime'], 'ShiftTime': row['ShiftTime'],
                       'NetID': row['NetID'], 'Situation': row['Situation'], 'Excused?': row['Excused?'], 'Checked': row['Checked']}
                existWrite.writerow(row)
            else:
                if row['Checked'] != "X":
                    tempDate = datetime.strptime(row['StartTime'], '%Y-%m-%d %H:%M:%S')
                    print('-----------------------------------------------------------------------------------------------')
                    print("\nLocation: ", row['Location'])
                    print("Date: ", row['WeekDay'],",",tempDate.strftime('%m/%d/%Y'))
                    print("Time: ",row['ShiftTime'])
                    webbrowser.open("https://zed.rutgers.edu/scheduling/view/"+zedLocationID(row['Location'])+"/?start_date="+tempDate.strftime('%Y-%m-%d'))
                    tempNetID = input("\nNetID of Shift Owner from Zed (if unknown, enter N/A): ")
                    if tempNetID in ["N/A","n/a"]:
                        explain = input("Input Brief Explanation: ")
                        row = {'ShiftID_x': row['ShiftID_x'], 'Location': row['Location'], 'WeekDay': row['WeekDay'],
                               'StartTime': row['StartTime'], 'EndTime': row['EndTime'], 'ShiftTime': row['ShiftTime'],
                               'NetID': "N/A", 'Situation': explain, 'Excused?': "?", 'Checked': "X"}
                        existWrite.writerow(row)
                        inputExit = input("Press ENTER to continue (type 'EXIT' to exit and save) ")
                        if inputExit.lower() == "exit":
                            forceExit = 0
                    else:
                        openWebsites(tempDate,tempNetID)
                        while ans == "que":
                            ans = input("Is a PTS incident warranted? (Y/N) ")
                            if (ans == "Y" or ans == "y"):
                                explain = input("Input Brief Explanation: ")
                                webbrowser.open(
                                    "https://sc-apps.rutgers.edu/pts/index.php?q=pts&action=Add%20Incident&class_id=1");
                                print("Incident blah blah")
                                row = {'ShiftID_x':row['ShiftID_x'],'Location':row['Location'],'WeekDay':row['WeekDay'],
                                       'StartTime':row['StartTime'],'EndTime':row['EndTime'],'ShiftTime':row['ShiftTime'],
                                       'NetID':tempNetID,'Situation':explain,'Excused?':"",'Checked':"X"}
                                existWrite.writerow(row)
                            elif ans == "N" or ans == "n":
                                explain = input("Input Brief Explanation: ")
                                row = {'ShiftID_x':row['ShiftID_x'],'Location':row['Location'],'WeekDay':row['WeekDay'],
                                       'StartTime':row['StartTime'],'EndTime':row['EndTime'],'ShiftTime':row['ShiftTime'],
                                       'NetID':tempNetID,'Situation':explain,'Excused?':"X",'Checked':"X"}
                                existWrite.writerow(row)
                            else:
                                ans = "que"
                        ans = "que"
                        inputExit = input("Press ENTER to continue (type 'EXIT' to exit and save) ")
                        if inputExit.lower() == "exit":
                            forceExit = 0
                else:
                    row = {'ShiftID_x': row['ShiftID_x'], 'Location': row['Location'], 'WeekDay': row['WeekDay'],
                           'StartTime': row['StartTime'], 'EndTime': row['EndTime'], 'ShiftTime': row['ShiftTime'],
                           'NetID': row['NetID'], 'Situation': row['Situation'], 'Excused?': row['Excused?'],
                           'Checked': row['Checked']}
                    existWrite.writerow(row)
        if forceExit != 0:
            print('-----------------------------------------------------------------------------------------------')
            print("\nNo Further Existence Incidents to Investigate")
            input("Press ENTER to Save and Exit to Menu")
    shutil.move(tempCons.name,".\\existenceAuditReport_" + start.strftime('%m_%d') + "--" + end.strftime('%m_%d') + ".csv")


def verifyThreshold(start, end):
    print('-----------------------------------------------------------------------------------------------')
    print('SR THRESHOLD AUDIT VERIFICATION')
    print("\nPlease verify each potential incident and PTS accordingly")
    ans = "que";
    option = "-1";
    forceExit = -1
    tempDate = datetime.now();
    explain = ""
    tempCons = NamedTemporaryFile(mode='w',newline="", delete=False)
    tempString = "";
    fields = ['ID', 'NetID', 'Site', 'WeekDay', 'ShiftDate', 'ShiftTime', 'ShiftStart', 'ShiftEnd', 'RoundLogs',
              'Comments', 'NumLogs', 'ThreshLogs', 'MaxLogs', 'PercentDone', 'Excused?', 'Notes', 'Checked']
    with open(".\\thresholdAuditReport_" + start.strftime('%m_%d') + "--" + end.strftime('%m_%d') + ".csv",
              'r') as csvRead, tempCons:
        thresRead = csv.DictReader(csvRead, fieldnames=fields);
        thresWrite = csv.DictWriter(tempCons, fieldnames=fields);
        print("\nPlease check ZED, PTS, Connect, and Slack for the following issues:")
        for row in thresRead:
            if row['NetID'] == "":
                print("\nNo Further Threshold Incidents to Investigate")
                input("Press ENTER to continue");
                break;
            if row['ID'] == "":
                thresWrite.writerow(row)
                continue;
            if forceExit == 0:
                row = {'ID': row['ID'], 'NetID': row['NetID'], 'Site': row['Site'], 'WeekDay': row['WeekDay'],
                       'ShiftDate': row['ShiftDate'], 'ShiftTime': row['ShiftTime'], 'ShiftStart': row['ShiftStart'],
                       'ShiftEnd': row['ShiftEnd'], 'RoundLogs': row['RoundLogs'],
                       'Comments': row['Comments'], 'NumLogs': row['NumLogs'], 'ThreshLogs': row['ThreshLogs'],
                       'MaxLogs': row['MaxLogs'], 'PercentDone': row['PercentDone'], 'Excused?': row['Excused?'],
                       'Notes': row['Notes'],
                       'Checked': row['Checked']}
                thresWrite.writerow(row)
            else:
                if row['Checked'] != "X":
                    tempDate = datetime.strptime(row['ShiftDate'], '%m/%d/%Y')
                    print('-----------------------------------------------------------------------------------------------')
                    print("\nNetID: ", row['NetID'])
                    print("Site: ", row['Site'])
                    print("Shift: ", row['WeekDay'], row['ShiftTime'])
                    temp = float(row['PercentDone'])
                    print("Report Percent: {0:.0f}%\n".format(temp))
                    openWebsites(tempDate,row['NetID'])
                    while ans == "que":
                        ans = input("Is a PTS incident warranted? (Y/N) ")
                        if (ans == "Y" or ans == "y"):
                            explain = input("Input Brief Explanation: ")
                            webbrowser.open(
                                "https://sc-apps.rutgers.edu/pts/index.php?q=pts&action=Add%20Incident&class_id=1");
                            print("Incident blah blah")
                            row = {'ID': row['ID'], 'NetID': row['NetID'], 'Site': row['Site'],
                                   'WeekDay': row['WeekDay'], 'ShiftDate': row['ShiftDate'],
                                   'ShiftTime': row['ShiftTime'], 'ShiftStart': row['ShiftStart'],
                                   'ShiftEnd': row['ShiftEnd'], 'RoundLogs': row['RoundLogs'],
                                   'Comments': row['Comments'], 'NumLogs': row['NumLogs'],
                                   'ThreshLogs': row['ThreshLogs'], 'MaxLogs': row['MaxLogs'],
                                   'PercentDone': row['PercentDone'], 'Excused?': '', 'Notes': explain, 'Checked': 'X'}
                            thresWrite.writerow(row)
                        elif ans == "N" or ans == "n":
                            explain = input("Input Brief Explanation: ")
                            row = {'ID':row['ID'], 'NetID':row['NetID'], 'Site':row['Site'], 'WeekDay':row['WeekDay'],
                                   'ShiftDate':row['ShiftDate'], 'ShiftTime':row['ShiftTime'],
                                   'ShiftStart':row['ShiftStart'], 'ShiftEnd':row['ShiftEnd'],
                                   'RoundLogs':row['RoundLogs'],
                  'Comments':row['Comments'], 'NumLogs':row['NumLogs'], 'ThreshLogs':row['ThreshLogs'],
                                   'MaxLogs':row['MaxLogs'], 'PercentDone':row['PercentDone'], 'Excused?':'X',
                                   'Notes':explain, 'Checked':'X'}
                            thresWrite.writerow(row)
                        else:
                            ans = "que"
                    ans = "que"
                    inputExit = input("Press ENTER to continue (type 'EXIT' to exit and save) ")
                    if inputExit.lower() == "exit":
                        forceExit = 0
                else:
                    row = {'ID': row['ID'], 'NetID': row['NetID'], 'Site': row['Site'], 'WeekDay': row['WeekDay'],
                           'ShiftDate': row['ShiftDate'], 'ShiftTime': row['ShiftTime'],
                           'ShiftStart': row['ShiftStart'],
                           'ShiftEnd': row['ShiftEnd'], 'RoundLogs': row['RoundLogs'],
                           'Comments': row['Comments'], 'NumLogs': row['NumLogs'], 'ThreshLogs': row['ThreshLogs'],
                           'MaxLogs': row['MaxLogs'], 'PercentDone': row['PercentDone'], 'Excused?': row['Excused?'],
                           'Notes': row['Notes'],
                           'Checked': row['Checked']}
                    thresWrite.writerow(row)
    if forceExit != 0:
        print('-----------------------------------------------------------------------------------------------')
        print("\nNo Further Threshold Incidents to Investigate")
        input("Press ENTER to Save and Exit to Menu")
    shutil.move(tempCons.name,".\\thresholdAuditReport_" + start.strftime('%m_%d') + "--" + end.strftime('%m_%d') + ".csv")


if __name__ == '__main__':
    print("Welcome to the Shift Report Auditor!!!")
    print("By: epl43, qh63, emo66")
    print("Last Updated: 07/23/2020 emo66")
    userChoice="-1"
    subChoice="-1";
    setDate = True;
    while userChoice == "-1":
        setDate = True;
        print("\n1: Generate Audit Result Files")
        print("2: Verify/Investigate Audit Results")
        print("0: Exit\n")
        userChoice = input("Choose Option Above: ")
        if(userChoice == "1"):
            print('\n-----------------------------------------------------------------------------------------------')
            print("SHIFT REPORT AUDIT GENERATION\n")
            print("The Following Files MUST be in the Same Directory as this Program:")
            print("\tReportTable.csv")
            print("\t\tContains all reports submitted by consultants")
            print("\t\tGo to Sharepoint > Site Contents, click 'Shift Reports' List")
            print("\t\tClick 'Export to Excel' and 'query.iqy' will be downloaded")
            print("\t\tOpen 'query.iqy' in Excel, accept all the settings as is, then sign into Connect as prompted.")
            print("\t\tSave as 'ReportTable.csv and save in the same folder as this program")
            print("\tShiftTable.csv")
            print("\t\tContains all shifts that are recorded from Zed for Shift Report Powerapp")
            print("\t\tGo to Sharepoint > Documents > Round Log Audits > ShiftTable.xlsx")
            print("\t\tOpen 'shiftTable.xlsx' with Excel and save as ShiftTable.csv")
            print("\t\tSave 'ShitTable.csv in the same folder as this program")
            input("\nPress ENTER to continue\n")
            print("Reading CSVs...")
            try:
                [stm, rtm] = readCSV();
            except FileNotFoundError as e:
                print(e, " is not found")
                input("Press ENTER to return to menu")
                userChoice = "-1"
                continue
            except Exception as e:
                print("UNKNOWN ERROR")
                print(e)
                input("Press ENTER to exit")
                exit(1)
            maxDateRTM = (datetime.strptime(max(rtm["ShiftDate"]), '%m/%d/%Y'))
            minDateRTM = (datetime.strptime(min(rtm["ShiftDate"]), '%m/%d/%Y'))
            [start, end] = getUserInput(minDateRTM, maxDateRTM);
            print("\n1: Run Existence Audit")
            print("2: Run Threshold Audit")
            print("3: Run Both Audits")
            print("0: Return To Menu\n")
            subChoice = "-1"
            while subChoice == "-1":
                subChoice = input("Choose Option Above: ")
                if subChoice == "1" or subChoice == "3":
                    try:
                        existence(stm,rtm,start,end)
                    except FileNotFoundError as e:
                        print (e," is not found")
                        input("Press ENTER to return to menu")
                        userChoice = "-1"
                        break;
                    except Exception as e:
                        print("UNKNOWN ERROR")
                        print(e)
                        input("Press ENTER to exit")
                        exit(1)
                if subChoice == "2" or subChoice == "3":
                    threshold(stm,rtm,start,end)
            if subChoice in ["1","2","3"]:
                print(
                    '\n-----------------------------------------------------------------------------------------------')
                subChoice = input("Do you want to Verify These Audits? (Y/N) ")
                if subChoice in ["Y","y"]:
                    setDate = False
                    userChoice = "2"
                else:
                    setDate = True
                    userChoice = "-1"
        if(userChoice == "2"):
            print('\n-----------------------------------------------------------------------------------------------')
            print("SR AUDIT MANUAL VERIFICATION\n")
            if setDate:
                print("Ensure that all audits you want to verify are in this folder")
                input("\nPress ENTER to continue\n")
            subChoice = "-1"
            while subChoice == '-1':
                if setDate:
                    [start, end] = getUserInput(datetime.min, datetime.max)
                    setDate = False
                print("\n1: Check Existence Audit")
                print("2: Check Threshold Audit")
                print("0: Return To Menu\n")
                subChoice = input("Choose Option Above: ")
                if subChoice == "1":
                    try:
                        verifyExistence(start,end)
                    except FileNotFoundError as e:
                        print("Existence Audit from",start.strftime('%m_%d') + " to " + end.strftime('%m_%d'),"not found")
                        input("Press ENTER to continue")
                        subChoice = "-1"
                        setDate=True
                    except Exception as e:
                        print("UNKNOWN ERROR")
                        print(e)
                        input("Press ENTER to exit")
                        exit(1)
                if subChoice == "2":
                    try:
                        verifyThreshold(start,end)
                    except FileNotFoundError as e:
                        print("Threshold Audit from",start.strftime('%m_%d') + " to " + end.strftime('%m_%d'),"not found")
                        input("Press ENTER to continue")
                        subChoice = "-1"
                        setDate=True
                    except Exception as e:
                        print("UNKNOWN ERROR")
                        print(e)
                        input("Press ENTER to exit")
                        exit(0)
                if subChoice in ["1","2"]:
                    print(
                        '\n-----------------------------------------------------------------------------------------------')
                    subChoice = input("Do you want to verify another audit? (Y/N) ")
                    if subChoice in ["y","Y"]:
                        subChoice = input("Do you want to change the date? (Y/N) ")
                        if subChoice in ["Y","y"]:
                            setDate = True
                        else:
                            setDate = False
                        subChoice = "-1"
                    else:
                        subChoice = "0"
                        setDate = True
                        userChoice = "-1"
        if(userChoice == "0"):
            break;
        else:
            userChoice = "-1"

