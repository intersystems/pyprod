from intersystems_pyprod import (
    IRISParameter,
    IRISProperty,
    BusinessService,
    BusinessProcess,
    BusinessOperation,
    OutboundAdapter,
    Column,
    JsonSerialize,
    PickleSerialize,
    IRISLog,
    Status,
    debug_host,
)

package_name = "AllPyComponents"

class MyJsonData(JsonSerialize):
    name = Column(default="default name")
    amount = Column(default=0)

class MyPickleData(PickleSerialize):
    name = Column()
    amount = 1

class AdapterlessBS(BusinessService):
    TargetConfigName = IRISProperty(settings="Target")
    def OnProcessInput(self, input):
        status = Status.OK()
        msg = MyJsonData(input)
        status, response = self.SendRequestSync(self.TargetConfigName, msg)
        return status, response
    
class CustomBP(BusinessProcess):
    TargetConfigName: str = IRISProperty(settings="Target")
    def OnRequest(self, request):
        status = Status.OK()
        if request.name == "testMyJson" :
            syncRequest = MyJsonData("MyJsonData request from BP to BO", 1)
        elif request.name == "testMyPickle":
            syncRequest = MyPickleData("MyPickleData request from BP to BO", 1)
        status, response = self.SendRequestSync(self.TargetConfigName, syncRequest)
        return status, response


class CustomBO(BusinessOperation):
    ADAPTER = IRISParameter("AllPyComponents.CustomOutAdapter")
    MessageMap = {
        "AllPyComponents.MyJsonData": "BOmethod1",
        "AllPyComponents.MyPickleData": "BOmethod2"
    }

    def BOmethod1(self, request):
        status = Status.OK()
        IRISLog.Info("Data received at BOmethod1 is: " + request.name)
        self.ADAPTER.OutAdapterMethod("From BOmethod1")
        response = MyJsonData("response from BOmethod1", 0)
        return status, response

    def BOmethod2(self, request):
        status = Status.OK()
        IRISLog.Info("Data received at BOmethod2 is: " + request.name)
        response = MyPickleData("response from BOmethod2", 0)
        return status, response
  

class CustomOutAdapter(OutboundAdapter):
    def OutAdapterMethod(self, information="default"):
        status = Status.OK()
        IRISLog.Info("Data received at Outbound Adapter is: " + information)
        return status

