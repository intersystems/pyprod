Class AllPyComponents.Production Extends Ens.Production
{

XData ProductionDefinition
{
<Production Name="AllPyComponents.Production" LogGeneralTraceEvents="false">
  <Description></Description>
  <ActorPoolSize>2</ActorPoolSize>
  <Item Name="AllPyComponents.AdapterlessBS" Category="" ClassName="AllPyComponents.AdapterlessBS" PoolSize="0" Enabled="true" Foreground="false" Comment="" LogTraceEvents="false" Schedule="">
    <Setting Target="Host" Name="TargetConfigName">AllPyComponents.CustomBP</Setting>
  </Item>
  <Item Name="AllPyComponents.CustomBP" Category="" ClassName="AllPyComponents.CustomBP" PoolSize="1" Enabled="true" Foreground="false" Comment="" LogTraceEvents="false" Schedule="">
    <Setting Target="Host" Name="TargetConfigName">AllPyComponents.CustomBO</Setting>
  </Item>
  <Item Name="AllPyComponents.CustomBO" Category="" ClassName="AllPyComponents.CustomBO" PoolSize="1" Enabled="true" Foreground="false" Comment="" LogTraceEvents="false" Schedule="">
  </Item>
</Production>
}

}
