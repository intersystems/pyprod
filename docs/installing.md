# pyprod - Installing

### 1. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install the Library in the Virtual Environment

```bash
pip install intersystems_pyprod
```

### 3. Install the Library in the IRIS Target Folder

```bash
pip install intersystems_pyprod --target /path/to/iris/installation/mgr/python
```

### 4. Set Required Environment Variables

These following environment variables may be defined in a Docker Compose file if you are using a containerized instance and do not need to be set for each command line session.

```bash
export IRISINSTALLDIR="/path/to/iris/installation"
export IRISUSERNAME="superuser"
export IRISPASSWORD="SYS"
export IRISNAMESPACE="ENSEMBLE"

export COMLIB="$IRISINSTALLDIR/bin"
export PYTHONPATH="$IRISINSTALLDIR/lib/python"
export DYLD_LIBRARY_PATH=$IRISINSTALLDIR/bin:$DYLD_LIBRARY_PATH

```

> **NOTE:**  
> 
> IRISINSTALLDIR is the path to your IRIS installation. For IRIS containers, it is usually ***"/usr/irissys"***.
> 
> The above instructions were written for a bash shell inside a Linux container. We assume that:
> - You are using a namespace with Interoperability enabled (in our example, the namespace is named `ENSEMBLE`)
> - The `ENSLIB` database is set to read/write
> - The Service Callin feature is enabled  
>  
> You can follow the [setup instructions here](https://github.com/intersystems/pyprod/blob/main/docs/setupiriscontainer.md) to configure these settings in your IRIS instance.
