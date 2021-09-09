import xml.etree.ElementTree as ET
from tabulate import tabulate
import time
import zipfile
import os
import shutil

def unNestDict(input, thisTier=0,maxTier=10):
    thisTier += 1
    op = ""
    for key, val in input.items():
        op += "\n" + (".." * (thisTier-1)) + (str(key) + ":  ")
        if isinstance(val, dict):
            if thisTier+1<=maxTier:
                nextTier = unNestDict(val, thisTier,maxTier)
                op += str(nextTier[0])
            else:
                op += "{dict}"
        else:
            op += str(val)
    if thisTier == 1:
        return op
    else:
        return op, thisTier

class importTags():

    def __init__(self, tagfilePath):

        with open(tagfilePath) as f:
            csv_list = [[val.strip() for val in r.split(",")] for r in f.readlines()]

            (_, *header), *data = csv_list
            csv_dict = {}
            for row in data:
                key, *values = row
                csv_dict[key] = {key: value for key, value in zip(header, values)}
        self.csv_dict = csv_dict


    def searchFor(self,searchString):
        self.searchResults = {}
        for key, val in self.csv_dict.items():
        # Key, Value (EX.) =
        # AR2S32-000002(2)(5) :
        #   {
        #       'Tag Name': '"Conveyor(2).Timers(5).Reset"',
        #       'Retentive Mode': 'FALSE',
        #       'Initial Value': '"0"',
        #       ...}

            try:
                val["Tag Name"] = val["Tag Name"].lstrip('"').rstrip('"')
                if searchString in val["Tag Name"]:
                    newEntry = {}
                    addr = key
                    name = val["Tag Name"]
                    nameParts = name.split(".")
                    name = ""
                    for part in nameParts:
                        part = part.split("(")
                        name += part[0]
                        name += "."
                    name = name.rstrip(".")
                    #print(name)
                    # Detect 2D array
                    if ")(" in addr:
                        #print("2d")
                        L,R = addr.split(")(")
                        addr,row = L.split("(")
                        col = R.rstrip(")")
                    else:
                        #print("1d")
                        # 1D array
                        addr,col = addr.split("(")
                        col = col.rstrip(")")
                        row = None
                    newEntry["Name"] = name.lstrip('"').rstrip('"')
                    newEntry["ID"] = addr
                    newEntry["Row"] = row
                    newEntry["Col"] = col
                    newEntry["TagDB_SystemID"] = key
                    self.searchResults[val["Tag Name"]] = newEntry
            except:
                pass
        return self.searchResults

