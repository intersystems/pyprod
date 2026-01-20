# intersystems_pyprod

intersystems_pyprod, short for InterSystems Python Productions, is a library that allows you to create different components for the InterSystems Productions Framework, purely in python. Productions provide the integration engine to connect systems that use different communication protocols and different message formats.

![SystemDiagramOfProductions](https://github.com/intersystems/pyprod/blob/main/docs/HelloWorldFiles/SystemDiagramOfProductions.png?raw=true)

## Example
The following is a Business Process written using intersystems_pyprod. It just returns the request it receives, back to the sender.

First follow [steps to setup environment variables](https://github.com/intersystems/pyprod/blob/main/docs/installing.md) to connect to a running iris instance.

```python
# save this as HelloWorld.py
from intersystems_pyprod import (BusinessProcess,Status)

class HelloWorldBP(BusinessProcess):
    def OnRequest(self, request):
        return Status.OK(), request

```

The following assumes you have set the environment variables.

```bash
$ intersystems_pyprod /full/path/to/HelloWorld.py

    Loading HelloWorldBP to IRIS...
    ...
    ...
    Load finished successfully.
```


Create a production using the UI

![HelloWorldProductionSetup](https://github.com/intersystems/pyprod/blob/main/docs/HelloWorldFiles/HelloWorldProductionSetup.png?raw=true)

This production reads in a file from a defined path and then forwards it to a target business process. We use a pre-existing Business Service called Enslib.File.PassthroughService. We set a path from where it reads in the file. Then we select the Business Process that we created as its target. Note, the Business Process has the name of the script (HelloWorld) appended to it. Read more about package names [here](https://github.com/intersystems/pyprod/blob/main/docs/apireference.md#-package-name-project-organization-). 

Start the Production add then add a text file at the file path defined for the business service. Upon refreshing the production page, we can see the messages that were deliverd. 

[HelloWorldResults](https://github.com/intersystems/pyprod/blob/main/docs/HelloWorldFiles/HelloWorldResults.png?raw=true)


NOTE: EnsLib.File.PassthroughService is an existing Business Service bundled with IRIS Productions. It loads a file from a given location and passes it forward to the desired target.


## Reporting Issues

Please report issues via GitHub Issues.

## Contributing 

See [Contributing guidelines](https://github.com/intersystems/pyprod/blob/main/.github/CONTRIBUTING.md)

## Useful links

[Installing](https://github.com/intersystems/pyprod/blob/main/docs/installing.md)

[Quick Start](https://github.com/intersystems/pyprod/blob/main/docs/quickstart.md)

[Debugging](https://github.com/intersystems/pyprod/blob/main/docs/debugging.md)

[API Reference](https://github.com/intersystems/pyprod/blob/main/docs/apireference.md)