# InterSystems_PyProd

intersystems_pyprod is a library that allows you to create different components for the InterSystems Productions Framework, purely in python.


## Example
The following is a Business Process written using intersystems_pyprod. It just returns the request it receives back to the sender.

```python
# save this as HelloWorld.py
from intersystems_pyprod import (BusinessProcess,Status)

class HelloWorldBP(BusinessProcess):
    def OnRequest(self, request):
        return Status.OK(), request

```

The following assumes you have set the environment variables.

```bash
$ intersystems_pyprod HelloWorld.py

    Loading HelloWorldBP to IRIS...
    ...
    ...
    Load finished successfully.
```

Create the production using the UI. Add targets and other settings for the service and operation (file path to pick up the txt files):


<div align="center"><img src="./docs/HelloWorldFiles/HelloWorldProductionSetup.png" alt="alt text" width="700"/></div>

Start the Production and see the results

<div align="center"><img src="./docs/HelloWorldFiles/HelloWorldResults.png" alt="alt text" width="700"/></div>


NOTE: EnsLib.File.PassthroughService is an existing Business Service bundled with IRIS Productions. It loads a file from a given location and passes it forward to the desired target.


## Reporting Issues

Please report issues via GitHub Issues.

## Contributing

Contributions are welcome. Please submit changes via Pull Requests. 