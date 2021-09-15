import xml.etree.ElementTree
import xml.etree.ElementTree as et
import zipfile
import os
import shutil
import random
import copy
import re
class openAdproFile():

    def __init__(self, filePath):
        #print("\n\nProductivity Suite Toolkit Rev 0 by Strantor 8/2/2021\n\n")
        self.filePath = filePath
        self.fileName = self.filePath.split('/')[-1]
        L,R = filePath.split(".adpro")
        #L2 = L.split('\\')
        L2 = L.split('/')
        self.projectfolder = L.rstrip(L2[-1])
        self.folder = L +"_Extract/"
        self.rllPath = self.folder + "task/"

        print("unpacking adpro contents of",self.fileName,"to", self.folder)
        zf = zipfile.ZipFile(self.filePath)
        zf.extractall(self.folder)
        print(self.fileName,"successfully unpacked")
        self.content = adcXML(self.folder)


    def rePackAdpro(self,saveAs=None, cleanup=False):
        """
        if saveAs == None:
            path = self.folder
            newFileName = self.projectfolder + self.fileName.split('.adpro')[0]+"_Mod.adpro"
        else:
            newFileName = saveAs.split('/')[-1]
            L,R = saveAs.split(".adpro")
            L2 = L.split('/')
            path = L.rstrip(L2[-1])
        """
        path = self.folder
        if saveAs == None:
            newFileName = self.projectfolder + self.fileName.split('.adpro')[0]+"_Mod.adpro"
        else:
            newFileName = saveAs
        print("path: ",path,", newFileName: ",newFileName)

        zipf = zipfile.ZipFile(newFileName, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(path):#os.walk(path):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file),
                                    os.path.join(path, '....')))
        zipf.close()
        if cleanup == True:
            try:
                shutil.rmtree(self.folder)
            except OSError as e:
                print ("Error: %s - %s." % (e.filename, e.strerror))

