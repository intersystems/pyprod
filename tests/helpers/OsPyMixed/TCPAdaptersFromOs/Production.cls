Class TCPAdaptersFromOs.Production Extends Ens.Production
{

XData ProductionDefinition
{
<Production Name="TCPAdaptersFromOs.Production" LogGeneralTraceEvents="false">
  <Description></Description>
  <ActorPoolSize>2</ActorPoolSize>
  <Item Name="TCPAdaptersFromOs.TCPBusinessService" Category="" ClassName="TCPAdaptersFromOs.TCPBusinessService" PoolSize="1" Enabled="true" Foreground="false" Comment="" LogTraceEvents="false" Schedule="">
    <Setting Target="Host" Name="TargetConfig">TCPAdaptersFromOs.TCPBusinessOperation</Setting>
    <Setting Target="Adapter" Name="AllowedIPAddresses">127.0.0.1</Setting>
    <Setting Target="Adapter" Name="Port">12345</Setting>
    <Setting Target="Adapter" Name="StayConnected">0</Setting>
  </Item>
  <Item Name="TCPAdaptersFromOs.TCPBusinessOperation" Category="" ClassName="TCPAdaptersFromOs.TCPBusinessOperation" PoolSize="1" Enabled="true" Foreground="false" Comment="" LogTraceEvents="false" Schedule="">
    <Setting Target="Adapter" Name="GetReply">0</Setting>
    <Setting Target="Adapter" Name="IPAddress">127.0.0.1</Setting>
    <Setting Target="Adapter" Name="Port">12346</Setting>
    <Setting Target="Adapter" Name="StayConnected">0</Setting>
  </Item>
</Production>
}

}
