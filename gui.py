#https://www.youtube.com/watch?v=dqg0L7Qw3ko
from PyQt5.QtCore import *
import PyQt5.QtCore as QtCore
from PyQt5.QtGui import *
import sys
from PyQt5.uic import loadUi

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem, QTreeWidget, QTreeView, QWidget, QVBoxLayout, QFileSystemModel
import xml.etree.ElementTree as et
import xmlFuncs
import traceback

class importedGUI(QtWidgets.QMainWindow):#, myGUI):
    def __init__(self, *args, **kwargs):
        # Import settings from settings File
        params = open('parameters','r')
        for line in params:
            if ':' in line:
                parameter,value = line.split('::')
                garbage, parameter = parameter.split('[')
                value, garbage  = value.split(']')
                print("self." + parameter + " ==",value)
                setattr(self,parameter,value) # this assigns new attributes to the importedGUI class
        params.close()
        super(importedGUI, self).__init__(*args, **kwargs)
        loadUi("toolkitUI.ui",self)
        self.show()

        self.model = QFileSystemModel()
        self.model.setNameFilters(['*.adpro'])
        self.model.setRootPath('')
        self.model.setNameFilterDisables(False)
        self.treeView.setModel(self.model)


        self.treeView.setAnimated(False)
        self.treeView.setIndentation(20)
        self.treeView.setSortingEnabled(True)
        self.treeView.setColumnWidth(0,400)


        self.treeWidget.setColumnCount(3)
        self.treeWidget.setHeaderLabels(["tag","text","attributes"])
        self.treeWidget.setColumnWidth(0,300)
        self.treeWidget_2.setColumnWidth(1,400)


        self.treeWidget_2.setColumnCount(3)
        self.treeWidget_2.setHeaderLabels(["tag","text","attributes"])
        #self.treeWidget_2.setColumnWidth(0,50)
        self.treeWidget_2.setColumnWidth(0,300)
        self.treeWidget_2.setColumnWidth(1,400)

        self.treeWidget_3.setColumnCount(3)
        self.treeWidget_3.setColumnWidth(0,300)
        self.treeWidget_3.setColumnWidth(1,400)

        self.treeWidget_3.setHeaderLabels(["tag","text","attributes"])

        self.pushButton.clicked.connect(self.searchXML)#(self.searchFor)
        self.pushButton_3.clicked.connect(self.openFile)
        self.treeView.doubleClicked.connect(self.openFile)
        self.treeView.clicked.connect(self.setSaveLocation)


        self.tab0Text = self.tabWidget.tabText(self.tabWidget.indexOf(self.tab))
        #self.tab1Text = self.tabWidget.tabText(self.tabWidget.indexOf(self.tab_1))
        self.tab2Text = self.tabWidget.tabText(self.tabWidget.indexOf(self.tab_2))
        self.tab3Text = self.tabWidget.tabText(self.tabWidget.indexOf(self.tab_3))
        self.tab4Text = self.tabWidget.tabText(self.tabWidget.indexOf(self.tab_4))
        self.tab5Text = self.tabWidget.tabText(self.tabWidget.indexOf(self.tab_5))
        self.tab6Text = self.tabWidget.tabText(self.tabWidget.indexOf(self.tab_6))
        self.tabWidget.removeTab(5)
        self.tabWidget.removeTab(4)
        self.tabWidget.removeTab(3)
        self.tabWidget.removeTab(2)
        self.tabWidget.removeTab(1)
        self.disregardNameChange = False
        self.project = None
        self.lineEdit_2.textChanged.connect(self.evalSavePath)
        self.pushButton_5.setEnabled(False)
        self.pushButton_5.clicked.connect(self.saveFile)
        #self.pushButton_3.setEnabled(False)
        self.pushButton_2.clicked.connect(self.startSeqRungCopy)
        self.treeWidget_4.clicked.connect(self.evalRungCopyDisplay)
        self.treeWidget_4.setColumnCount(11)
        tw4Cols = ["Rung#"]
        for i in range(1,11):
            self.treeWidget_4.setColumnWidth(i,120)
            tw4Cols.append("Column " + str(i))
        self.treeWidget_4.setHeaderLabels(tw4Cols)
        self.treeWidget_5.setColumnCount(2)
        self.treeWidget_5.setHeaderLabels(["Task Name","File"])
        self.treeWidget_5.setSortingEnabled(True)
        self.treeWidget_5.setColumnWidth(0,300)
        self.treeWidget_5.clicked.connect(self.populateSeqRungList)
        self.lineEdit_4.setText("1")
        self.lineEdit_4.textChanged.connect(self.evalRungCopyNoTxt)
        self.rungCopySelected = None
        self.pushButton_2.setEnabled(False)
        self.taskForCopy = None

        self.appendStatus("Productivity Suite Toolkit Rev 1 by Strantor 9/14/2021")
        self.goToLastDir()

    def saveFile(self):
        try:
            for i in range(0,len(self.c.tasks)):
                self.c.saveRLL(self.c.tasks[i]["path"],self.c.tasks[i]["xml"])
            self.c.tagsTree.write(self.c.folder + "program.tag")
            self.project.rePackAdpro(cleanup=False, saveAs=self.lineEdit_2.text())
        except:
            self.outputError()

    def startSeqRungCopy(self):
        try:
            if self.rungCopySelected != None and self.taskForCopy != None:
                numcopies = int(self.lineEdit_4.text())
                task = self.c.tasks[int(self.taskForCopy)]
                #print(task, self.rungCopySelected, numcopies)
                fb = self.c.sequentialRungCopy(task, int(self.rungCopySelected), numcopies)
                self.appendStatus(fb)
        except:
            self.outputError()

    def outputError(self):
        a,b,c = sys.exc_info()
        er = traceback.format_exception(a,b,c)
        erTxt = ""
        for line in er:
            erTxt += line
        print(erTxt)
        self.appendStatus(erTxt)


    def evalRungCopyNoTxt(self):
        def is_integer(n):
            try:
                float(n)
            except ValueError:
                return False
            else:
                return float(n).is_integer()
        if is_integer(self.lineEdit_4.text()) and self.rungCopySelected != None:
                self.pushButton_2.setEnabled(True)
        else:
            self.pushButton_2.setEnabled(False)

    def evalRungCopyDisplay(self):
        try:
            root = self.treeWidget_4.invisibleRootItem()
            model = self.treeWidget_4.model()
            rungQty = root.childCount()
            checkedRungs = 0
            for i in range(rungQty):
                rungItem = root.child(i) #QTreeWidgetItem
                if rungItem.checkState(0) == Qt.Checked:
                    checkedRungs +=1
            if checkedRungs == 0:
                self.rungCopySelected = None
                for i in range(rungQty):
                    rungItem = root.child(i) #QTreeWidgetItem
                    rungItem.setDisabled(False)
                    for col in range (0,11):
                        bgColor = QBrush(QColor(255, 255, 255))
                        model.setData(model.index(i,col), bgColor, QtCore.Qt.BackgroundRole)
            else:
                checkedRungs = 0
                for i in range(rungQty):
                    rungItem = root.child(i) #QTreeWidgetItem
                    rungIndex = model.index(i,0)
                    x = rungIndex.row() #applies to type QModelIndex
                    y = rungIndex.column()
                    if rungItem.checkState(0) == Qt.Checked:
                        checkedRungs +=1
                        self.rungCopySelected = rungItem.text(0)
                        if checkedRungs == 1:
                            bgColor = QBrush(QColor(0, 255, 255))
                            for col in range (0,11):
                                model.setData(model.index(x,col), bgColor, QtCore.Qt.BackgroundRole)
                                model.setData(model.index(x+1,col), bgColor, QtCore.Qt.BackgroundRole)
                    else:
                        rungItem.setDisabled(True)
                        if rungItem.text(0) != self.lastCopyRung:
                            rungItem.setCheckState(0,False)
            self.evalRungCopyNoTxt()
        except:
            self.outputError()



    def evalSavePath(self):
        self.pushButton_5.setEnabled(False)
        try:
            extension = self.lineEdit_2.text().split(".")[-1]
            if extension == "adpro" and self.project is not None:
                self.pushButton_5.setEnabled(True)
        except:
            pass

    def populateSeqRungList(self):
        try:
            self.taskForCopy = None
            for item in self.treeWidget_5.selectedIndexes():
                task = item.data(Qt.DisplayRole)
                for i in range(0,len(self.c.tasks)):
                    if self.c.tasks[i]['name'] == task:
                        #print(self.c.tasks[i]["taskFileName"])
                        self.populateRungCopyTree(i)
                        #print(type(self.c.tasks[i]["xml"]))
                        self.printTree(self.c.tasks[i]["xml"].getroot(),self.treeWidget_3)#treeWidget_3
        except:
            self.outputError()

    def populateTaskList(self):
        self.taskForCopy = None
        self.treeWidget_5.clear()
        self.treeWidget_4.clear()
        try:
            self.c.getTasks(self.c.folder)
        except:
            self.outputError()
        for task in self.c.tasks:
            branch = QTreeWidgetItem([task['name'],task["taskFileName"]])
            self.treeWidget_5.addTopLevelItem(branch)
        wait = self.appendStatus("File Successfully opened")

    def populateRungCopyTree(self,taskNo):
        self.rungCopySelected = None
        self.treeWidget_4.clear()
        self.taskForCopy = taskNo
        sresults = self.c.searchRungsForDisplay(self.c.tasks[taskNo])
        rungs = {}
        for result in sresults:
            #print(result)

            #print(self.c.unNestDict(result))
            for k,v in result.items():
                #print(k,v)
                rungNo = str(v['ladderRungNoDisp'])
                if "." not in rungNo:
                    rungNo += ".0"
                r,sr = rungNo.split(".")
                if r not in rungs:
                    rungs[r] = {}
                if rungNo not in rungs[r]:
                    rungs[r][rungNo] = {}

                if v['ladderColumnNoDisp'] not in rungs[r][rungNo]:
                    rungs[r][rungNo][v['ladderColumnNoDisp']] = {}

                if v['ladderInstruction'] not in rungs[r][rungNo][v['ladderColumnNoDisp']]:
                    rungs[r][rungNo][v['ladderColumnNoDisp']][v['ladderInstruction']] = {}

                if v['tagName'] not in rungs[r][rungNo][v['ladderColumnNoDisp']][v['ladderInstruction']]:
                    rungs[r][rungNo][v['ladderColumnNoDisp']][v['ladderInstruction']][v['tagName']] = {}
                tagID = v['tagID']

                if 'array' in v:
                    tagID += "("+ v['array']['col']+")"
                    if 'row' in v['array']:
                        tagID += "("+ v['array']['row']+")"
                if 'BOW' in v:
                    tagID += ":" + v["BOW"]["bit"]
                rungs[r][rungNo][v['ladderColumnNoDisp']][v['ladderInstruction']][v['tagName']][tagID]=True
        self.lastCopyRung = r
        #self.unNestDict2Widget(self.treeWidget_4,rungs)
        #print(self.c.unNestDict(rungs))
        #print("done")
        for k,v in rungs.items(): #rung
            a=QTreeWidgetItem([k])
            if k != self.lastCopyRung:
                a.setCheckState(0,False)


            self.treeWidget_4.addTopLevelItem(a)
            for k,v in v.items(): #subrung
                rung = [k,"-","-","-","-","-","-","-","-","-","-"]
                for k,v in v.items(): #column
                    col = int(k)
                    entry = ""
                    for k,v in v.items(): #instruction
                        entry +=k + "\n"
                        for k,v in v.items(): #tagname
                            entry +=k + "\n"
                            for k,v in v.items(): #id
                                entry +=k + "\n"
                    rung[col] = entry
                branch = QTreeWidgetItem(rung)
                branch.setFlags(branch.flags() & ~Qt.ItemIsSelectable)
                a.addChild(branch)
        self.evalRungCopyNoTxt()

    def unNestDict2Widget(self,whichWidget, input):
        for k,v in input.items():
            tree = v
            a=QTreeWidgetItem([k])
            whichWidget.addTopLevelItem(a)
            def displaytree(a,s):
                for k,v in s.items():
                    #k=str(k)
                    try:
                        if isinstance(v,dict):

                            if "text" in s.keys():
                                txt = s["text"]
                            else:
                                txt = ""
                            if "attributes" in s.keys():
                                attr = s["attributes"]
                            else:
                                attr = ""
                            ks=str(k)
                            branch = QTreeWidgetItem([ks,txt,attr])
                            a.addChild(branch)
                            displaytree(branch,v)
                        """
                        else:
                            if k != 'element':
                                print("k,v:     ", k,v)
                                if "text" in v:
                                    txt = v
                                else:
                                    txt = ""
                                if "attributes" in v:
                                    attr = v
                                else:
                                    attr = ""
                                print("k,txt,attr:     ",k,txt,attr)
                                #v = str(v)
                                branch = QTreeWidgetItem([k,txt,attr])
                                #branch = QTreeWidgetItem([child.tag,txt,str(child.attrib)])
                                a.addChild(branch)
                    """
                    except:
                        self.outputError()
            displaytree(a,tree)

    def setSaveLocation(self):
        index = self.treeView.currentIndex()
        path = self.model.filePath(index)
        extension = self.lineEdit_2.text().split(".")[-1]
        if self.disregardNameChange == False:
            self.lineEdit_2.setText(path)



    def goToLastDir(self):
        pathParts = self.lastPath.split("/")
        pathText = ""
        for part in pathParts:
            if pathText == "":
                pathText = part
            else:
                pathText += "/" + part
            index = self.model.index(pathText)
            self.treeView.expand(index)


    def saveSingleToContainter(self, varname, val):
        if "self." in varname:
            varname = varname.split("self.")[1]
        searchterm = "[" + varname + "::"
        containerFile = open('parameters', 'r')
        linelist = containerFile.readlines()
        containerFile.close()
        i = 0
        hits = 0
        for line in linelist:
            i += 1
            if searchterm in line:
                hits += 1
                #print("old line", line)
                left, right = line.split(searchterm)
                oldval, post = right.split(']')
                #print("self." + parameter + " ==", value)
                newline = left + searchterm + str(val) + "]" + post
                #print("new line:",newline)
                linelist[i-1] = newline
        if hits == 0:
            newline = "\n" + searchterm + str(val) + "]"
            linelist.append(newline)
            #print("new variable saved to container:",newline)
        containerFile = open('parameters', 'w')
        containerFile.writelines(linelist)
        containerFile.close()

    def appendStatus(self,txt):
        self.tb_StatusDisplay.appendPlainText(txt)
        QApplication.processEvents()
        return True

    def openFile(self):

        index = self.treeView.currentIndex()
        if not self.model.isDir(index):
            path = self.model.filePath(index)
            wait = self.appendStatus("opening " + str(path) + " This may take a few seconds...")
            self.project = xmlFuncs.openAdproFile(path)
            self.c = self.project.content
            self.lastPath = path
            self.projectPath = path
            pathParts = self.lastPath.split("/")
            pathText = ""
            projectNameTxt=""
            projectName = pathParts[-1].split(".")
            for i in range(0,len(projectName)-1):
                projectNameTxt += projectName[i] + "."
            projectNameTxt+="Mod.adpro"
            pathParts[-1] = projectNameTxt
            for part in pathParts:
                if pathText == "":
                    pathText = part
                else:
                    pathText += "/" + part
            self.disregardNameChange = True
            self.lineEdit_2.setText(pathText)
            self.saveSingleToContainter("self.lastPath", self.lastPath)
            self.tabWidget.insertTab(1,self.tab,self.tab0Text)
            self.tabWidget.insertTab(1,self.tab_3,self.tab3Text)
            self.tabWidget.insertTab(1,self.tab_5,self.tab5Text)
            self.tabWidget.insertTab(1,self.tab_4,self.tab4Text)
            self.tabWidget.insertTab(1,self.tab_2,self.tab2Text)
            #self.tabWidget.insertTab(0,self.tab_6,self.tab6Text)
            self.tabWidget.setCurrentIndex(2)
            self.populateTaskList()
            self.printTree(self.c.tagsRoot,self.treeWidget)




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



    def searchXML(self):
        tree = et.parse("T8.rll")
        taskName = tree.find("pgmName").text
        searchTerm = self.lineEdit.text()
        searchTerm = "Orion"
        results = {}
        resultNo = 0
        for rung in tree.iter('rungs'):
            rungNo = int(rung.find('rungNumber').text)
            subrungNo = int(rung.find('subRungNumber').text)
            if subrungNo == 0:
                rungNoDisp = "Rung # " + str(rungNo+1)
            else:
                rungNoDisp = "Rung # " + str(rungNo)+"."+str(subrungNo)
            results[rungNoDisp]={}
            rungAttribs=str(rung.attrib)

            for a in rung.iter('data'):
                hit = False
                children = []
                for b in a:
                    children.append(b)
                    if b.text != None:
                        if searchTerm in b.text:
                            hit = True
                if hit == True:
                    resultNo +=1
                    results[rungNoDisp][resultNo] = {}
                    results[rungNoDisp][resultNo]["Result #"] = resultNo
                    if b.attrib != {}:
                        results[rungNoDisp][resultNo]["attributes"] = str(b.attrib)
                    for child in children:
                        results[rungNoDisp][resultNo]["element"] = a

                        results[rungNoDisp][resultNo][child.tag] = {}
                        results[rungNoDisp][resultNo][child.tag]["text"] = child.text

                        #for tag in child:
                        #    results[rungNoDisp][resultNo]["parent"] = "yomama"
                        if child.attrib is not None:
                            results[rungNoDisp][resultNo][child.tag]["attributes"] = str(child.attrib)
                        if rungAttribs != {}:
                            results[rungNoDisp]["attributes"] = rungAttribs
                    #results[rungNoDisp][resultNo]["parent"] = a.findall("...")
        deleteList = []
        for k,v in results.items():
            if v == {}:
                deleteList.append(k)
        for key in deleteList:
            del results[key]
        op = {}
        op[taskName] = results
        print(self.unNestDict(op))
        self.unNestDict2Widget(self.treeWidget_2,op)
        #print(deleteList)
                        #print(b.text)
            ##print(children)
        #    print(i)




    def printTree(self,s,whichWidget):#treeWidget_3

        #tree = et.fromstring(s)
        tree = s
        a=QTreeWidgetItem([tree.tag,tree.text,str(tree.attrib)])
        whichWidget.addTopLevelItem(a)
        def displaytree(a,s):
            for child in s:
                try:
                    if child.text is not None:
                        txt = child.text
                    else:
                        txt = ""
                    branch = QTreeWidgetItem([child.tag,txt,str(child.attrib)])
                    a.addChild(branch)
                    displaytree(branch,child)
                except:
                    self.outputError()
        displaytree(a,tree)

    def printTree2(self,s,whichWidget):
        tree = et.fromstring(s)
        a=QTreeWidgetItem([tree.tag,tree.text,str(tree.attrib)])
        whichWidget.addTopLevelItem(a)
        def displaytree(a,s):
            for child in s:
                try:
                    if child.text is not None:
                        txt = child.text
                    else:
                        txt = ""
                    branch = QTreeWidgetItem([child.tag,txt,str(child.attrib)])
                    if "unique_ID" in child.attrib:
                        a.addChild(branch)
                    displaytree(branch,child)
                except:
                    self.outputError()
        displaytree(a,tree)

def main():
    app = QApplication([])
    window = importedGUI()
    #monitor = QDesktopWidget().screenGeometry(1)
    #window.move(monitor.left(), monitor.top())
    #window.showFullScreen()
    #window.showMaximized()
    #app.aboutToQuit.connect(lambda: window.pullCord())
    #window.myClick.writeSingleDigitalOutput()
    #app.exec_()
    try:
        sys.exit(app.exec_())
    except:
        print("Exiting")

if __name__ == '__main__':
    main()
