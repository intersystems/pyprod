from intersystems_pyprod import (
    BusinessProcess, 
    IRISProperty,
    IRISLog)

iris_package_name = "test.properties"
class aProcess(BusinessProcess):
    myStr = IRISProperty(datatype="str", settings="my settings", default="default string", description="A string property for the process")
    myInt = IRISProperty(datatype="int", settings="my settings", default=10, description="An integer property for the process")
    myBool = IRISProperty(datatype="bool", settings="my settings", default=1, description="A boolean property for the process")
    myNum = IRISProperty(datatype="num", settings="my settings", default=42, description="Number of concurrent tasks for the adapter")
    
    def OnRequest(self, input):
        IRISLog.Info("myStr: " + self.myStr)
        IRISLog.Info("myInt: " + str(self.myInt))
        IRISLog.Info("myBool: " + str(self.myBool))
        IRISLog.Info("myNum: " + str(self.myNum))
        return 1,input