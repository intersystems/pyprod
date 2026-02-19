# Set up an IRIS container to use pyprod

Here, we will set up an **InterSystems IRIS Community Edition** container to use pyprod.

### 1. Spin up the Container

```bash
docker run -d --name pyprodcontainer -p 1972:1972 -p 52773:52773 intersystems/iris-community:2025.1
```

### 2. Create an Interoperability Namespace in IRIS

You can access the IRIS Management Portal using this link : ***http://localhost:52773/csp/sys/%25CSP.Portal.Home.zen***. If your container was started using a different port mapping, substitute 52773 in the URL with your configured port. When you log in for the first time in an IRIS container, it may prompt you to update the password.

You can create an **interoperability-enabled namespace** here: 
  ```
  System > Configuration > Namespaces > Create New Namespace
  ```
  You can select ***ENSLIB*** for both the databases, or create a new database. Make sure ***Enable namespace for interoperability productions*** is selected.

### 3. Ensure the ENSLIB database is read/write

  ```
  System > Configuration > Local Databases > ENSLIB
  ```
  Uncheck *Mount Read-Only* if selected.


### 4. Enable Service Callin

Navigate to the following page on the UI and ensure **%Service_Callin** is enabled
```
System Administration > Security > Services
```
