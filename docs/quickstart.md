# Quick Start Guide

In the following example, we design a production which sends a Sync request from a BS to BP, which in turn sends a Sync request to a BO:

<img src="./images/quickstart.png" alt="alt text" width="700"/>

## Step 1 Importing libraries and objects

First, import all the components that you might need from intersystems_pyprod. Also, import any other python library that you might be using.

```python
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
```

## Step 2 Package name

In **InterSystems IRIS**, objects are organized into packages. In **intersystems_pyprod**, the attribute **`package_name`** is reserved and can be used to specify the name of the package to which all components defined within a module belong.  

This is important because components created in a Python production script may run in different processes. For the production backend to locate them, each component must have a clearly defined name. The **`package_name`** attribute ensures this. If **`package_name`** is not specified, the production automatically uses the name of the Python script as the package name.  

In this example, **`package_name`** is set at the module level, but it can also be defined at the class level if needed.  

All production components created in the script will appear in the **Production UI** using the format **`package_name.class_name`**.



```python
package_name = "QuickStart"
```


## Step 3 Create the message objects

The primary function of any production is to **pass messages**. Naturally, the design of a production depends on the types of messages it needs to handle.  

In this example, we define three message types:  

- **`TempData`** – a Python-only object. This type cannot be transmitted through the message-passing engine callbacks (**`SendRequestSync`**, **`SendRequestAsync`**, or **`SendDeferredResponse`**). However, it can be exchanged between the **Inbound Adapter and Business Service**, as well as between the **Business Operation and Outbound Adapter**.  

- **`MyJsonData`** and **`MyPickleData`** – these classes inherit from **`JsonSerialize`** and **`PickleSerialize`**, respectively. These superclasses specify the serialization method used for persisting the data contained in the message type. Unlike `TempData`, these messages can be transmitted using all message-passing engine callbacks. More information on how to create and initialize persistable messages can be found [here].  

**Note:** The **`Column()`** decorator used for certain fields in `JsonSerialize` and `PickleSerialize` subclasses indicates that those fields are stored in separate columns within the IRIS database. This design enables users to run SQL queries on those fields and even create indexes for faster lookups.
[Read more about Columns here](./allcomponents.md).

```python

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


```


## Step 4: Creating an Inbound Adapter

An inbound adapter is responsible for receiving and validating requests from external systems. Inbound adapter classes work in conjunction with business service classes. Typically, the inbound adapter provides general-purpose, reusable functionality, while the business service implements production-specific logic, such as custom validation or processing rules.

The adapter passes the data it receives to a Business Service. This data transfer can take the form of a regular Python object, an InterSystems IRIS object, or a Python message object (e.g., JsonSerialize or PickleSerialize).

In this example, we create a regular Python object to pass data from the inbound adapter to the business service. This demonstrates that any Python-based adapter will typically receive information as a Python object at the interface. [Read here for more details about the inbound adapter](./allcomponents.md). 

All inbound adapters will use the **`BusinessHost_ProcessInput`** method to pass data to the service. 

```python
class CustomInAdapter(InboundAdapter):
    Counter = IRISProperty("int", default=0)

    def OnTask(self):
        status = Status.OK()
        try:
            time.sleep(0.5)
            msg = TempData("test", self.Counter)
            status = self.BusinessHost_ProcessInput(msg)
            self.Counter += 1
        except Exception as e:
            error_msg = "ERROR in CustomInAdapter OnTask : "+str(e)
            IRISLog.Error(error_msg)
            status = Status.ERROR(error_msg)
        return status

```


## Step 5: Creating a Business Service

The role of a **Business Service (BS)** is to ensure that the data received from the adapter is packaged as an object type that can be persisted by the production before it is passed to another business host using a **`SendRequest...`** callback. A Business Service also coordinates with the adapter to receive data from external sources, performs any necessary validation on the incoming data, and, if needed, sends a response back to the source.  

In this example, the Business Service receives data from the adapter as a regular Python object. This is typical when the inbound adapter is also Python-based (though Python and ObjectScript adapters/services can be mixed).  

Here, we also see the use of **`IRISProperty`** and **`IRISParameter`**, which allow us to manage state directly within IRIS and link the class to the UI. **`IRISParameter`** acts as a class constant, while **`IRISProperty`** represents a variable. By configuring the **`setting`** field of an **`IRISProperty`**, we can specify that its value should be provided through the UI, allowing different instances of the class to have unique configurations.

```python
class CustomBS(BusinessService):

    TargetConfigName = IRISProperty(description="Name of Host as seen in the production", settings="TargetConfigName:Target")

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
    
```



## Step 6: Creating a Business Process

The **Business Process (BP)** is where the core logic of the production resides. It typically receives messages from services, transforms them or creates new messages, and then creates new messages to send to operations. A BP can also send messages to other BPs or even services 

In this example, we demonstrate the **`OnRequest()`** method. It creates two new message objects to send to another target and uses the **`SendRequestSync`** method to transmit them.


```python

class CustomBP(BusinessProcess):

    TargetConfigName: str = IRISProperty(
        settings="TargetConfigName:Target:selector?context={Ens.ContextSearch/ProductionItems?targets=1&productionName=@productionId}"
    )

    def OnRequest(self, request):
        status = Status.OK()
        if random.getrandbits(1):
            syncRequest = MyJsonData("MyJsonData request from BP to BO", 1)
        else:
            syncRequest = MyPickleData("MyPickleData request from BP to BO", 1)
        status, response = self.SendRequestSync(self.TargetConfigName, syncRequest)
        return status, response

```

## Step 7: Creating a Business Operation

The **Business Operation (BO)** is responsible for sending requests from the production to external systems via an outbound adapter. Its primary role is to convert information into a format that the outbound adapter can use.  

A Business Operation also includes a **Message Map**, which routes incoming messages to different methods based on their data type.  

In the following example, incoming messages of type **`QuickStart.MyPickleData`** are routed to **`BOmethod1`**, while messages of type **`QuickStart.MyJsonData`** are routed to **`BOmethod2`**.  

When invoking methods of an outbound adapter created using **pyprod**, all arguments must be passed explicitly—even if they are default values. However, if you prefer a more Pythonic experience when calling adapter methods, you can define the outbound adapter as a pure Python object. Since there is no additional layer of persistence or housekeeping between a Business Operation and an outbound adapter, a custom Python class can easily serve as the outbound adapter.


```python

class CustomBO(BusinessOperation):

    ADAPTER = IRISParameter("QuickStart.CustomOutAdapter")
    MessageMap = {
        "QuickStart.MyPickleData": "BOmethod1",
        "QuickStart.MyJsonData": "BOmethod2",
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
    

```

## Step 8: Creating an OutBound Adapter

An **outbound adapter** handles sending requests to external systems. It serves as a bridge that converts the native programming interface of an external application or database into a format the production can understand. Each external application or database that interacts with a production through a business operation requires its own outbound adapter.

```python
class CustomOutAdapter(OutboundAdapter):
    def OutAdapterMethod(self, information="default"):
        status = Status.OK()
        IRISLog.Info("Data received at Outbound Adapter is: " + information)
        return status

```



[You can see the complete script here](../tests/helpers/QuickStart.py)
