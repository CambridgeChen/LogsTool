import os
import re
import time
import datetime
import zipfile
import getopt
import sys
import shutil
import mysql.connector

DATABASE_INFO_EXP = r'(\w+):?(\w*)@(.[^:]+):?(\w*)/(\w+)$'

class LogProcessor:
    ignorePathList = []
    
    logsPath = ''
    ignorePathString = ''
    databaseInfo = ''

    def pack(self, packDirectory, zipFilePath, zipFileName):
        zipFileName = zipFileName + ".zip"
        zipFileName = os.path.join(zipFilePath, zipFileName)

        if not os.path.exists(zipFilePath):
            os.mkdir(os.path.join('.', zipFilePath))

        if os.path.exists(zipFileName):
            print("file: " + zipFileName + " is already exists!Please check again!")
            return

        myZipFile = zipfile.ZipFile(zipFileName, "w", zipfile.ZIP_DEFLATED)
        
        logFileNameList = os.listdir(packDirectory)

        try:
            for logFileName in logFileNameList:
                info = os.path.join(packDirectory, logFileName)
                if os.path.isfile(info):
                    myZipFile.write(info, logFileName)
        finally:
            myZipFile.close()
        
        try:
            myZipFile = zipfile.ZipFile(zipFileName, "r", zipfile.ZIP_DEFLATED)

            errorFileName =  myZipFile.testzip()
        finally:
            myZipFile.close()
            
        if errorFileName == None:
            #shutil.rmtree(packDirectory)
            return True
        else:
            print("pack into zip file error!file name: " + errorFileName)
            return False


    def getSubdirectoryList(self, path):
        subdirectoryList = []
        fileNameList = os.listdir(path)
        for fileName in fileNameList:
            if os.path.isdir(os.path.join(path, fileName)):
                subdirectoryList.append(fileName)
        return subdirectoryList
    
    def go(self):
        
        self.initialise()
        
        todayStr = time.strftime('%Y_%m_%d')
        logSubdirectoryList = self.getSubdirectoryList(self.logsPath)
        for subdirectory in logSubdirectoryList:
            if subdirectory in self.ignorePathList:
                continue
            serverSubdirectoryList = self.getSubdirectoryList(os.path.join(self.logsPath, subdirectory))
            for serverSubdirectory in serverSubdirectoryList:
                if serverSubdirectory < todayStr:
                    curDir = os.path.join(self.logsPath, subdirectory, serverSubdirectory)
                    if not os.path.exists(curDir):
                        continue
            
                    command = "python " + "ErrorCatcher.py " + curDir
                    command += " -d " + self.databaseInfo
                    command += " -t " + subdirectory
                    command += " -v " + serverSubdirectory
                    os.system(command)
            
                    self.pack(curDir, subdirectory, serverSubdirectory)
    
    def tryConnectDB(self):
        databaseRegExp = re.compile(DATABASE_INFO_EXP)
        match = databaseRegExp.findall(self.databaseInfo)
        
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
            conn = mysql.connector.connect(user=user, passwd=password, host=host)
        else:
            conn = mysql.connector.connect(user=user, passwd=password, host=host, port=port)

        cur  = conn.cursor(buffered=True)

        sql = "create database if not exists " + database + ";"
        cur.execute(sql)
        sql = "use " + database + ";"
        cur.execute(sql)
        conn.commit()

        conn.close()
        print("DB connection's ok!")

    def initialise(self):
        self.ignorePathList = self.ignorePathString.split(',')
        self.tryConnectDB()
    
if __name__ == '__main__':
    logProcessor = LogProcessor();
    
    if len(sys.argv) < 2:
        print('please enter logs path!')
        exit()
    if os.path.isdir(sys.argv[1]):
        logProcessor.logsPath = sys.argv[1]
    else:
        print('Path Error! Please check path!')
        exit()
    
    opts, arg = getopt.getopt(sys.argv[2:], 'd:i:')
    for op, value in opts:
        if op == '-d':
            logProcessor.databaseInfo = value
        if op == '-i':
            logProcessor.ignorePathString = value
    
    logProcessor.go()