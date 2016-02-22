# encoding=utf-8


import re
import os
import sys
import codecs
import time
import datetime
import getopt
import math
import mysql.connector

TIME_SPLIT_MASK_OFFSET = 8
ERROR_MASK_OFFSET = 16
TIME_REG_EXP = r'^\d{8}-\d{6}-\w: '
LOG_REG_EXP = TIME_REG_EXP + r'(\[[ \w-]+\])?( <(\w+):\w+>)?(.+)$'
DATABASE_INFO_EXP = r'(\w+):?(\w*)@(.[^:]+):?(\w*)/(\w+)$'
UNKNOWN_TYPE = "unknown"

class ErrorCatcher:
    count = {}
    detail = {}
    fileCount = 0
    path = ''
    beginTime = 0
    databaseInfo = ''
    tableName = ''
    version = ''
    
    def writeResult(self):
        sortedList = sorted(self.count.items(), key=lambda e:e[1], reverse=True)
        if self.databaseInfo != '':
            match = self.databaseRegExp.findall(self.databaseInfo)
            user = match[0][0]
            password = match[0][1]
            host = match[0][2]
            database = match[0][4]
            if match[0][3] != '':
                port = int(match[0][3])
            else:
                port = None

        if user == '' or host == '' or database == '':
            print("user, host or database can't be empty!example: root:password@127.0.0.1:334/database")
            exit()

        if port == None:
            conn = mysql.connector.connect(user=user, passwd=password, host=host, db=database)
        else:
            conn = mysql.connector.connect(user=user, passwd=password, host=host, port=port, db=database)

        cur  = conn.cursor(buffered=True)
        
        sql  = "create table if not exists " + self.tableName + "(errorid varchar(200) primary key, logLevel varchar(1), count int, detail longtext);"
        cur.execute(sql)
        conn.commit()
        
        print("write to DB...")
        for value in sortedList:
            detail = self.detail[value[0]]
            detail = detail.replace('"', "'")
            logLevel = detail[ERROR_MASK_OFFSET]
            sql = 'insert into ' + self.tableName + ' values ("' + str(value[0]) + '",' + '"' + logLevel + '", '+ str(value[1]) + ', "' + detail + '"' + ') on duplicate key update count=count+' + str(value[1])
            cur.execute(sql)
            conn.commit() 
        conn.close()
        
        print("write to file...")
        result = ''
        for value in sortedList:
            line = str(value[1]) + '\t' + self.detail[value[0]]
            result += line
        #writeFile = open('ErrorLog-' + time.strftime("%Y%m%d-%H%M%S") + '.txt', 'w')
        fileName = self.tableName + '_' + self.version + '_Version_' + time.strftime("%Y%m%d-%H%M%S") + '.txt'
        fileName = os.path.join(self.tableName, fileName)
        writeFile = codecs.open(fileName , 'w', 'utf-8', 'ignore')
        try:
            writeFile.write(result)
        finally:
            writeFile.close()
            
    def prosessFile(self, fileName):
        self.fileCount += 1;
        
        try:
            readFile = codecs.open(fileName, 'r', 'utf-8', 'ignore')
            lines = readFile.readlines()
        finally:
            readFile.close();
            
        logDetail = None
        errorType = None
        lineIndex = 0
        lineCount = len(lines)
        for line in lines:
            lineIndex += 1

            sys.stdout.write("match line " + str(lineIndex) + "/" + str(lineCount) + " ... " + str(round(lineIndex * 100 / lineCount , 2)) + "%\t\t\r")

            if errorType != None and logDetail != None:
                match = self.timeRegExp.findall(line)
                if not match:
                    logDetail += line
                    continue
                else:
                    if errorType in self.count:
                        self.count[errorType] += 1
                    else:
                        self.count.setdefault(errorType, 1)
                        self.detail.setdefault(errorType, logDetail)

            if len(line) > ERROR_MASK_OFFSET and line[TIME_SPLIT_MASK_OFFSET] == "-" and line[ERROR_MASK_OFFSET - 1] == "-" and (line[ERROR_MASK_OFFSET] == "E" or line[ERROR_MASK_OFFSET] == "W"):
                match = self.logRegExp.findall(line)
                if not match:
                    print("Parse log failed: " + line + " at file " + fileName + "@" + str(lineIndex))
                    exit(0)

                logDetail = line
                errorType = match[0][2]
                if errorType == None or errorType == '':
                    errorType = match[0][1]
                if errorType == None or errorType == '':
                    errorType = match[0][0]
                if errorType == None or errorType == '':
                    errorType = match[0][3]
                if errorType in self.count:
                    self.count[errorType] += 1
                    logDetail = None
                    errorType = None

        if logDetail != None:
            self.count.setdefault(errorType, 1)
            self.detail.setdefault(errorType, logDetail)
        
    def traverse(self, path):
        if not path:
            return False
        if not os.path.exists(path):
            print("error path " + path)
            return False
        if os.path.isfile(path):
            currentTime = time.time() + 0.01
            speed = math.floor(self.fileCount / (currentTime - self.beginTime) * 100) / 100
            print("parse file " + str(self.fileCount) + " " + path + " with speed " + str(speed) + "/s.")
            self.prosessFile(path)
        if os.path.isdir(path):
            print("walk path " + path)
            fileNameList = os.listdir(path)
            for fileName in fileNameList:
                fileName = path + '/' + fileName
                self.traverse(fileName)
            return True
    
    def go(self):
        self.logRegExp = re.compile(LOG_REG_EXP)
        self.timeRegExp = re.compile(TIME_REG_EXP)
        self.databaseRegExp = re.compile(DATABASE_INFO_EXP)
        
        self.traverse(self.path)
        
if __name__ == '__main__':
    myErrorCatcher = ErrorCatcher()
    
    if len(sys.argv) < 2:
        print('please enter path!')
        exit()
    if os.path.isdir(sys.argv[1]):
        myErrorCatcher.path = sys.argv[1]
    else:
        print('Path Error! Please check path!' + sys.argv[1])
        exit()
    
    begin_time = time.time()
    myErrorCatcher.beginTime = begin_time
    print('error catcher working ... ')
    opts, arg = getopt.getopt(sys.argv[2:], 'd:t:v:')
    for op, value in opts:
        if op == '-d':
            myErrorCatcher.databaseInfo = value
        if op == '-t':
            myErrorCatcher.tableName = value
        if op == '-v':
            myErrorCatcher.version = value
    try:
        myErrorCatcher.go()
    except:
        raise
    finally:
        myErrorCatcher.writeResult()
    
    end_time = time.time()
    cost_second = int(end_time - begin_time)
    
    print("process " + str(myErrorCatcher.fileCount) + " files.")
    print("cost time " + str(cost_second) + "s.")
    print('Done!')