class rllTask():

    def __init__(self,xmlPath):
        self.xmlPath = xmlPath

        self.tree = ET.parse(self.xmlPath)
        self.root = self.tree.getroot()
        self.properLine = '<Program xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xs="http://www.w3.org/2001/XMLSchema">'


    def searchRll(self, searchTerms):
        #print(searchTerms)
        sweepNo = 0
        hitNo = 0
        hits = {}
        progName = self.root.find('pgmName').text
        print("Task Name:",progName)
        for key,val in searchTerms.items():
            searchTerm = val
            for rung in self.root.iter('rungs'):
                rungNo = rung.find('rungNumber').text
                for instr in rung.iter('instruction'):
                    instrTxt = instr.get("{http://www.w3.org/2001/XMLSchema-instance}type").lstrip("adcInst")
                    for data in instr.iter('data'):
                        dataType = data.get("{http://www.w3.org/2001/XMLSchema-instance}type")
                        if dataType == 'adcArrayTag':
                            arrayTagCol = None
                            arrayTagRow = None
                            sweepNo +=1
                            arrayTagRef = data.iter("arrayTagRef")
                            for tagData in arrayTagRef:
                                arrayTagData = tagData.iter("data")
                                for reallyDeeplyNestedThing1 in arrayTagData:
                                    arrayTagName = reallyDeeplyNestedThing1.find("name").text
                                    arrayTagID = reallyDeeplyNestedThing1.find("ID").text
                            colTagRef = data.iter("colTagRef")
                            for tagData in colTagRef:
                                arrayTagData = tagData.iter("data")
                                for reallyDeeplyNestedThing2 in arrayTagData:
                                    try:
                                        arrayTagCol = reallyDeeplyNestedThing2.find("constText").text
                                        # NOTE The Column number is stored twice and will need to be changed twice
                                        # 1st in <constText> and then in <constValue>\<value>
                                    except:
                                        pass
                            rowTagRef = data.iter("rowTagRef")
                            for tagData in rowTagRef:
                                arrayTagData = tagData.iter("data")
                                for reallyDeeplyNestedThing3 in arrayTagData:
                                    try:
                                        arrayTagRow = reallyDeeplyNestedThing3.find("constText").text
                                        # NOTE The Column number is stored twice and will need to be changed twice
                                        # 1st in <constText> and then in <constValue>\<value>
                                    except:
                                        pass


                            if searchTerm["Name"] in arrayTagName:
                                if searchTerm["Row"] == arrayTagRow and \
                                    searchTerm["Col"] == arrayTagCol:
                                        #print(arrayTagName,arrayTagCol,arrayTagRow,searchTerm["Col"],searchTerm["Row"])
                                        hit = {}
                                        hit["sweepNo"] = sweepNo
                                        hit["instructionType"] = instrTxt
                                        hit["rungNumber"] = rungNo
                                        hit["Name"] = arrayTagName
                                        hit["ID"] = arrayTagID
                                        hit["Col"] = arrayTagCol
                                        hit["Row"] = arrayTagRow
                                        hitNo += 1
                                        key = str(hitNo) #"Hit # " + str(hitNo)
                                        hits[key] = hit

                            #results[resultNo] = result
        return(hits)
        #print(unNestDict(hits))

    def replaceRll(self, searchTerms, replaceTerms):
        #print(unNestDict(replaceTerms))
        sweeplist = []
        for k,v in replaceTerms.items():
            sweeplist.append(v['sweepNo'])
        #print(sweeplist)
        sweepNo = 0
        hitNo = 0
        hits = {}
        progName = self.root.find('pgmName').text
        print("Task Name:",progName)

        for key,val in searchTerms.items():
            searchTerm = val
            for rung in self.root.iter('rungs'):
                rungNo = rung.find('rungNumber').text
                for instr in rung.iter('instruction'):
                    instrTxt = instr.get("{http://www.w3.org/2001/XMLSchema-instance}type").lstrip("adcInst")
                    for data in instr.iter('data'):
                        dataType = data.get("{http://www.w3.org/2001/XMLSchema-instance}type")
                        if dataType == 'adcArrayTag':
                            arrayTagCol = None
                            arrayTagRow = None
                            sweepNo +=1
                            if sweepNo in sweeplist:
                                for k,v in replaceTerms.items():
                                    if v['sweepNo'] == sweepNo:
                                        #print(sweepNo)
                                        #print(replaceTerms[k])
                                        replacementTag = replaceTerms[k]
                                arrayTagRef = data.iter("arrayTagRef")
                                for tagData in arrayTagRef:
                                    arrayTagData = tagData.iter("data")
                                    for reallyDeeplyNestedThing1 in arrayTagData:
                                        arrayTagName = reallyDeeplyNestedThing1.find("name")
                                        arrayTagName.text = replacementTag['Name']
                                        arrayTagID = reallyDeeplyNestedThing1.find("ID")
                                        arrayTagID.text = replacementTag['ID']
                                colTagRef = data.iter("colTagRef")
                                for tagData in colTagRef:
                                    arrayTagData = tagData.iter("data")
                                    for reallyDeeplyNestedThing2 in arrayTagData:
                                        arrayTagCol = reallyDeeplyNestedThing2.find("constText")
                                        arrayTagCol.text = replacementTag['newCol']
                                        arrayTagCol2 = reallyDeeplyNestedThing2.find("constValue")
                                        ridiculouslyDeeplyNestedThing2 = arrayTagCol2.find("value")
                                        #print(ridiculouslyDeeplyNestedThing2.text)
                                        ridiculouslyDeeplyNestedThing2.text = replacementTag['newCol']
                                        #print(ridiculouslyDeeplyNestedThing2.text)
                                        # NOTE The Column number is stored twice and will need to be changed twice
                                        # 1st in <constText> and then in <constValue>\<value>
                                rowTagRef = data.iter("rowTagRef")
                                for tagData in rowTagRef:
                                    arrayTagData = tagData.iter("data")
                                    for reallyDeeplyNestedThing3 in arrayTagData:
                                        if replacementTag["Row"] != None:
                                            arrayTagRow = reallyDeeplyNestedThing3.find("constText")
                                            arrayTagRow.text = replacementTag['newRow']
                                            arrayTagRow3 = reallyDeeplyNestedThing3.find("constValue")
                                            ridiculouslyDeeplyNestedThing3 = arrayTagRow3.find("value")
                                            ridiculouslyDeeplyNestedThing3.text = replacementTag['newRow']
        self.tree.write(self.xmlPath)
        with open(self.xmlPath, 'r') as buggeredFile:
            buggeredText = buggeredFile.read()
            properText = buggeredText.replace('<Program xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',self.properLine)
        with open(self.xmlPath,'w') as fixedFile:
            fixedFile.write(properText)




