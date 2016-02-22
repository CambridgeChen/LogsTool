import os
import re
import sys
import codecs
import time
import datetime
import getopt
import math
import mysql.connector

DATABASE_INFO_EXP = r'(\w+):?(\w*)@(.[^:]+):?(\w*)/(\w+)$'

class PlayerLogSender:
    databaseInfo = ''
    logsPath = ''
    fileCount = 0
    beginTime = 0

    def sendLogs2DB(self, fileName):
        self.fileCount += 1
        if self.port == None:
            conn = mysql.connector.connect(user=self.user, passwd=self.password, host=self.host, db=self.database)
        else:
            conn = mysql.connector.connect(user=self.user, passwd=self.password, host=self.host, port=self.port, db=self.database)

        cur  = conn.cursor()

        try:
            readFile = codecs.open(fileName, 'r', 'utf-8', 'ignore')
            lines = readFile.readlines()
        finally:
            readFile.close();

        lineCount = len(lines)
        lineIndex = 0
        for line in lines:
            lineIndex += 1

            sys.stdout.write("process line " + str(lineIndex) + "/" + str(lineCount) + " ... " + str(round(lineIndex * 100 / lineCount , 2)) + "%\t\t\r")
            values = line.split('\t')
            if len(values) != 7:
                print("file:" + fileName + "with line " + str(lineIndex) + "error!")
                continue

            gotException = False

            sql = 'insert into playerlogs(select from_unixtime(' + values[0] + '),' + values[1] + ',' + values[2] + ',"' +  values[3] + '","' +  values[4] + '",' +  values[5] + ',"' +  values[6] + '");' 
            try:
                cur.execute(sql)
            except:
                gotException = True
            finally:
                for i in range(0, len(values)):
                    if values[i] == 'nil':
                        values[i] = '0'
                sql = 'insert into playerlogs(select from_unixtime(' + values[0] + '),' + values[1] + ',' + values[2] + ',"' +  values[3] + '","' +  values[4] + '",' +  values[5] + ',"' +  values[6] + '");' 
            
            if gotException:
                try:
                    cur.execute(sql)
                except:
                    print("got exception with line " + str(lineIndex) + "sql:" + sql)

            if lineIndex % 100 == 0:
                conn.commit()
        
        conn.commit()
        conn.close()
            
    def getSubdirectoryList(self, path):
        subdirectoryList = []
        fileNameList = os.listdir(path)
        for fileName in fileNameList:
            if os.path.isdir(os.path.join(path, fileName)):
                subdirectoryList.append(fileName)
        return subdirectoryList

    def tryConnectAndInitDB(self):
        databaseRegExp = re.compile(DATABASE_INFO_EXP)
        match = databaseRegExp.findall(self.databaseInfo)
        
        self.user = match[0][0]
        self.password = match[0][1]
        self.host = match[0][2]
        self.database = match[0][4]
        if match[0][3] != '':
            self.port = int(match[0][3])
        else:
            self.port = None

        if self.user == '' or self.host == '' or self.database == '':
            print("user, host or database can't be empty!example: root:password@127.0.0.1:334/database")
            exit()

        if self.port == None:
            conn = mysql.connector.connect(user=self.user, passwd=self.password, host=self.host)
        else:
            conn = mysql.connector.connect(user=self.user, passwd=self.password, host=self.host, port=self.port)

        cur  = conn.cursor(buffered=True)

        sql = "create database if not exists " + self.database + ";"
        ret = cur.execute(sql)
        sql = "use " + self.database + ";"
        ret = cur.execute(sql)
        conn.commit()

        sql = 'DROP TABLE IF EXISTS `playerlogs`;'
        cur.execute(sql)

        sql = '''CREATE TABLE `playerlogs` 
            (
                  `TIME` datetime DEFAULT NULL,
                  `GROUP` int(11) DEFAULT NULL,
                  `ROLE_ID` int(11) DEFAULT NULL,
                  `ACCOUNT` varchar(45) DEFAULT NULL,
                 `ROLE_NAME` varchar(45) DEFAULT NULL,
                 `HERO_TEMPLATE` int(11) DEFAULT NULL,
                 `CONTENT` varchar(256) DEFAULT NULL
            )
            ENGINE=InnoDB DEFAULT CHARSET=utf8;
            '''
        cur.execute(sql)
        conn.commit()
        conn.close()
        print("DB connection's ok!")

    def go(self):
        self.tryConnectAndInitDB()

        logSubdirectoryList = self.getSubdirectoryList(self.logsPath)
        for subdirectory in logSubdirectoryList:
            curdir = os.path.join(self.logsPath, subdirectory)
            fileNameList = os.listdir(curdir)
            for fileName in fileNameList:
                curFile = os.path.join(curdir, fileName)
                if os.path.isfile(curFile):
                    currentTime = time.time() + 0.01
                    speed = math.floor(self.fileCount / (currentTime - self.beginTime) * 100) / 100
                    print("parse file " + str(self.fileCount) + " " + fileName + " with speed " + str(speed) + "/s.")
                    self.sendLogs2DB(curFile)

if __name__ == '__main__':
    playerLogSender = PlayerLogSender()

    if len(sys.argv) < 2:
        print('please enter playerLogs path!')
        exit()
    if os.path.isdir(sys.argv[1]):
        playerLogSender.logsPath = sys.argv[1]
    else:
        print('Path Error! Please check path!')
        exit()
    
    opts, arg = getopt.getopt(sys.argv[2:], 'd:')
    for op, value in opts:
        if op == '-d':
            playerLogSender.databaseInfo = value

    begin_time = time.time()
    playerLogSender.beginTime = begin_time
    print('playerlog sender working ... ')
    playerLogSender.go()