import adproToolkit

# Modify The next 3 lines, nothing else
# Use double-backslashes in file paths (C:\\Users\\Default\\Documents\\etc

searchfor = "Conveyor(1)"
replacewith = "Conveyor(2)"
pathToProject = "Y:\\102 BCIP\\bag line 2\\plc programs\\Conveyors\\Conv1-4.1.adpro"



myProject = adproToolkit.openAdproFile(pathToProject,searchfor,replacewith)