class arraySearchReplace():

    def __init__(self,csvPath,rllPath,searchFor,replaceWith):
        self.tagDB = importTags(csvPath)
        self.tagsToBeReplaced = self.tagDB.searchFor(searchFor)
        #print("Tags to be replaced:")
        #print(unNestDict(self.tagsToBeReplaced))
        self.tagReplacements = self.tagDB.searchFor(replaceWith)
        #print("\n\nTags will be replaced with:")
        #print(unNestDict(self.tagReplacements))
        self.task = rllTask(rllPath)
        self.searchHits = self.task.searchRll(self.tagsToBeReplaced)
        #print(unNestDict(self.searchHits))
        table = self.comparisonTable(self.searchHits)

    def comparisonTable(self, searchHits,startover=False):
        #print(unNestDict(data))
        #print(unNestDict(self.tagReplacements))
        if startover == False:
            table = [['Hit #', 'Found in Rung', 'Instruction Type', 'Tag Name','OLD TagDB System ID', 'NEW TagDB System ID','sweep']]
            for k,v in searchHits.items():
                #print(k,v)
                for k2,v2 in self.tagReplacements.items():
                    if v['Name'] == v2['Name']:
                        if v['Row'] == None:
                            v['newCol'] = v2['Col']
                            v['newRow'] = None
                        else:
                            if v['Col'] == v2['Col']:
                                v['newCol'] = v2['Col']
                                v['newRow'] = v2['Row']

                v = self.formatTagDB(v)
                row = [k,
                       v['rungNumber'],
                       v['instructionType'],
                       v['Name'],
                       v['formattedID'],v['newFormattedID'],v['sweepNo']]
                table.append(row)
            #table = [["Sun",696000,1989100000],["Earth",6371,5973.6],["Moon",1737,73.5],["Mars",3390,641.85]]
            print(tabulate(table, tablefmt="grid"))
        response = input("How to proceed? \n'A' = Replace ALL instances in the above table\n"
                 "'E' = Exclude (you want to replace all but a few)\n"
                 "'I' = Include (you want to leave most alone and replace only a few)\n"
                 "'C' = Cancel")
        if response in ['e',"E"]:
            excludeList = input("Type the hit #s you want to exclude, separated by commas")
            excludeList = excludeList.split(",")
            cont = True
            errlist = []
            for exclusion in excludeList:
                if exclusion not in searchHits.keys():
                    errlist.append(exclusion)
                    cont = False
            if cont == True:
                for exclusion in excludeList:
                    del(searchHits[exclusion])
            else:
                print("the following hit numbers from the exclusion list were not recognized:\n",
                      errlist,'\nPlease try again')
                time.sleep(5)
            self.comparisonTable(searchHits)
        elif response in ['i',"I"]:
            includeList = input("Type the hit #s you want to include, separated by commas")
            print("\n\nGenerating new search & replace list...")
            includeList = includeList.split(",")
            cont = True
            errlist = []
            for inclusion in includeList:
                if inclusion not in searchHits.keys():
                    errlist.append(inclusion)
                    cont = False
            if cont == True:
                for i in range(1,len(searchHits)+1):
                    if str(i) not in includeList:
                        del searchHits[str(i)]
            else:
                print("the following hit numbers from the inclusion list were not recognized:\n",
                      errlist,'\nPlease try again')
                time.sleep(5)

            self.comparisonTable(searchHits)
        elif response in ['c',"C"]:
            print("Fine, your loss. Guess you don't want to be PRODUCTIVE today...")
        elif response in ['a',"A"]:
            self.task.replaceRll(self.tagsToBeReplaced,searchHits)
        else:
            print("Entry not recognized, try again")
            self.comparisonTable(searchHits,startover=True)

    def formatTagDB(self,input):
        if input['Row'] == None:
            input['formattedID'] = input["ID"] + '(' + input['Col'] + ')'
            input['newFormattedID'] = input["ID"] + '(' + input['newCol'] + ')'
        else:
            input['formattedID'] = input["ID"] + '(' + input['Row'] + ')(' + input['Col'] + ')'
            input['newFormattedID'] = input["ID"] + '(' + str(input['newRow']) + ')(' + str(input['newCol']) + ')'
        return input

