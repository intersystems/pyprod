import iris
import pytest
import time
import os
from pathlib import Path

def _detect_repo_root() -> Path:
    # Prefer GH Actions env when present
    ws = os.environ.get("GITHUB_WORKSPACE")
    if ws:
        return Path(ws).resolve()
    # Otherwise walk up from this file until we find a repo marker
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
    return Path.cwd()

@pytest.fixture(scope="module",autouse=True)
def startprod():
    repo_root = _detect_repo_root()
    cls_host = repo_root / "tests" / "helpers" / "allPyComponents" / "Production.cls"
    if not cls_host.exists():
        raise FileNotFoundError(f"IRIS class file not found: {cls_host}")

    #nothing
    status = iris._SYSTEM.OBJ.Load(str(cls_host), "ck")
    print("production loading status = ", status)
    status = iris.Ens.Director.StartProduction("AllPyComponents.Production")
    print("production starting status = ", status)
    end_loop = 1
    start_time = time.time()
    prod = iris.ref()
    running = iris.ref()
    while end_loop:
        if time.time()-start_time > 12:
            end_loop = 0
            print("unable to start production in 12 seconds")
            isrunning = 0
            break
        status = iris.Ens.Director.GetProductionStatus(prod, running)
        if running.value == 1:
            isrunning = 1
            end_loop = 0
        else:
            time.sleep(0.5)
    print("productionrunning status = ", isrunning)


    yield

    status = iris.Ens.Director.StopProduction()

    end_loop = 1
    start_time = time.time()
    prod = iris.ref()
    running = iris.ref()
    while end_loop:
        if time.time()-start_time > 12:
            end_loop = 0
            print("unable to stop production in 12 seconds")
        status = iris.Ens.Director.GetProductionStatus(prod, running)
        if running.value != 1:
            end_loop = 0
        else:
            time.sleep(0.5)
    


def test_BOMethod1():
    """
    This method tests an adapterless business service. 
    """
    mybs = iris.ref()
    status = iris.Ens.Director.CreateBusinessService("AllPyComponents.AdapterlessBS", mybs)
    adapterless = mybs.value
    adapterless.TargetConfigName = "AllPyComponents.CustomBP"
    response = iris.ref()
    status = adapterless.ProcessInput("testMyJson",response)
    response = response.value.name
    adapterless.PythonClassObject = ""
    assert response == "response from BOmethod1", f"response was {response}"

def test_BOMethod2():
    """
    This method tests an adapterless business service. 
    """
    mybs = iris.ref()
    status = iris.Ens.Director.CreateBusinessService("AllPyComponents.AdapterlessBS", mybs)
    adapterless = mybs.value
    adapterless.TargetConfigName = "AllPyComponents.CustomBP"
    response = iris.ref()
    status = adapterless.ProcessInput("testMyPickle",response)
    response = response.value.name
    adapterless.PythonClassObject = ""
    assert response == "response from BOmethod2", f"response was {response}"

