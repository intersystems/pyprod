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

class MyJsonData(JsonSerialize):
    name: str = Column(index=True)
    amount = Column(datatype = int)

class MyPickleData(PickleSerialize):
    name = Column()
    amount = 1

class CustomInAdapter(InboundAdapter):

    def __init__(self,iris_host_object):
        super().__init__(iris_host_object)
        self.counter = 0
        # you must preserve the constructor signature defined by the base class 
        # if you want to define instance variables using __init__. 
        # DO NOT introduce additional parameters
        # Alternatively, you can use IRISProperty to define instance variables of string and numeric types

    def OnTask(self):
        status = Status.OK()
        try:
            time.sleep(0.5)
            msg = ["any data type" , "can be shared", "between an adapter and service", self.counter]
            status = self.business_host_process_input(msg)
            self.counter += 1
        except Exception as e:
            status, _ = log_error_and_return_status("ERROR in CustomInAdapter OnTask : "+str(e))
        return status


class CustomBS(BusinessService):

    prop_setting_0 = IRISProperty(default = "does not appear on the UI as settings have not been defined")
    prop_setting_1  = IRISProperty(default = 45, description = "this appears under Additional Settings", settings="")
    prop_setting_2  = IRISProperty(settings="MyCategory")
    prop_setting_3 = IRISProperty(description = "this appears when you click on the property name in the UI", 
                                  settings="MyCategory:bplSelector")
    prop_setting_4: int = IRISProperty(settings=":dtlSelector")

    target_config_name = IRISProperty(description="Drop down list of possible target hosts under category called Target", 
                                      settings="Target:selector?context={Ens.ContextSearch/ProductionItems?targets=1&productionName=@productionId}")
    ADAPTER: str = IRISParameter(value="QuickStart.CustomInAdapter", description="Full name of ADAPTER as would appear in the backend")

    def OnProcessInput(self, input):
        status = Status.OK()
        try:
            persistent_msg = MyJsonData(input[0], input[3])
            status = self.SendRequestSync(self.target_config_name, persistent_msg)
            IRISLog.Info("Type of prop_setting_1 is " + str(type(self.prop_setting_1)))
            IRISLog.Error("displaying how to generate an error message")
            IRISLog.Status(status)
            self.prop_setting_1 += 1
            IRISLog.Warning("prop_setting_1 has been incremented" + str(self.prop_setting_1))
        except Exception as e:
            status, _ = log_error_and_return_status("ERROR in CustomBS OnProcessInput : "+str(e))
        return status


class CustomBP(BusinessProcess):

    target_config_name = IRISProperty(
        settings="Target:selector?context={Ens.ContextSearch/ProductionItems?targets=1&productionName=@productionId}")

    def OnRequest(self, request):
        status = Status.OK()
        try:
            if random.getrandbits(1):
                sync_request = MyJsonData(request.name + " json data from BP", request.amount)
            else:
                sync_request = MyPickleData(request.name + " pickle data from BP", request.amount)
            status, response = self.SendRequestSync(self.target_config_name, sync_request)
        except Exception as e:
            status, response = log_error_and_return_status("ERROR in CustomBP on_request : "+str(e))
        return status, response


class CustomBO(BusinessOperation):

    ADAPTER = IRISParameter("QuickStart.CustomOutAdapter")
    MessageMap = {
        "QuickStart.MyPickleData": "bo_method_1",
        "QuickStart.MyJsonData": "bo_method_2"
    }

    def bo_method_1(self, request):
        status = Status.OK()
        try:
            status, out_adapter_response = self.ADAPTER.out_adapter_method_1(" first argument ", parameter2 = " second argument ", python_object = ("third", "argument"))
            IRISLog.Info("Data received at bo_method_1 is: " + out_adapter_response[0])
            response = MyJsonData(out_adapter_response[0], out_adapter_response[1])
        except Exception as e:
            status, response = log_error_and_return_status("ERROR in CustomBO bo_method_1 : "+str(e))
        return status, response

    def bo_method_2(self, request):
        status = Status.OK()
        try:
            status = self.ADAPTER.out_adapter_method_2(" first argument ")
            IRISLog.Info("Data received at bo_method_2 is: " + request.name)
            response = MyJsonData("response from bo_method_2", 0)
        except Exception as e:
            status, response = log_error_and_return_status("ERROR in CustomBO bo_method_2 : "+str(e))
        return status, response
  

class CustomOutAdapter(OutboundAdapter):

    counter = IRISProperty(0,int)

    def out_adapter_method_1(self, information="default", parameter2 = "parameter2", python_object = ""):
        status = Status.OK()
        try:
            IRISLog.Info("All out adapter log messages are displayed in the BO log viewer on the production config page")
            IRISLog.Info(f"Data received at out_adapter_method_1 is: {information} {parameter2}  {str(python_object)}")
            response = ("response from out_adapter_method_1", self.counter)
            self.counter += 1
        except Exception as e:
            status, response = log_error_and_return_status("ERROR in CustomOutAdapter out_adapter_method_1 : "+str(e))
        return status, response
    
    def out_adapter_method_2(self, information="default"):
        status = Status.OK()
        try:
            IRISLog.Info("Data received at out_adapter_method_2 is: " + information)
        except Exception as e:
            status, _ = log_error_and_return_status("ERROR in CustomOutAdapter out_adapter_method_2 : "+str(e))
        return status


def log_error_and_return_status(error_message):
    IRISLog.Error(error_message)
    status = Status.ERROR(error_message)
    response = "error"
    return status, response