class openAdproFile():

    def __init__(self, filePath,searchFor,replaceWith):
        print("\n\nProductivity Suite Toolkit Rev 0 by Strantor 8/2/2021\n\n")
        self.searchFor = searchFor
        self.replaceWith = replaceWith
        self.filePath = filePath
        self.fileName = self.filePath.split('\\')[-1]
        #print(self.fileName)
        L,R = filePath.split(".adpro")
        L2 = L.split('\\')
        self.projectfolder = L.rstrip(L2[-1])
        self.csvPath = L + "_Basic.csv"
        self.folder = L +"_Extract\\"
        #print(self.folder)
        #print(self.csvPath)
        self.rllPath = self.folder + "task\\"

        print("unpacking adpro contents of",self.fileName,"to", self.folder)
        zf = zipfile.ZipFile(self.filePath)
        zf.extractall(self.folder)
        print(self.fileName,"successfully unpacked")
        self.chooseOperation()

    def chooseOperation(self):
        operation = input("which operation would you like to perform?\n"
                          "1 = Array find/replace\n"
                          "2 = incremental copy/paste\n"
                          "3 = renaming operations not supported by PSuite\n"
                          "HINT: Choose #1, it's the only operation currently supported")
        print("\n\nStarting Array find/replace operation...")
        self.getTasks()

    def getTasks(self):
        print("searching tasks...")
        resultNo = 0
        tasks = os.listdir(self.rllPath)
        results = {}

        for task in tasks:
            resultNo += 1
            result = {}
            taskpath = self.rllPath + task
            result["path"] = taskpath
            tree = ET.parse(taskpath)
            root = tree.getroot()
            progName = root.find('pgmName').text
            result["name"] = progName
            result["taskFileName"] = task
            #print(progName)
            results[str(resultNo)] = result
        #print(unNestDict(results))
        self.taskSearchResults = results
        self.listTasks()

    def listTasks(self):

        table = [['Result #','Task Name','File Name']]
        for k,v in self.taskSearchResults.items():
            row = [str(k),v['name'],v["taskFileName"]]
            table.append(row)
        print(tabulate(table, tablefmt="grid"))
        response = input("How to proceed? \n'A' = Search/Replace tags in ALL tasks in the above table\n"
                         "'E' = Exclude (you want to search/replace within all but a few of the tasks)\n"
                         "'I' = Include (you want to leave most of the tasks alone and search/replace only within a few of them)\n"
                         "'C' = Cancel")
        if response in ['e',"E"]:
            excludeList = input("Type the result #s you want to exclude, separated by commas")
            excludeList = excludeList.split(",")
            cont = True
            errlist = []
            for exclusion in excludeList:
                if exclusion not in self.taskSearchResults.keys():
                    errlist.append(exclusion)
                    cont = False
            if cont == True:
                for exclusion in excludeList:
                    del(self.taskSearchResults[exclusion])
            else:
                print("the following result numbers from the exclusion list were not recognized:\n",
                      errlist,'\nPlease try again')
                time.sleep(5)
            self.listTasks()
        elif response in ['i',"I"]:
            includeList = input("Type the result #s you want to include, separated by commas")
            print("\n\nGenerating new task list...")
            includeList = includeList.split(",")
            cont = True
            errlist = []
            for inclusion in includeList:
                if inclusion not in self.taskSearchResults.keys():
                    errlist.append(inclusion)
                    cont = False
            if cont == True:
                for i in range(1,len(self.taskSearchResults)+1):
                    if str(i) not in includeList:
                        del self.taskSearchResults[str(i)]
            else:
                print("the following result numbers from the inclusion list were not recognized:\n",
                      errlist,'\nPlease try again')
                time.sleep(5)

            self.listTasks()
        elif response in ['c',"C"]:
            print("Fine, your loss. Guess you don't want to be PRODUCTIVE today...")
        elif response in ['a',"A"]:
            #self.task.replaceRll(self.tagsToBeReplaced,searchHits)
            #print(self.taskSearchResults)
            for task in self.taskSearchResults.items():
                self.searchAndReplace(task)
            self.rePackAdpro()
        else:
            print("Entry not recognized, try again")
            self.listTasks()

    def searchAndReplace(self, task):
        #print(task)
        taskName = task[1]['name']
        rllPath = task[1]['path']
        print("\n\nperforming Search & Replace on Task: ", taskName)
        snr = arraySearchReplace(self.csvPath, rllPath, self.searchFor,self.replaceWith)

    def rePackAdpro(self):
        path = self.folder
        fileChoice = input("Create new file ('N') or overwrite original file ('O')?")
        if fileChoice in ['O','o','n','N']:
            if fileChoice in ['O','o']:
                newFileName = self.filePath
            elif fileChoice in ['n','N']:
                newFileName = self.projectfolder + self.fileName.split('.adpro')[0]+"_Mod.adpro"

            zipf = zipfile.ZipFile(newFileName, 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(path):
                for file in files:
                    zipf.write(
                        os.path.join(root, file),
                        os.path.relpath(os.path.join(root, file),
                                        os.path.join(path, '....')))
            zipf.close()
            try:
                shutil.rmtree(self.folder)
            except OSError as e:
                print ("Error: %s - %s." % (e.filename, e.strerror))



if __name__ == "__main__":
    #myProject = openAdproFile("Z:\\G\\PSuite Project Python\\New folder (3)\\Conv1-4.2.zip")
    searchfor = "Conveyor(7)"
    replacewith = "Conveyor(1)"
    pathToProject = "sample1.adpro"
    myProject = openAdproFile(pathToProject,searchfor,replacewith)


    #csvPath = "Z:\\G\\PSuite Project Python\\New folder (3)\\Conv1-4.2_Basic.csv"
    #rllPath = "Z:\\G\\PSuite Project Python\\New folder (3)\\unzip\\task\\T2.rll"
    #searchfor = "Conveyor(1)"
    #replacewith = "Conveyor(2)"
    #searchAndReplace = arraySearchReplace(csvPath, rllPath, searchfor,replacewith)

