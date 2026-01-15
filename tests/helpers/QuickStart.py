import time
import random
from intersystems_pyprod import (
    IRISParameter,
    IRISProperty,
    InboundAdapter,
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

iris_package_name = "QuickStart"

class TempData:
    def __init__(self, Name: str, Amount: int):
        self.Name = Name
        self.Amount = Amount


class MyJsonData(JsonSerialize):
    Name = Column()
    Amount = Column()


class MyPickleData(PickleSerialize):
    Name = Column()
    Amount = 1


class CustomInAdapter(InboundAdapter):
    Counter = IRISProperty(0,"int")

    def OnTask(self):
        status = Status.OK()
        try:
            time.sleep(0.5)
            msg = TempData("test", self.Counter)
            status = self.business_host_process_input(msg)
            self.Counter += 1
        except Exception as e:
            error_msg = "ERROR in CustomInAdapter OnTask : "+str(e)
            IRISLog.Error(error_msg)
            status = Status.ERROR(error_msg)
        return status


class CustomBS(BusinessService):

    TargetConfigName = IRISProperty(description="Name of Host as seen in the production", settings="Target")

    DummyParam = IRISParameter("constant param",description="Used to demostrate parameter use")

    ADAPTER: str = IRISParameter(value="QuickStart.CustomInAdapter", description="Full name as would appear in the backend")

    state_in_python: int = 0

    def OnProcessInput(self, input):
        status = Status.OK()
        self.state_in_python = self.state_in_python + 1
        msg = MyJsonData(input.Name+"BS", input.Amount)
        status = self.SendRequestSync(self.TargetConfigName, msg)
        IRISLog.Warning("state in python : " + str(self.state_in_python))
        IRISLog.Info("this is the dummy param" + str(self.DummyParam))
        return status


class CustomBP(BusinessProcess):

    TargetConfigName: str = IRISProperty(
        settings="Target:selector?context={Ens.ContextSearch/ProductionItems?targets=1&productionName=@productionId}"
    )

    def OnRequest(self, request):
        status = Status.OK()
        if random.getrandbits(1):
            syncRequest = MyJsonData("MyJsonData request from BP to BO", 1)
        else:
            syncRequest = MyPickleData("MyPickleData request from BP to BO", 1)
        status, response = self.SendRequestSync(self.TargetConfigName, syncRequest)
        return status, response


class CustomBO(BusinessOperation):

    ADAPTER = IRISParameter("QuickStart.CustomOutAdapter")
    MessageMap = {
        "QuickStart.MyPickleData": "BOmethod1",
        "QuickStart.MyJsonData": "BOmethod2"
    }

    def BOmethod1(self, request):
        status = Status.OK()
        IRISLog.Info("Data received at BOmethod1 is: " + request.Name)
        self.ADAPTER.OutAdapterMethod("From BOmethod1")
        response = MyPickleData("response from BOmethod1", 0)
        return status, response

    def BOmethod2(self, request):
        status = Status.OK()
        IRISLog.Info("Data received at BOmethod2 is: " + request.Name)
        response = MyPickleData("response from BOmethod2", 0)
        return status, response
  

class CustomOutAdapter(OutboundAdapter):
    def OutAdapterMethod(self, information="default"):
        status = Status.OK()
        IRISLog.Info("Data received at Outbound Adapter is: " + information)
        return status

