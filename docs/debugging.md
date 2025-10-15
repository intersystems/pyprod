## 🐞 For Debugging in containers


You can open the `user_script.py` in local VS Code. Add the launch configuration shown below in VS Code.

1. Install debugpy within the iris installation: 
```bash
$ pip install debugpy --target /usr/irissys/mgr/python
```
2. Open `user_script.py` in local VS Code (open it from the local directory to which the docker volume is mapped)

3. In `user_script.py`, wherever you want to debug, write a line of code:
```python
# enter the value for portnumber, for instance 5547
debug_host("ipaddressoshost", portnumber)
```
   This ip address is of the local host and not from the container. 
   ipaddressoshost can be obtained by writing the following in your terminal : ifconfig | grep "inet " | grep -v 127.0.0.1
   it will look something like: debug_host("192.168.1.48",5547)
   Make sure in user_script you are importing debug_host from intersystems_pyprod

4. Start the debugger in vscode

5. Start the production using the UI *after* starting the debugger in vscode

### VS Code `launch.json` configuration

In this config, the localRoot and remoteRoot will be the docker volume mappings that you would've used to start the container. In case you followed started the container with volume mapping as : -v /Users/local/path:/opt/pyprodfiles, then the localRoot would be /Users/local/path and remoteRoot would be /opt/pyprodfiles (Also assuming that your user_script.py is present in this volume)

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "IRIS Attach",
            "type": "python",
            "request": "attach",
            "listen": {
                "host": "0.0.0.0",
                "port": 5547
            },
            "justMyCode": false,
            "pathMappings": [
                {
                    "localRoot": "/local/path", 
                    "remoteRoot": "/docker/path"
                    // "remoteRoot": "/local/path" in case of a local instance
                }
            ]
        }
    ]
}
```
