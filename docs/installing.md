# Installing `intersystems_pyprod`

* [Docker](#docker)
* [Local Instance](#local-instance)

---

## Docker

These steps assume that you have a containerized version of IRIS with an interoperability namespace and %Service_Callin enabled. You can follow [Setup an IRIS container](#setup-an-iris-container) to setup a container. 

#### 1. Start a bash shell inside the Container

```bash
docker exec -it pyprod bash
```

#### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install the Library in the Virtual Environment

> **Note:** As long as this repo is private, `intersystems_pyprod` won’t be available on PyPI.
> You can download the latest wheel file from /intersystems_pyprod/dist/intersystems_pyprod-1.0.0a3-py3-none-any.whl

```bash
pip install intersystems_pyprod
```

#### 4. Install the Library in the IRIS Target Folder

```bash
pip install intersystems_pyprod --target /usr/irissys/mgr/python
```

#### 5. Set Required Environment Variables

```bash
export IRISINSTALLDIR="/usr/irissys"
export DYLD_LIBRARY_PATH=$IRISINSTALLDIR/bin:$DYLD_LIBRARY_PATH
export IRISUSERNAME="superuser"
export IRISPASSWORD="SYS"
export IRISNAMESPACE="ENSEMBLE"
export COMLIB="/usr/irissys/bin/"
export PYTHONPATH="/usr/irissys/lib/python"
```

#### 6. Link Your Python Production to IRIS

Ensure your `user_script.py` (which contains the Python production) is placed in the local directory linked to Docker.
Then, run the following command to register and view your components in the IRIS UI:

```bash
intersystems_pyprod user_script.py
```

> **Note:**
> IRIS is typically installed in `/usr/irissys`.
> If your installation directory differs, replace `/usr/irissys` with your actual path.

---



## Local Instance

The process for linking `pyprod` to a **local IRIS instance** is similar to the Docker setup above.

---



# Setup an IRIS container

We’ll use an **InterSystems IRIS Community Edition** container for testing.
This setup links a Docker volume to the local filesystem.

#### 1. Start a Container with IRIS

```bash
docker run -d --name pyprod \
  -p 1972:1972 -p 52773:52773 \
  -v .:/opt/pyprodfiles \
  intersystems/iris-community:2025.1
```

#### 2. Create an Interoperability Namespace in IRIS

When you log in for the first time in an IRIS container, it may prompt you to update the password.
After that, create an **interoperability-enabled namespace** where you want your production to run.

For this example, we’ll call the namespace **ENSEMBLE**.

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