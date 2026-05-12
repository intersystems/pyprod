# pyprod - Installing

### 1. Create a Virtual Environment

#### Linux / Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows (Powershell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install the Library in the Virtual Environment

#### Linux / Mac
```bash
pip install intersystems_pyprod
```

#### Windows (Powershell)

```powershell
pip install intersystems_pyprod
deactivate
```

### 3. Install the Library in the IRIS Target Folder

#### Linux / Mac

```bash
pip install intersystems_pyprod --target /path/to/iris/installation/mgr/python
```

#### Windows (Powershell)

```powershell
pip install intersystems_pyprod --target C:\InterSystems\IRIS\mgr\python
```

### 4. Set Required Environment Variables

These following environment variables may be defined in a Docker Compose file if you are using a containerized instance and do not need to be set for each command line session.

#### Linux / Mac

```bash
export IRISINSTALLDIR="/path/to/iris/installation"
export IRISUSERNAME="superuser"
export IRISPASSWORD="SYS"
export IRISNAMESPACE="ENSEMBLE"

export COMLIB="$IRISINSTALLDIR/bin"
export PYTHONPATH="$IRISINSTALLDIR/lib/python"
export DYLD_LIBRARY_PATH=$IRISINSTALLDIR/bin:$DYLD_LIBRARY_PATH
export LD_LIBRARY_PATH=$IRISINSTALLDIR/bin:$LD_LIBRARY_PATH
```

#### Windows (Powershell)

```powershell
$Env:IRISINSTALLDIR="C:\path\to\IRIS"
$Env:IRISUSERNAME="SuperUser"
$Env:IRISPASSWORD="SYS"
$Env:IRISNAMESPACE="ENSEMBLE"

$Env:COMLIB="$Env:IRISINSTALLDIR\bin"
$Env:PYTHONPATH="$Env:IRISINSTALLDIR\lib\python"
$Env:DYLD_LIBRARY_PATH="$Env:IRISINSTALLDIR\bin;$Env:DYLD_LIBRARY_PATH"
$Env:LD_LIBRARY_PATH="$Env:IRISINSTALLDIR\bin;$Env:LD_LIBRARY_PATH"
```

> **NOTE:**  
> 
> IRISINSTALLDIR is the path to your IRIS installation. On IRIS containers, it is usually ***"/usr/irissys"***. On Windows, it is usually ***"C:\InterSystems\IRIS"***.
> 
> In the above instructions, we assume that:
> - You are using a namespace with Interoperability enabled (in our example, the namespace is named `ENSEMBLE` - see [Configuring Namespaces](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_config_namespace))
> - The `ENSLIB` database is set to read/write (see [Editing a Local Database's Properties](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_config_database_edit))
> - The Service Callin feature is enabled (see [GSA_manage_services](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_manage_services)) 
>  
> You can follow the [setup instructions here](https://github.com/intersystems/pyprod/blob/main/docs/setupiriscontainer.md) to configure these settings in your IRIS instance for a container.
