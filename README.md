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
# save this as HelloWorld.py
from intersystems_pyprod import (BusinessProcess,Status)

class HelloWorldBP(BusinessProcess):
    def OnRequest(self, request):
        return Status.OK(), request

```

### Step 2: Load your components to IRIS

From a command line session where you configured the environment variables, run the `intersystems_pyprod` command and provide the path to your script as an argument.

```bash
$ intersystems_pyprod /full/path/to/HelloWorld.py

    Loading HelloWorldBP to IRIS...
    ...
    ...
    Load finished successfully.
```

### Step 3: Create a production using the UI

Create the production using the **Production Configuration** page, which you can access in the IRIS UI by navigating to **Interoperability > Configure > Productions**

![HelloWorldProductionSetup](https://github.com/intersystems/pyprod/blob/main/docs/HelloWorldFiles/HelloWorldProductionSetup.png?raw=true)

This production reads in a file from a defined path and then forwards it to a target Business Process. 

We use a pre-existing Business Service called Enslib.File.PassthroughService. Configure the service by setting the file path from which it should read. Then select the Business Process you created as its target. 


> **Note:** The Business Process name includes the script name (`HelloWorld`) appended to it. Read more about package names [here](https://github.com/intersystems/pyprod/blob/main/docs/apireference.md#-package-name-project-organization-)

---
### Test your Production
Start the Production, then place a text file in the configured file path for the Business Service. After refreshing the Production page, you should see the messages that were delivered.

![HelloWorldResults](https://github.com/intersystems/pyprod/blob/main/docs/HelloWorldFiles/HelloWorldResults.png?raw=true)

> **Note:** `EnsLib.File.PassthroughService` is an existing Business Service bundled with IRIS Productions. It loads a file from a specified location and forwards it to the configured target component.

---

## Reporting Issues

Please report issues via GitHub Issues.

## Contributing 

See [Contributing guidelines](https://github.com/intersystems/pyprod/blob/main/.github/CONTRIBUTING.md)

## Useful links

[Installing](https://github.com/intersystems/pyprod/blob/main/docs/installing.md)

[Quick Start](https://github.com/intersystems/pyprod/blob/main/docs/quickstart.md)

[Debugging](https://github.com/intersystems/pyprod/blob/main/docs/debugging.md)

[API Reference](https://github.com/intersystems/pyprod/blob/main/docs/apireference.md)

[Changelog](https://github.com/intersystems/pyprod/blob/main/CHANGELOG.md)