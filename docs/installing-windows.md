# pyprod - Installing on Windows

### 1. Create a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install the Library in the Virtual Environment (from within venv)

```powershell
pip install intersystems_pyprod
deactivate
```

### 3. Install the Library in the IRIS Target Folder

```powershell
pip install intersystems_pyprod --target C:\InterSystems\IRIS\mgr\python
```

### 4. Set Required Environment Variables

```powershell
$Env:IRISINSTALLDIR="C:\InterSystems\IRIS"
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
> IRISINSTALLDIR is the path to your IRIS installation. For Windows, it is usually ***"C:\InterSystems\IRIS"***.
> 
> The above instructions were written for Windows PowerShell. We assume that:
> - You are using a namespace with Interoperability enabled (in our example, the namespace is named `ENSEMBLE`)
>     See [Configuring Namespaces](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_config_namespace)
> - The `ENSLIB` database is set to read/write
>     See [Editing a Local Database's Properties](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_config_database_edit)
> - The Service Callin feature is enabled  
>     See [GSA_manage_services](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_manage_services)