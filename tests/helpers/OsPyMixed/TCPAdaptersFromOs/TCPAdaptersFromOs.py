from intersystems_pyprod import ( IRISParameter, IRISProperty,Status,
    BusinessService, BusinessOperation, JsonSerialize,IRISLog)


package_name = "TCPAdaptersFromOs"

class simplemsg(JsonSerialize):
    value: str

class TCPBusinessService(BusinessService):
    ADAPTER = IRISParameter("EnsLib.TCP.TextLineInboundAdapter")
    TargetConfig = IRISProperty(settings="TargetConfig:SelectTarget")
    def OnProcessInput(self, input):
        status = Status.OK()
        mymsg = simplemsg()
        mymsg.value = input.StringValue
        IRISLog.Info("message received at business service"+ mymsg.value)
        status = self.SendRequestAsync("TCPAdaptersFromOs.TCPBusinessOperation", mymsg)
        return status

class TCPBusinessOperation(BusinessOperation):
    ADAPTER = IRISParameter("EnsLib.TCP.TextLineOutboundAdapter")
    MessageMap = {"TCPAdaptersFromOs.simplemsg": "sendout"}
    def sendout(self,input):
        status = Status.OK()
        IRISLog.Info("recevied at operation: "+str(input.value))
        self.ADAPTER.SendMessageString(input.value)
        return status
