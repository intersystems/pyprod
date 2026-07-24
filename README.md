# intersystems_pyprod

**intersystems_pyprod**, short for *InterSystems Python Productions*, is a library that allows you to build components for the InterSystems Productions framework entirely in Python. Productions provide the integration engine to connect systems that use different communication protocols and different message formats.

You can read [this introductory article](https://community.intersystems.com/post/pyprod-pure-python-iris-interoperability) to learn how to use pyprod.

The following image shows all the production components that **pyprod** enables you to create:

![SystemDiagramOfProductions](https://github.com/intersystems/pyprod/blob/main/docs/HelloWorldFiles/SystemDiagramOfProductions.png?raw=true)

## Example Workflow

Using pyprod is essentially a **3 step process**. The following example shows a Production that uses a Business Process written using **intersystems_pyprod**. This Business Process simply returns the request it receives back to the sender.

> **Note:** Before running the example, make sure you have [configured the required environment variables](https://github.com/intersystems/pyprod/blob/main/docs/installing.md) to connect to a running IRIS instance.

### Step 1: Create your production components
```python
# save this as Readme.py
from intersystems_pyprod import (BusinessProcess,Status)

iris_package_name = "Readme"

class HelloWorldBP(BusinessProcess):
    def OnRequest(self, request):
        return Status.OK(), request

```

### Step 2: Load your components to IRIS

From a command line session where you configured the environment variables, run the `intersystems_pyprod` command and provide the path to your script as an argument.

```bash
$ intersystems_pyprod /full/path/to/HelloWorld.py

    Compiling class Readme.HelloWorldBP...
    ...
    ...
    Load finished successfully.
```

### Step 3: Create a production 
You can create the production using one of two approaches: programmatically or using the UI.   
Note: These two approaches must not be mixed - use only one for the entire lifecycle of a production.  

#### A. Programmatically

```python
# add this to the end of the Readme.py file
from intersystems_pyprod import Production, ServiceItem, ProcessItem

class MyProduction(Production):
    services = [
        ServiceItem(
            "MyFileService",
            "EnsLib.File.PassthroughService",
            host_settings={
                "TargetConfigNames": "MyCustomBP",
            },
            adapter_settings={
                "FilePath": "path/to/read/files/for/Readme/in",
                "DeleteFromServer": 0,
            },
        )
    ]
    processes = [
        ProcessItem("MyCustomBP", f"{iris_package_name}.HelloWorldBP")
    ]
```

Follow Step 2 to load this production to IRIS


#### B. Using the UI

Create the production using the **Production Configuration** page, which you can access in the IRIS UI by navigating to **Interoperability > Configure > Productions**

![HelloWorldProductionSetup](https://github.com/intersystems/pyprod/blob/main/docs/HelloWorldFiles/HelloWorldProductionSetup.png?raw=true)

This production reads in a file from a defined path and then forwards it to a target Business Process. 

We use a pre-existing Business Service called Enslib.File.PassthroughService. Configure the service by setting the file path from which it should read. Then select the Business Process you created as its target. 


> **Note:** The Business Process class name in ProcessItem() includes the iris_package_name appended to it. Read more about package names [here](https://github.com/intersystems/pyprod/blob/main/docs/apireference.md#-package-name-project-organization-)



---
### Test your Production
You can start the production and inspect messages in two ways:

#### A. Using the UI

Start the Production, then place a text file in the configured file path for the Business Service. After refreshing the Production page, you should see the messages that were delivered.

![HelloWorldResults](https://github.com/intersystems/pyprod/blob/main/docs/HelloWorldFiles/HelloWorldResults.png?raw=true)

> **Note:** `EnsLib.File.PassthroughService` is an existing Business Service bundled with IRIS Productions. It loads a file from a specified location and forwards it to the configured target component.

#### B. Programmatically
You can control the production lifecycle and inspect messages using the director module. The following example starts the production, stops it, then retrieves messages sent and received at `MyFileService`:

```python
>>> from intersystems_pyprod import director
>>> director.start_production("Readme.MyProduction")
>>> director.stop_production()
>>> msgs = director.get_host_messages("MyFileService",100)
>>> msgs[1]
{'id': '496', 'time_created': '2026-06-02 23:32:36.674', 'source': 'MyFileService', 'target': 'MyCustomBP', 'status': 9, 'session_id': 496, 'body_class': 'Ens.StreamContainer', 'body_id': '6'}
```

---

## Reporting Issues

If you have an InterSystems support contract, please contact InterSystems' Worldwide Response Center (WRC) for support. Otherwise, use GitHub issues.

## Contributing 

See [Contributing guidelines](https://github.com/intersystems/pyprod/blob/main/.github/CONTRIBUTING.md)

## Useful links

[Installing](https://github.com/intersystems/pyprod/blob/main/docs/installing.md)

[Quick Start](https://github.com/intersystems/pyprod/blob/main/docs/quickstart.md)

[Debugging](https://github.com/intersystems/pyprod/blob/main/docs/debugging.md)

[API Reference](https://github.com/intersystems/pyprod/blob/main/docs/apireference.md)

[Changelog](https://github.com/intersystems/pyprod/blob/main/CHANGELOG.md)