class adcXML():

    def __init__(self,folder):
        self.uniqueIDs = []
        self.folder = folder
        self.tags = self.getTags(folder)
        self.tasks = self.getTasks(folder)

        print(self.tasks)

    def getTags(self,path):
        self.tagsTree = et.parse(path + "program.tag")
        self.tagsRoot = self.tagsTree.getroot()

    def getTasks(self,path):
        path = path + "task/"
        print("searching tasks...")
        resultNo = 0
        tasks = os.listdir(path)
        results = []

        for task in tasks:
            result = {}
            taskpath = path + task
            result["path"] = taskpath
            result["xml"] = self.assignIDs(taskpath)
            self.saveRLL(taskpath,result["xml"])
            progName = result["xml"].find('pgmName').text
            result["name"] = progName
            result["taskFileName"] = task
            results.append(result)
        return results

    def printTree(self,tree):
        def recurPrint(data, dots=""):
            for child in data:
                print(dots, [child.tag,child.text,str(child.attrib)])
                recurPrint(child, dots + "..")
        recurPrint(tree)

    def statusOutput(self,text,forReal=False):
        if forReal == True:
            print(text)

    def returnTree(self,tree):
        linelist = []
        text = ""
        def recurPrint(data, dots=""):
            for child in data:
                linelist.append(dots + str([child.tag,child.text,str(child.attrib)]))
                recurPrint(child, dots + "..")
        recurPrint(tree,"..")

        for line in linelist:
            text += line
            text += "\n"
        return text

    def unNestDict(self, input, thisTier=0,maxTier=10):
        thisTier += 1
        op = ""
        for key, val in input.items():
            op += "\n" + (".." * (thisTier-1)) + (str(key) + ":  ")
            if isinstance(val, dict):
                if thisTier+1<=maxTier:
                    nextTier = self.unNestDict(val, thisTier,maxTier)
                    op += str(nextTier[0])
                else:
                    op += "{dict}"
            else:
                op += str(val)
        if thisTier == 1:
            return op
        else:
            return op, thisTier

    def getUniqueID(self):
        randy = random.randint(1, 99999999)
        randy = str(randy).zfill(8)
        if randy in self.uniqueIDs:
            randy = self.getUniqueID()
        return randy

    def recurMark(self, data, parentID=None):
        for child in data:
            my_ID = self.getUniqueID()
            child.set("my_ID",my_ID)
            #child.set("parent_Tag",data.tag)
            #child.set("parent_ID",parentID)
            self.recurMark(child, my_ID)

    def assignIDs(self,task):
        thisTree = et.parse(task)
        thisRoot = thisTree.getroot()
        rootID = self.getUniqueID()
        thisRoot.set("my_ID",rootID)
        self.recurMark(thisRoot,rootID)
        return thisTree

    def formatTagDisplayName(self, tagObject):
        for item in self.tagsRoot.iter("item"):
            id = item.find('./tagSystemId/sysId').text
            if id == tagObject["tagName"]:
                print(item.find("tagName").text)
        return tagObject["tagName"]

    def copyRung(self,file,rungNo):
        rungNo = str(int(rungNo))
        rungs = file.findall("rungs")
        rungsToCopy = []
        lastRung = 0
        for rung in rungs:
            lastRung = rung.find("rungNumber").text
            if lastRung == rungNo:
                rungsToCopy.append(rung)
        lastRung = str(int(lastRung)+1)
        program = file.getroot()
        for rung in rungsToCopy:
            newRung = copy.deepcopy(rung)
            newRung.find("rungNumber").text = lastRung
            #newRung.set("my_ID",self.getUniqueID())
            #self.recurMark(newRung)
            program.append(newRung)
        return lastRung

    def searchRungsForDisplay(self,file):
        rungs = file["xml"].findall('rungs')
        rungDataList = []
        for rung in rungs:
            thisRung = self.searchRLLelement(rung,None)
            rungDataList.append(thisRung)
        return rungDataList

    def sequentialRungCopy(self, file, firstRungNo, howMany):
        firstRungNo = str(firstRungNo-1)
        file = file["xml"]
        newFirstRungNo = self.copyRung(file,firstRungNo)
        for rungCopy in range(1,howMany):
            self.copyRung(file,firstRungNo)
        secondRungNo = str((int(firstRungNo)+1))
        rungs = file.findall('rungs')
        # subrungs are stored in RLL files as rungs, so there might be 15 different <rungs> elements for a single
        # rung. So we make two list of all the <rungs> elements having a <rungNumber> equal to that of the first and
        # second seed rung
        firstRungs = []
        secondRungs = []
        for rung in rungs:
            thisRungNo = rung.find("rungNumber").text
            if thisRungNo == firstRungNo:
                firstRungs.append(rung)
            elif thisRungNo == secondRungNo:
                secondRungs.append(rung)
        frResultList = [] # temporary list to store all the {dict} items returned above
        for rung in firstRungs:
            frResultList.append(self.searchRLLelement(rung,None))
        # now create a dictionary where all of these individual search results will be combined into
        frResults = {}
        for result in frResultList:
            for k,v in result.items():
                # in the end we want two separate dictionaries; one for the first seed rung and one for the second
                # seed rung, and we want them to have identical keys so that we can compare the values. So we use a
                # combination of Rung # and ladder column # to form a new key for the results dictionary (previously
                # the key of the search result was its unique XML ID).
                newKey = str(v["ladderRungNoDisp"]) + "_" + str(v["ladderColumnNoDisp"])
                frResults[newKey] = v
                srResultList = []
        for rung in secondRungs:
            srResultList.append(self.searchRLLelement(rung,None))
        srResults = {}
        for result in srResultList:
            for k,v in result.items():
                if "." in v["ladderRungNoDisp"]:
                    # for the second seed rung dictionary we need to further modify the dictionry key, subtracting one
                    # from the run number, so that the keys from dictionary 2 will match the keys from dictionary 1
                    modifiedRungNo = v["ladderRungNoDisp"].split(".")
                    modifiedRungNo[0] = str(int(modifiedRungNo[0])-1)
                    modifiedRungNo = modifiedRungNo[0] + "." + modifiedRungNo[1]
                else:
                    modifiedRungNo = str(int(v["ladderRungNoDisp"])-1)
                newKey = str(modifiedRungNo) + "_" + str(v["ladderColumnNoDisp"])
                srResults[newKey] = v
        #print("results:",self.unNestDict(srResults))
        #print(frResultList)
        try: # check first rung against 2nd rung and 2nd rung against first rung for inconsistencies
            for k,v in frResults.items():
                if frResults[k]["ladderInstruction"] != srResults[k]["ladderInstruction"]:
                    raise KeyError(k)
                apple = frResults[k]
                banana = srResults[k]
            for k,v in frResults.items():
                apple = frResults[k]
                banana = srResults[k]
        except KeyError as e:
            rung,col = str(e).strip("'").split("_")
            self.statusOutput("rungs not equivalent! Check Rung " + rung + ", column " + col + ".")


        newTags = {}
        for k,v in frResults.items():
            # handle incrementing simple tagnames like
            # (DI-0.1.1.1 -> DI-0.1.1.3 -> DI-0.1.1.5) or
            # (Conveyor 2 run -> Conveyor 3 run -> Conveyor 4 run)
            if v['tagName'] != srResults[k]['tagName']:
                n1 = v['tagName']
                n2 = srResults[k]['tagName']
                n3 = self.incrementBasicTagName(v['tagName'],srResults[k]['tagName'])
                newTags[k] = v
                newTags[k]['tagName'] = n3
                newTags[k]["nameSequence"] = {}
                newTags[k]["sysIDSequence"] = {}
                newTags[k]["nameSequence"]["i"] = 3
                newTags[k]["nameSequence"]["1"] = n1
                newTags[k]["sysIDSequence"]["1"] = v['tagID']
                newTags[k]["nameSequence"]["2"] = n2
                newTags[k]["sysIDSequence"]["2"] = srResults[k]['tagID']
                newTags[k]["nameSequence"]["3"] = n3
                newTags[k]["sysIDSequence"]["3"] = self.incrementBasicTagID(srResults[k]['tagID'], n3)
            else:
                if 'array' in v:
                    newTags[k] = self.incrementArrayTag(v, srResults[k])
                else:
                    if 'BOW' in v:
                        newTags[k] = v
                        bitDiff = int(srResults[k]['BOW']['bit']) - int(v['BOW']['bit'])
                        nextBit = int(srResults[k]['BOW']['bit']) + bitDiff
                        newTags[k]['BOW']={}
                        newTags[k]['BOW']['bit'] = str(nextBit)
                        newTags[k]['BOW']['prevBit'] = srResults[k]['BOW']['bit']


        rungs = file.findall("rungs")
        newFirstRungNo = int(newFirstRungNo)
        for newRungNo in range(newFirstRungNo,newFirstRungNo+howMany):
            for rung in rungs:
                if rung.find("rungNumber").text == str(newRungNo):
                    for data in rung.iter("data"):
                        for k,v in newTags.items():
                            if data.attrib['my_ID'] == v['tagXML_ID']:
                                if 'array' not in v:
                                    if 'BOW' in v:
                                        #print(v['BOW']['prevBit'],v['BOW']['bit'])
                                        bitDiff = int(v['BOW']['bit']) - int(v['BOW']['prevBit'])
                                        nextBit = int(v['BOW']['bit']) + bitDiff
                                        v['BOW']['prevBit'] = v['BOW']['bit']
                                        v['BOW']['bit'] = nextBit
                                        #print(v['BOW']['prevBit'],v['BOW']['bit'])
                                        data.find('./indexTagRef/data/constValue/value').text = str(nextBit)
                                        data.find('./indexTagRef/data/constText').text = str(nextBit)
                                    else:
                                        i = v["nameSequence"]["i"]
                                        newName = v["nameSequence"][str(i)]
                                        newID = v["sysIDSequence"][str(i)]
                                        nextName = self.incrementBasicTagName(v["nameSequence"][str(i-1)],v["nameSequence"][str(i)])
                                        nextID = self.incrementBasicTagID(newID, nextName)
                                        i+=1
                                        v["nameSequence"]["i"] = i
                                        v["nameSequence"][str(i)] = nextName
                                        v["sysIDSequence"][str(i)] = nextID
                                        data.find("name").text = newName
                                        data.find("ID").text = newID
                                else:
                                    if "BOW" in v:
                                        newBit = v['BOW']['bit']
                                        data.find('./indexTagRef/data/constValue/value').text = newBit
                                        data.find('./indexTagRef/data/constText').text = newBit
                                        newCol = v["array"]['col']
                                        data.find('./baseTagRef/data/colTagRef/data/constText').text = newCol
                                        data.find('./baseTagRef/data/colTagRef/data/constValue/value').text = newCol
                                        if 'row' in v["array"]:
                                            newRow = v["array"]['row']
                                            data.find('./rowTagRef/data/constText').text = newRow
                                            data.find('./rowTagRef/data/constValue/value').text = newRow
                                    else:
                                        newCol = v["array"]['col']
                                        data.find('./colTagRef/data/constText').text = newCol
                                        data.find('./colTagRef/data/constValue/value').text = newCol
                                        if 'row' in v["array"]:
                                            newRow = v["array"]['row']
                                            data.find('./rowTagRef/data/constText').text = newRow
                                            data.find('./rowTagRef/data/constValue/value').text = newRow
                                    nextTag = self.incrementArrayTag(v)
                                """
                                try:
                                    file.write('test.xml')
                                    print("it worked")
                                    workedBeforeThat = lastThatWorked
                                    lastThatWorked = v
                                except:
                                    if failedOnce == False:
                                        print("worked before last", workedBeforeThat)
                                        self.printTree(workedBeforeThat['tag'])
                                        print("last workd", lastThatWorked)
                                        self.printTree(lastThatWorked['tag'])
                                        print("failed on", v)
                                        self.printTree(v['tag'])
                                        failedOnce = True
                                """
        self.tagsTree.write(self.folder + "program.tag")

    def searchTags(self, searchFor):
        for item in self.tagsRoot.iter("item"):
            tag_name = item.find('tagName').text
            if searchFor == tag_name:
                self.printTree(item)


    def incrementArrayTag(self, firstTag, secondTag=None):
        if secondTag == None:
            a1col = firstTag['array']['prevCol']
            a2col = firstTag['array']["col"]
            if "row" in firstTag['array']:
                a1row = firstTag['array']['prevRow']
                a2row = firstTag['array']["row"]
            if "BOW" in firstTag:
                a1bit = firstTag["BOW"]["prevBit"]
                a2bit = firstTag["BOW"]["bit"]
        else:
            a1col = firstTag['array']["col"]
            a2col = secondTag['array']["col"]
            if "row" in firstTag['array']:
                a1row = firstTag['array']["row"]
                a2row = secondTag['array']["row"]
            if "BOW" in firstTag:
                a1bit = firstTag["BOW"]["bit"]
                a2bit = secondTag["BOW"]["bit"]
        colDiff = int(a2col) - int(a1col)
        a3col = str(int(a2col) + colDiff)
        newTag = firstTag
        newTag['array']['col'] = a3col
        newTag['array']['prevCol'] = a2col
        if "row" in firstTag['array']:
            rowDiff = int(a2row) - int(a1row)
            a3row = str(int(a2row) + rowDiff)
            newTag['array']['row'] = a3row
            newTag['array']['prevRow'] = a2row
        if "BOW" in firstTag:
            bowDiff = int(a2bit) - int(a1bit)
            a3bit = str(int(a2bit) + bowDiff)
            newTag["BOW"]["bit"] = a3bit
            newTag["BOW"]["prevBit"] = a2bit
        for item in self.tagsRoot.iter("item"):
            tag_name = item.find('tagName').text
            if firstTag['tagName'] == tag_name:
                found = True
                id = item.find('./tagSystemId/sysId').text
                cols = item.find('./initValue/cols').text
                if "BOW" in firstTag:
                    l,n = id.split("-")
                    if "16" in l:
                        if int(a3bit) > 16:
                            newTag["BOW"]["bit"] = "16"
                            newTag["BOW"]["prevBit"] = "16"
                            self.statusOutput("Bit of Word bit exceeds tag bits("+tag_name+").")
                    if "32" in l:
                        if int(a3bit) > 32:
                            newTag["BOW"]["bit"] = "32"
                            newTag["BOW"]["prevBit"] = "32"
                            self.statusOutput("Bit of Word bit exceeds tag bits("+tag_name+").")
                if int(a3col) > int(cols):
                    item.find('./initValue/cols').text = a3col
                    dims = item.findall('./initValue/value/dimensions')
                    dims[0].text = a3col
                    item.find('./initValue/value/dataTabs/count').text = a3col
                if "row" in firstTag['array']:
                    rows = item.find('./initValue/rows').text
                    if int(a3row) > int(rows):
                        item.find('./initValue/rows').text = a3row
                        dims = item.findall('./initValue/value/dimensions')
                        dims[1].text = a3row
                    rows = int(item.find('./initValue/rows').text)
                    cols = int(item.find('./initValue/cols').text)
                    count = str(rows*cols)
                    item.find('./initValue/value/dataTabs/count').text = count
        return newTag


    def incrementBasicTagName(self, firstRung,secondRung):
        tn1 = firstRung
        tn2 = secondRung
        tn1Parse = self.parseNumbers(tn1)
        tn2Parse = self.parseNumbers(tn2)
        tn3Parse = []
        for i in range(0,len(tn1Parse)):
            if tn1Parse[i] == tn2Parse[i]:
                tn3Parse.append(tn1Parse[i])
            else:
                if type(tn1Parse[i]) == int:
                    diff = tn2Parse[i] - tn1Parse[i]
                    tn3Parse.append(tn2Parse[i]+diff)
                else:
                    self.statusOutput("incompatible tag ("+tn1+") vs ("+tn2+").")
        tn3 = ""
        for part in tn3Parse:
            tn3 += str(part)
        return tn3

    def incrementBasicTagID(self, lastKnownAddress, tagName):
        found = False
        for item in self.tagsRoot.iter("item"):
            tag_name = item.find('tagName').text
            if tagName == tag_name:
                found = True
                id = item.find('./tagSystemId/sysId').text
                ret = id
        if found == False:
            letter,number = lastKnownAddress.split("-")
            if letter in ["DI","DO","MST"]:
                numList = number.split(".")
                numList[3] = int(numList[3])+1
                newNum = letter+"-"+numList[0]+"."+numList[1]+"."+numList[2]+"."+str(numList[3])
                ret = lastKnownAddress
                self.statusOutput("cannot create new hardware tags ("+newNum+") that don't exist")
            else:
                for item in self.tagsRoot.iter("item"):
                    id = item.find('./tagSystemId/sysId').text
                    if id == lastKnownAddress:
                        newItem = copy.deepcopy(item)
                nLast = 0
                for item in self.tagsRoot.iter("item"):
                    id = item.find('./tagSystemId/sysId').text
                    l,n = id.split("-")
                    if l not in ["DI","DO","MST"]:
                        if l == letter:
                            n = int(n)
                            if n > nLast:
                                nLast = n
                newId = letter+"-"+str(nLast+1).zfill(6)
                newItem.find('./tagSystemId/sysId').text = newId
                newItem.find('tagName').text = tagName
                ret = newId
                tags = self.tagsRoot.find("tags")
                tags.append(newItem)
        return ret

    def parseNumbers(self, s):
        numbers = '0123456789'
        stringList = []
        text = ''
        number = ''
        lastWasNumber = False
        lastWasText = False
        for c in s:
            if c in numbers:
                lastWasNumber = True
                if lastWasText == True:
                    stringList.append(text)
                    lastWasText = False
                    text = ''
                number += c
            else:
                lastWasText = True
                if lastWasNumber == True:
                    stringList.append(int(number))
                    number = ''
                    lastWasNumber = False
                text += c
        if lastWasNumber == True:
            stringList.append(int(number))
        if lastWasText == True:
            stringList.append(text)
        return stringList

    def searchRLLelement(self,tree,searchTerm=None):
        results = {}
        for dataTag in tree.iter("data"):
            name = dataTag.find("name")
            if name != None:
                if searchTerm != None:
                    if name.text == searchTerm:
                        result = self.identifyTag(tree,dataTag)
                        results[result["tagXML_ID"]] = result
                else:
                    #print(name.text)
                    result = self.identifyTag(tree,dataTag)
                    results[result["tagXML_ID"]] = result
                    #print(result,result["tagXML_ID"])
        #print(self.unNestDict(results))
        return results

    def getAncestor(self, tree, tag, ancestor):
        while tag.tag != ancestor:
            tag = tree.find(".//"+tag.tag+'[@my_ID="'+tag.attrib["my_ID"]+'"]...')
        return tag

    def getRungNo(self,rung):
        rungNo = int(rung.find('rungNumber').text)
        subrungNo = int(rung.find('subRungNumber').text)
        if subrungNo == 0:
            rungNoDisp = str(rungNo+1)
        else:
            rungNoDisp = str(rungNo+1)+"."+str(subrungNo)
        return rungNoDisp

    def identifyTag(self,tree, tag):
        result = {}
        try:
            # this will throw an exception if 'arrayTagRef' is not found higher up in the tree,
            # which means this is not an array tag
            parentDataTag = self.getAncestor(tree,tag,'arrayTagRef')
            # if the above does not throw an exception then 'arrayTagRef' IS found,
            # so we set the tag to be the 'data' tag parent of 'arrayTagRef'

            try:
                # if the above worked, then this IS an array tag, so we check further to see if it's a Bit of Word array tag.
                # this will throw an exception if 'baseTagRef' is not found higher up in the tree,
                # which means this is not a bit of word array tag
                parentDataTag = self.getAncestor(tree,tag,'baseTagRef')
                # If 'baseTagRef' is found, go one level higher to the top level "data"
                tag = tree.find(".//"+parentDataTag.tag+'[@my_ID="'+parentDataTag.attrib["my_ID"]+'"]...')
                result["tag"] = tag
                result["tagXML_ID"] = tag.get('my_ID')
                result["tagName"] = tag.find("./baseTagRef/data/arrayTagRef/data/name").text
                result["tagID"] = tag.find("./baseTagRef/data/arrayTagRef/data/ID").text
                result["array"] = {}
                result["array"]["col"] = tag.find('./baseTagRef/data/colTagRef/data/constValue/value').text
                result["BOW"] = {}
                result["BOW"]["bit"] = tag.find('./indexTagRef/data/constValue/value').text
                try:
                    # this will throw an exception if 'rowTagRef' is not found as a child like 'colTagRef',
                    # which means this is not a 2D array tag
                    result["array"]["row"] = tag.find('./baseTagRef/data/rowTagRef/data/constValue/value').text
                except:
                    pass

            except:
                #this is an ordinary array tag, not a bit of word
                tag = tree.find(".//"+parentDataTag.tag+'[@my_ID="'+parentDataTag.attrib["my_ID"]+'"]...')
                result["tag"] = tag
                result["tagXML_ID"] = tag.get('my_ID')
                result["tagName"] = tag.find("./arrayTagRef/data/name").text
                result["tagID"] = tag.find("./arrayTagRef/data/ID").text
                result["array"] = {}
                result["array"]["col"] = tag.find('./colTagRef/data/constValue/value').text
                try:
                    # this will throw an exception if 'rowTagRef' is not found as a child like 'colTagRef',
                    # which means this is not a 2D array tag
                    result["array"]["row"] = tag.find('./rowTagRef/data/constValue/value').text
                except:
                    pass
        except:
            #  it's not an array tag
            try:
                #but is it a bit of word tag?
                parentDataTag = self.getAncestor(tree,tag,'baseTagRef')
                tag = tree.find(".//"+parentDataTag.tag+'[@my_ID="'+parentDataTag.attrib["my_ID"]+'"]...')
                result["tagXML_ID"] = tag.get('my_ID')
                result["tagName"] = tag.find("./baseTagRef/data/name").text

                result["tagID"] = tag.find("./baseTagRef/data/ID").text
                result["BOW"] = {}
                result["BOW"]["bit"] = tag.find('./indexTagRef/data/constValue/value').text
                result["tag"] = tag

            except:
                # nope. just a plain ol tag
                result["tagXML_ID"] = tag.get('my_ID')
                result["tagName"] = tag.find("name").text
                result["tagID"] = tag.find("ID").text
                result["tag"] = tag


        # Starting with the input tag, Iterate up the tree to find the parent
        # object ('elements') which contains the ladder column position
        ladderElement = self.getAncestor(tree,tag,'elements')
        result["ladderColumnNoDisp"] = int((int(ladderElement.find("position").text)+1)/2)
        result["ladderColumnNo"] = ladderElement.find("position").text
        result["ladderInstruction"] = ladderElement.find("instruction"). \
            get("{http://www.w3.org/2001/XMLSchema-instance}type"). \
            lstrip("adcInst")
        # From the ('elements') tag, continue iterating up the tree to find the parent
        # object ('rungs') which contains the ladder row/rung position
        ladderRung = self.getAncestor(tree,ladderElement,'rungs')
        result["ladderRungNoDisp"] = self.getRungNo(ladderRung)
        result["ladderRungNo"] = ladderRung.find("rungNumber").text
        result["ladderSubRungNo"] = ladderRung.find("subRungNumber").text
        #result["displayName"] = self.formatTagDisplayName(result)
        return result

    def searchAllRLLfiles(self, searchTerm=None):
        results = {}
        for task in self.tasks:
            tree = task["xml"]
            root = tree.getroot()
            for dataTag in root.iter("data"):
                name = dataTag.find("name")
                if name != None:
                    if searchTerm != None:
                        if name.text == searchTerm:
                            result = self.identifyTag(tree,dataTag)
                            results[result["tagXML_ID"]] = result
                    else:
                        result = self.identifyTag(tree,dataTag)
                        results[result["tagXML_ID"]] = result
        return results

    def saveRLL(self,path,data):
        print("saveRLL",path,data)
        root = data.getroot()
        root.set("xmlns:xs","http://www.w3.org/2001/XMLSchema")
        data.write(path)


def main():
    #project = openAdproFile("sample1.adpro")
    project = openAdproFile("Z:/PSuite Project Python/sample1.adpro")
    c = project.content

    #c.searchTags("MultiDim Array")

    searchResults = c.searchAllRLLfiles("DI-0.1.1.2")
    #print(c.unNestDict(searchResults))
    #c.copyRung(c.tasks[0],1)
    sresults = c.searchRungsForDisplay(c.tasks[0])
    #for result in sresults:
    #    print(c.unNestDict(result))
    c.sequentialRungCopy(c.tasks[0], 1, 3)

    #c.searchTags("MultiDim Array")

    #searchResults = c.searchRLL("Array Bit")
    #print(c.unNestDict(searchResults))
    #searchResults = project.c.searchRLL("MultiDim Array")
    #print(project.c.unNestDict(searchResults))
    c.saveRLL(c.tasks[0]["path"],c.tasks[0]["xml"])
    project.rePackAdpro()

if __name__ == '__main__':
    main()