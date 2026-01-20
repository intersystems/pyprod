# pyprod - Installing

We describe the installation process for containerized instances. Installation and execution of pyprod on local instances follow a similar procedure. To provide clarity on the installation steps, we first demonstrate how to set up an IRIS container and then use this setup to illustrate the installation process.

## Setup an IRIS container

We’ll use an **InterSystems IRIS Community Edition** container for testing.

#### 1. Spin up the Container

```bash
docker run -d --name pyprodcontainer -p 1972:1972 -p 52773:52773 intersystems/iris-community:2025.1
```

#### 2. Create an Interoperability Namespace in IRIS

- You can access the IRIS Management Portal using this link : ***http://localhost:52773/csp/sys/%25CSP.Portal.Home.zen***.   
If your container was started using a different port mapping, substitute 52773 in the URL with your configured port.When you log in for the first time in an IRIS container, it may prompt you to update the password.

- After that, create an **interoperability-enabled namespace** 
  ```
  System > Configuration > Namespaces > Create New Namespace
  ```

  We’ll call the namespace **ENSEMBLE**.

  You can select ***ENSLIB*** for both the databases

- Make the ENSLIB database read/write

  ```
  System > Configuration > Local Databases > ENSLIB
  ```
  Uncheck *Mount Read-Only*


#### 3. Enable Service Callin

On the IRIS Management Portal, navigate to:

```
System Administration > Security > Services
```

and enable **%Service_Callin**.

You can also access it directly via:

[http://localhost:52773/csp/sys/sec/%25CSP.UI.Portal.Services.zen](http://localhost:52773/csp/sys/sec/%25CSP.UI.Portal.Services.zen)

If your container was started using a different port mapping, substitute 52773 in the URL with your configured port.

---

## Installing `intersystems_pyprod` on IRIS running in a container

We use IRIS that we started in a container above to install pyprod. 

#### 1. Start a bash shell inside the Container

```bash
docker exec -it pyprodcontainer bash
```

#### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install the Library in the Virtual Environment

```bash
pip install intersystems_pyprod
```

#### 4. Install the Library in the IRIS Target Folder

```bash
pip install intersystems_pyprod --target /usr/irissys/mgr/python
```

#### 5. Set Required Environment Variables

These following environment variables may be defined in a Docker Compose file and do not need to be set for each terminal session.

```bash
export IRISINSTALLDIR="/usr/irissys"
export DYLD_LIBRARY_PATH=$IRISINSTALLDIR/bin:$DYLD_LIBRARY_PATH
export IRISUSERNAME="superuser"
export IRISPASSWORD="SYS"
export IRISNAMESPACE="ENSEMBLE"
export COMLIB="$IRISINSTALLDIR/bin"
export PYTHONPATH="$IRISINSTALLDIR/lib/python"
```
IRISINSTALLDIR is path to your IRIS installation. For containers, it is usually "/usr/irissys".



---

## Link Your Python production components to IRIS

Ensure your `user_script.py` (which contains the Python production components defined by you) is placed in the local directory linked to Docker. You can use the following command to do so:
```
docker cp <local_source_path> <container_name_or_id>:<container_destination_path> 
```
Then, run the following command, in the same shell where you setup the environment variables, to link your components to IRIS and view them in IRIS UI:

```bash
intersystems_pyprod <container_destination_path>/user_script.py
```

You can view the components on the following page:
```
Interoperability > Configure > Productions
```
Create a new production and click on the "+" sign next to host names to find your components in the `iris_package_name.class_name` format


