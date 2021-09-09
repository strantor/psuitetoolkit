#https://www.youtube.com/watch?v=dqg0L7Qw3ko
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
from PyQt5.uic import loadUi

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem, QTreeWidget, QTreeView, QWidget, QVBoxLayout, QFileSystemModel
import xml.etree.ElementTree as et
import xmlFuncs

class importedGUI(QtWidgets.QMainWindow):#, myGUI):
    def __init__(self, *args, **kwargs):
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
        #f=open("T8.rll",'r').read()
        #self.printTree(f,self.treeWidget_3)
        f=open("sample1_Extract\\task\\T1.rll",'r').read()
        self.printTree(f,self.treeWidget_3)
        f=open("sample1_Extract\\program.tag",'r').read()
        self.printTree(f,self.treeWidget)




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
                    except Exception as e:
                        print(e)
            displaytree(a,tree)


    def printTree(self,s,whichWidget):
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
                    a.addChild(branch)
                    displaytree(branch,child)
                except Exception as e:
                    print(e)
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
                except Exception as e:
                    print(e)
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
