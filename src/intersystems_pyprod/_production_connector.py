import importlib
import inspect
from typing import get_type_hints
import iris
import pickle
import sys
import ast

datatype_map = {
    "int": "%Integer",
    "str": "%VarString",
}

iris_reference = type(iris.ref())


class IRISLog:

    @staticmethod
    def _get_caller_info(skip: int = 2):
        """
        Returns (class_name, method_name) of the caller.
         - skip=0 → this frame (_get_caller_info)
         - skip=1 → Warning/Error
         - skip=2 → the real caller
        """
        frame = sys._getframe(skip)
        method_name = frame.f_code.co_name
        self_obj = frame.f_locals.get("self", None)
        if self_obj:
            class_name = type(self_obj).__name__
        else:
            class_name = frame.f_globals.get("__name__", "<module>")
        return class_name, method_name

    @staticmethod
    def Warning(message: str):
        cls, meth = IRISLog._get_caller_info()
        iris.Ens.Util.Log.LogWarning(cls, meth, message)

    @staticmethod
    def Error(message: str):
        cls, meth = IRISLog._get_caller_info()
        iris.Ens.Util.Log.LogError(cls, meth, message)

    @staticmethod
    def Info(message: str):
        cls, meth = IRISLog._get_caller_info()
        iris.Ens.Util.Log.LogInfo(cls, meth, message)

    @staticmethod
    def Assert(message: str):
        cls, meth = IRISLog._get_caller_info()
        iris.Ens.Util.Log.LogAssert(cls, meth, message)

    @staticmethod
    def Alert(message: str):
        cls, meth = IRISLog._get_caller_info()
        iris.Ens.Util.Log.LogAlert(cls, meth, message)

    @staticmethod
    def Status(status: iris.system.Status):
        cls, meth = IRISLog._get_caller_info()
        iris.Ens.Util.Log.LogStatus(cls, meth, status)


class Status:
    @staticmethod
    def OK():
        return 1

    @staticmethod
    def ERROR(error_string):
        iris.system.Status.Error(5001, error_string)


class IRISProperty:
    """
    Descriptor for exposing Python attributes as InterSystems IRIS class properties. These properties
    can be used to maintain state as well as link to the user interface and allow to enter different values for
    different instances of the class.

    Parameters
    ----------
    datatype : str
        Python datatype that will get mapped to IRIS datatype. int->%Integer, str->%VARString, bool -> %Boolean.
    description : str
        A human-readable description that will become a “///” comment line right above the Property definition.
    default : any
        The default value to emit as [InitialExpression = ...] in the generated OS code.
    settings : str
        A string which will appear as is in the Parameter SETTINGS that is generated in the OS code.
        https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EGDV_prog#EGDV_prog_settings_options
    """

    def __init__(self, datatype="%VarString", description="", default=None, settings=""):
        self.datatype = datatype
        self.description = description
        self.default = default
        self.settings = settings
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance.iris_host_object, self.name, self.default)

    def __set__(self, instance, value):
        setattr(instance.iris_host_object, self.name, value)

    def metadata(self):
        return {
            "datatype": self.datatype,
            "description": self.description,
            "default": self.default,
            "SETTINGS": self.settings,
        }

    def generate_os_property(self):
        desc = ""
        if self.description:
            desc = f"/// {self.description} \n"
        desc = desc + f"Property {self.name}"
        if self.datatype:
            desc = desc + f" As {datatype_map[self.datatype]}"
        else:
            desc = desc + f" As %String"

        if self.default:

            desc = desc + " [InitialExpression = {self.default}] ;"
        return desc


class IRISParameter:
    """
    Descriptor for exposing Python attributes as InterSystems IRIS class constants (called parameters in IRIS).
    These cannot be modified at runtime.

    Parameters
    ----------
    datatype : str
        Python datatype that will get mapped to IRIS datatype. int->%Integer, str->%VARString, bool -> %Boolean.
    description : str
        A human-readable description that can be seen in the GUI, on hovering over the parameter name.
    value : any
        The value for this contant.
    """

    def __init__(self, value, *, description="", datatype="", keyword_list=""):
        self.value = value
        self.description = description
        self.datatype = datatype
        self.keyword_list = keyword_list
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.name == "ADAPTER":
            return getattr(instance.iris_host_object, "Adapter")
        return getattr(instance.iris_host_object, self.name, self.value)

    def __set__(self, instance, value):
        raise AttributeError(f"{self.name} is a class constant and cannot be modified")

    def metadata(self):
        return {
            "value": self.value,
            "description": self.description,
            "datatype": self.datatype,
            "keyword_list": self.keyword_list,
        }


class Column:
    """
    Used in message classes to define class attributes as independent columns for the given field in IRIS database.
    This can be used when the user would want to create indexes on certain fields or would want to run SQL queries.


    """

    def __init__(
        self, *, default=None, index=False, description=None, datatype=None, **kwargs
    ):
        self.default = default
        self.index = bool(index)
        self.datatype = datatype
        self.description = description
        # capture any other flags user might pass:
        self.extra = kwargs

    def __repr__(self):
        flags = []
        if self.index:
            flags.append("index")
        flags += [f"{k}={v!r}" for k, v in self.extra.items()]
        return f"<description default={self.default!r} {' '.join(flags)}>"

    def get_default(self):
        # allows wrapper to uniformly fetch the default value
        return self.default


_BaseClass_registry: dict[str, type] = {}


# Intermediate layer for IRIS roles
# Base class
class BaseClass:

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Look first for a class-level override:
        pkg = getattr(cls, "package_name", None)
        if pkg is None:
            # Next, look for a module-level override. In this case, the package name must have been defined closer to the top:
            mod = importlib.import_module(cls.__module__)
            pkg = getattr(mod, "package_name", None)

        if pkg is None:
            # Fallback to the filename of the module:
            pkg = cls.__module__.split(".")[-1]

        # Cache it on the class object, in the class’s internal __dict__, for instant lookup later:
        cls._package = pkg
        cls._fullname = cls._package + "." + cls.__name__
        # register every user subclass by its __name__. This is later used in Host classes for
        # generating objects dynamically at runtime based on incoming message type...
        _BaseClass_registry[cls._fullname] = cls

    def __init__(self, iris_host_object):
        self.iris_host_object = iris_host_object

    def _createmessage(self, message_object, *args, **kwargs):
        try:
            
            # this removes iris. which is in front of the incoming class name from iris backend
            module_name = message_object.__class__.__module__[5:]  
            class_name = message_object.__class__.__name__
            saved_class_name = module_name + "." + class_name
            if saved_class_name not in _ProductionMessage_registry:
                # in coming message_object is already an objectscript data type class
                return message_object

            MsgCls = _ProductionMessage_registry[module_name + "." + class_name]
            if issubclass(MsgCls, PickleSerialize):
                return unpickle_binary(message_object,MsgCls)

        except KeyError:
            raise LookupError(f"No messageclass named {class_name!r} registered")
        return MsgCls(iris_message_object=message_object)

    def request_to_send(self, request):
        if request == "":
            return ""
        if getattr(request, "_fullname", None):
            request.update_iris_message_object()
            return request.iris_message_object
        else: 
            return request

    def fullname(self):
        return self._fullname

    def OKStatus(self):
        return 1

    def ErrorStatus(self, error_string):
        return iris.system.Status.Error(5001, error_string)


class BusinessService(BaseClass):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._hostname = "BusinessService"

    def OnProcessInput(self, input):
        """
        The standard signatue is
        def OnProcessInput(self, input):
            status = 1
            ...
            return status,output
        must return a status string. This is usually the one received from a SendReq.. call.
        Alterately, this can be set manually. "1" is for success, uses self.ErrorStatus() to generate error status
        output is optional
        :param input: data received either from the inbound adapter or by direct call to the BS
        """
        raise NotImplementedError(
            "OnProcessInput() must be implemented by the subclass"
        )

    def OnProcessInputHelper(self, input):
        # This must return a status and an output in an array

        result = self.OnProcessInput(input)
        if isinstance(result, (tuple, list)):
            status, output = result
            return {
                "status": status,
                "pOutput": self.request_to_send(output),
                "pOutput_available": 1,
            }
        else:
            status = result
            return {"status": status, "pOutput_available": 0}

    def SendRequestSync(
        self, pTargetDispatchName, pRequest, pTimeout=-1, pDescription=""
    ):
        pResponse = iris.ref()
        pSendSyncHandling = iris.ref()
        status = self.iris_host_object.SendRequestSync(
            pTargetDispatchName,
            self.request_to_send(pRequest),
            pResponse,
            pTimeout,
            pDescription,
            pSendSyncHandling,
        )

        response_value = pResponse.value
        pResponse.value = None
        sendSyncHandling_value = pSendSyncHandling.value
        pSendSyncHandling.value = None
        del pResponse
        del pSendSyncHandling

        if sendSyncHandling_value != None:
            if response_value != None:
                return (
                    status,
                    self._createmessage(message_object=response_value),
                    sendSyncHandling_value,
                )
        else:
            if response_value != None:
                return status, self._createmessage(message_object=response_value)
            else:
                return status

        return status

    def SendRequestAsync(self, pTargetDispatchName, pRequest, pDescription=""):
        status = self.iris_host_object.SendRequestAsync(
            pTargetDispatchName, self.request_to_send(pRequest), pDescription
        )
        return status


class BusinessProcess(BaseClass):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._hostname = "BusinessProcess"

    def OnRequest(self, request):
        ## To be defined by the user
        pass

    def OnRequestHelper(self, request):
        python_request = self._createmessage(message_object=request)
        result = self.OnRequest(python_request)
        if isinstance(result, (tuple, list)):
            status, response = result
            return {
                "response": self.request_to_send(response),
                "status": status,
                "response_available": 1,
            }
        else:
            status = result
            return {"status": status, "response_available": 0}

    def OnResponse(self, request, response, callrequest, callresponse, pCompletionKey):
        pass

    def OnResponseHelper(
        self, request, response, callrequest, callresponse, pCompletionKey
    ):

        python_request = self._createmessage(message_object=request)
        python_response = self._createmessage(message_object=response)
        python_callrequest = self._createmessage(message_object=callrequest)
        python_callresponse = self._createmessage(message_object=callresponse)

        result = self.OnResponse(
            python_request,
            python_response,
            python_callrequest,
            python_callresponse,
            pCompletionKey,
        )

        if isinstance(result, (tuple, list)):
            status, response = result
            return {
                "response": self.request_to_send(response),
                "status": status,
                "response_available": 1,
            }
        else:
            status = result
            return {"status": status, "response_available": 0}

    def SendRequestAsync(
        self,
        pTargetDispatchName,
        pRequest,
        pResponseRequired=1,
        pCompletionKey=0,
        pDescription="",
    ):
        status = self.iris_host_object.SendRequestAsync(
            pTargetDispatchName,
            self.request_to_send(pRequest),
            pResponseRequired,
            pCompletionKey,
            pDescription,
        )
        return status

    def SendRequestSync(
        self, pTargetDispatchName, pRequest, pTimeout=-1, pDescription=""
    ):
        pResponse = iris.ref()
        status = self.iris_host_object.SendRequestSync(
            pTargetDispatchName,
            self.request_to_send(pRequest),
            pResponse,
            pTimeout,
            pDescription,
        )

        response_value = pResponse.value
        pResponse.value = None
        del pResponse

        if response_value != None:
            return status, self._createmessage(message_object=response_value)
        else:
            return status


class BusinessOperation(BaseClass):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._hostname = "BusinessOperation"

    def OnMessage(self, pReq):
        ## To be defined by the user
        pass

    def OnMessageHelper(self, request, response):
        # debug_host("192.168.1.48",5549)
        python_request = self._createmessage(message_object=request)

        result = self.OnMessage(python_request)

        if isinstance(result, (tuple, list)):
            status, response = result
            # return {"status":status, "response_available":0}
            # return {"response":response,"status":status, "response_available":1}
            return {
                "response": self.request_to_send(response),
                "status": status,
                "response_available": 1,
            }
        else:
            status = result
            return {"status": status, "response_available": 0}

    def AnyMethodHelper(self, request, methodName):
        python_request = self._createmessage(message_object=request)
        result = getattr(self, methodName)(python_request)
        if isinstance(result, (tuple, list)):
            status, response = result
            return {
                "response": self.request_to_send(response),
                "status": status,
                "response_available": 1,
            }
        else:
            status = result
            return {"status": status, "response_available": 0}

    def SendRequestSync(
        self, pTargetDispatchName, pRequest, pTimeout=-1, pDescription=""
    ):
        pResponse = iris.ref()
        status = self.iris_host_object.SendRequestSync(
            pTargetDispatchName,
            self.request_to_send(pRequest),
            pResponse,
            pTimeout,
            pDescription,
        )

        response_value = pResponse.value
        pResponse.value = None
        del pResponse

        if response_value != None:
            return status, self._createmessage(message_object=response_value)
        else:
            return status

    def SendRequestAsync(self, pTargetDispatchName, pRequest, pDescription=""):
        status = self.iris_host_object.SendRequestAsync(
            pTargetDispatchName, self.request_to_send(pRequest), pDescription
        )
        return status


class InboundAdapter(BaseClass):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._hostname = "InboundAdapter"

    def OnTask():
        raise NotImplementedError(
            "OnTask() must be implemented by the subclass. This only returns a status"
        )

    def BusinessHost_ProcessInput(self, pInput, InHint=""):
        
        pOutput = iris.ref()
        pOutput.value = ""
        tempHint = InHint
        pHint = iris.ref()
        pHint.value = tempHint
        status = self.iris_host_object.BusinessHost.ProcessInput(pInput, pOutput, pHint)

        output_value = pOutput.value
        pOutput.value = None
        del pOutput

        hint_value = pHint.value
        pHint.value = None
        del pHint

        if InHint != "":
            if (output_value is not None) and (output_value != ""):
                return status, output_value, hint_value
        else:
            if (output_value is not None) and (output_value != ""):
                return status, output_value
            else:
                return status


class OutboundAdapter(BaseClass):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._hostname = "OutboundAdapter"


def debug_host(ip: str, port: int = 5547) -> None:
    """
    Connect to a debugpy debugger.

    Assumes debugpy is installed.

    On macOS, you can get the IP by running:
        ifconfig | grep "inet " | grep -v 127.0.0.1

    The IP address is the value right after 'inet' in the response.
    """
    import debugpy

    try:
        debugpy.connect((ip, port))
        debugpy.breakpoint()
    except Exception as e:
        iris.Ens.Util.Log.LogWarning(
            " ",
            " ",
            f"Failed to connect to debugger: {e}, continuing code execution."
            f"Check if you are using correct ip address and port."
            f"If your pool size for this business host is > 1, "
            f"it is possible that one of the jobs is connected to the debugger already",
        )


_ProductionMessage_registry: dict[str, type] = {}


class ProductionMessage:
    """
    Base class for messages with three valid creation paths:

    1. Brand-new with positional and/or keyword arguments
    (args/kwargs provided, no iris_message_object or JSON)
    — creates a new Python object and a new empty IRIS wrapper.

    2. Brand-new empty
    (no args, no kwargs, no iris_message_object, no JSON)
    — creates a new Python object with defaults and a new empty IRIS wrapper.

    3. Rehydrate existing wrapper (iris_message_object)
    — used when recreating the Python object from an IRIS object.
    Not intended for direct use by end users.

    All other combinations raise a TypeError.
    """


    __slots__ = ("_iris_message_wrapper", "_serializer")

    # subclass hook: runs once when each subclass is defined
    # Used here to just get the package name.
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Look first for a class-level override:
        pkg = getattr(cls, "package_name", None)
        if pkg is None:
            # Next, look for a module-level override. In this case, the package name must have been defined closer to the top:
            mod = importlib.import_module(cls.__module__)
            pkg = getattr(mod, "package_name", None)

        if pkg is None:
            # Fallback to the filename of the module:
            pkg = cls.__module__.split(".")[-1]

        # Cache it on the class object, in the class’s internal __dict__, for instant lookup later:
        cls._package = pkg
        cls._fullname = cls._package + "." + cls.__name__
        cls._field_names, cls._column_field_names = cls._class_body_field_order_top_level()
        # register every user subclass by its __name__. This is later used in Host classes for
        # generating objects dynamically at runtime based on incoming message type...
        _ProductionMessage_registry[cls._fullname] = cls

    def __init__(
        self,
        *args,
        iris_message_object=None,
        json_str_or_dict=None,
        serializer="json",
        **kwargs,
    ):

        if (json_str_or_dict is None) != (iris_message_object is None):
            raise TypeError(
                "iris_message_object or json_str_or_dict both need to be provided."
            )

        if (args or kwargs) and (iris_message_object or json_str_or_dict):
            raise TypeError(
                "Either provide only iris_message_object + json_str_or_dict, or use args/kwargs to create a new object."
            )

        # Grabs the actual class of the instance you’re initializing.ou want to inspect the annotations on whatever subclass 
        # you’re in (e.g. NewMsgType), not on ProductionMessage itself. Using type(self) makes it generic for any subclass.
        cls = type(self)
        field_names = cls._field_names

        # 2) Build map of passed-in values
        values = {}
        if iris_message_object is not None:
            # There is a case when the python type object is originating IRIS side. This happens when using testing
            # service from the productions UI. Here, the json_str_or_dict would be empty. 
            if json_str_or_dict == "":
                for name in cls._column_field_names:
                    if (val:=getattr(iris_message_object,name)) is not "":
                        setattr(self, name, val)
            else:
                if serializer != "pickle":
                    # building using iris_message_object and json_str_or_dict. This is primarily to be used by IRIS side.
                    data = (
                        json_str_or_dict
                        if isinstance(json_str_or_dict, dict)
                        else __import__(serializer).loads(json_str_or_dict)
                    )
                    for name in field_names:
                        if name in data:
                            values[name] = data[name]
                    # 3) For each field, decide its runtime default:
                    #  Note: We do not re-instantiate defaults as we assume that the json_str_or_dict is populated as expected, and in case
                    #  there is a missing field, it is by design....
                    for name in field_names:
                        if name in values:
                            val = values[name]
                            setattr(self, name, val)
        else:

            PackageName = cls._package
            ClassName = cls.__name__
            current_package = getattr(iris, PackageName)
            current_class = getattr(current_package, ClassName)
            iris_message_object = current_class._New()

            # building using args/kwargs. This is primarily to be used by python side.
            #   a) positional
            for idx, value in enumerate(args):
                if idx >= len(field_names):
                    raise TypeError(
                        f"{cls.__name__}() takes at most {len(field_names)} positional args (got {len(args)})"
                    )
                values[field_names[idx]] = value
            #   b) keyword
            for key, value in kwargs.items():
                if key not in field_names:
                    raise TypeError(f"{cls.__name__}() got unexpected argument '{key}'")
                values[key] = value

            # For each field, decide its runtime default:
            for name in field_names:
                if name in values:
                    val = values[name]
                else:
                    # Did the class declare a Column(...) default?
                    class_default = getattr(cls, name, None)
                    if isinstance(class_default, Column):
                        val = class_default.get_default()
                    else:
                        # any plain class-level default (e.g. Amount: int = 10)
                        val = class_default if class_default is not None else None
                setattr(self, name, val)

        # 5) Link the Python object to the IRIS wrapper:
        object.__setattr__(self, "_iris_message_wrapper", iris_message_object)
        object.__setattr__(self, "_serializer", serializer)


    @staticmethod
    def _is_column_call(value: ast.AST) -> bool:
        return isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "Column"

    @classmethod
    def _class_body_field_order_top_level(cls):
        """Return names in the exact order they appear in the top-level class body.
        Handles both 'AnnAssign' (e.g., 'Name: T' or 'Name: T = v') and 'Assign'
        (e.g., 'Name = v'). Does NOT descend into nested classes."""
        src = inspect.getsource(cls)
        mod = ast.parse(src)
        # find the top-level ClassDef with this name
        target = next(
            (
                n
                for n in mod.body
                if isinstance(n, ast.ClassDef) and n.name == cls.__name__
            ),
            None,
        )
        if not target:
            raise RuntimeError(f"Couldn't locate class body for {cls.__name__}")

        names, columns, seen = [], [], set()
        for stmt in target.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                n = stmt.target.id
                if n not in seen:
                    if stmt.value is not None and cls._is_column_call(stmt.value):
                        columns.append(n)
                    names.append(n)
                    seen.add(n)
            elif isinstance(stmt, ast.Assign):
                # include simple 'Name = ...' (also collects each Name in 'x = y = 0')
                for t in stmt.targets:                    
                    if isinstance(t, ast.Name):
                        name = t.id
                        if name not in seen:
                            if cls._is_column_call(stmt.value):
                                columns.append(name)
                            names.append(name)
                            seen.add(name)
            # ignore methods, decorators, nested classes, etc.
        return names, columns

    @property
    def iris_message_object(self):
        return object.__getattribute__(self, "_iris_message_wrapper")

    def __repr__(self):
        cls = type(self)
        items = ", ".join(f"{n}={getattr(self, n)!r}" for n in cls._field_names)
        return f"{cls.__name__}({items})"

    def update_iris_message_object(self):
        pass
        # raise NotImplementedError("must write this method for each subclass to define serialization tactics")

class JsonSerialize(ProductionMessage):
    __slots__ = ("_serial_stream",)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._serializer = "JsonSerialize"
    
    def __init__(
        self,
        *args,
        iris_message_object=None,
        json_str_or_dict=None,
        serializer="json",
        **kwargs,
    ):
        if (iris_message_object is not None) and (json_str_or_dict is None):
            chunkSize = (
                3 * 1024 * 1024
            )  # note. keep in mind that increasing it to a higher value can lead to <MAXSTRING> error in IRIS
            iteration = 0
            chunks = []
            while True:
                part = iris_message_object.chunksFromIRIS(iteration, chunkSize)
                if not part:
                    break
                chunks.append(part)
                iteration += 1
            json_str = "".join(chunks)

            json_str_or_dict = json_str
        return super().__init__(
            *args,
            iris_message_object=iris_message_object,
            json_str_or_dict=json_str_or_dict,
            serializer=serializer,
            **kwargs,
        )

    def chunksFromPython(self, iteration, start, end):
        if iteration == 0:
            import json

            object.__setattr__(
                self,
                "_serial_stream",
                __import__(self._serializer).dumps(self.__dict__),
            )
        return object.__getattribute__(self, "_serial_stream")[start:end]

    @property
    def iris_message_object(self):
        return object.__getattribute__(self, "_iris_message_wrapper")

    def update_iris_message_object(self):
        newStream = iris._Stream.GlobalCharacter._New()
        chunkSize = 1024 * 3 * 1024
        start = 0
        iteration = 0
        chunk = self.chunksFromPython(iteration, start, start + chunkSize)
        while chunk:
            newStream.Write(chunk)
            iteration = iteration + 1
            start = start + chunkSize
            chunk = self.chunksFromPython(iteration, start, start + chunkSize)
        self._iris_message_wrapper.SerializedStream = newStream
        self.create_iris_message_object_properties(self._iris_message_wrapper)
        ## reset _Serial_stream to empty string as it has no purpose
        object.__setattr__(self, "_serial_stream", "")

    def create_iris_message_object_properties(self, message_object):
        module_name = message_object.__class__.__module__[5:]
        class_name = message_object.__class__.__name__
        saved_class_name = module_name + "." + class_name
        cdef = iris._Dictionary.ClassDefinition._OpenId(saved_class_name)
        for i in range(1, cdef.Properties.Count() + 1, 1):
            prop = cdef.Properties.GetAt(i).Name
            if prop in self.__dict__:
                setattr(message_object, prop, self.__dict__[prop])


def unpickle_binary(iris_message_object,MsgCls):
    if iris_message_object is not None:

        chunkSize = (
            3 * 1024 * 1024
        )  # note. keep in mind that increasing it to a higher value can lead to <MAXSTRING> error in IRIS
        iteration = 0
        chunks = []
        while True:
            part = iris_message_object.chunksFromIRIS(iteration, chunkSize)
            if not part:
                break
            chunks.append(part)
            iteration += 1

        binary_serial_msg = b"".join(chunks)

        if binary_serial_msg:
            thisobject = pickle.loads(binary_serial_msg)
            thisobject._iris_message_wrapper = iris_message_object
        else: 
            thisobject = MsgCls()
            for name in thisobject._column_field_names:
                if (val:=getattr(iris_message_object,name)) is not "":
                    setattr(thisobject, name, val)
    return thisobject



class PickleSerialize(ProductionMessage):
    __slots__ = ("_serial_stream",)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._serializer = "PickleSerialize"

    def __init__(self, *args, iris_message_object=None, **kwargs):
        ## initialize _serial_stream to empty string as it is only temporarily holding a value, before and after that it must stay empty
        object.__setattr__(self, "_serial_stream", "")
        if iris_message_object is not None:
            import pickle

            chunkSize = (
                3 * 1024 * 1024
            )  # note. keep in mind that increasing it to a higher value can lead to <MAXSTRING> error in IRIS
            iteration = 0
            chunks = []
            while True:
                part = iris_message_object.chunksFromIRIS(iteration, chunkSize)
                if not part:
                    break
                chunks.append(part)
                iteration += 1

            binary_serial_msg = b"".join(chunks)

            thisobject = pickle.loads(binary_serial_msg)
            thisobject._iris_message_wrapper = iris_message_object
            return thisobject
            # object.__setattr__(self, "_iris_message_wrapper", iris_message_object)
        else:
            return super().__init__(
                *args,
                iris_message_object=iris_message_object,
                json_str_or_dict=None,
                serializer="pickle",
                **kwargs,
            )

    def chunksFromPython(self, iteration, start, end):

        if iteration == 0:
            import pickle

            temp = self._iris_message_wrapper
            self._iris_message_wrapper = ""  ## can't pickle this
            object.__setattr__(
                self,
                "_serial_stream",
                pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL, fix_imports=False),
            )
            self._iris_message_wrapper = temp

        return object.__getattribute__(self, "_serial_stream")[start:end]

    def update_iris_message_object(self):
        newStream = iris._Stream.GlobalBinary._New()
        chunkSize = 1024 * 3 * 1024
        start = 0
        iteration = 0
        chunk = self.chunksFromPython(iteration, start, start + chunkSize)
        bytepickledata = iris._SYS.Python.Bytes(chunk)
        while bytepickledata:
            newStream.Write(bytepickledata)
            iteration = iteration + 1
            start = start + chunkSize
            chunk = self.chunksFromPython(iteration, start, start + chunkSize)
            bytepickledata = iris._SYS.Python.Bytes(chunk)
        self._iris_message_wrapper.SerializedStream = newStream
        self.create_iris_message_object_properties(self._iris_message_wrapper)
        ## reset _Serial_stream to empty string as it has no purpose
        object.__setattr__(self, "_serial_stream", "")

    def create_iris_message_object_properties(self, message_object):
        # saved_class_name = self._package+"."+self.__class__.__name__
        module_name = message_object.__class__.__module__[5:]
        class_name = message_object.__class__.__name__
        saved_class_name = module_name + "." + class_name
        cdef = iris._Dictionary.ClassDefinition._OpenId(saved_class_name)
        for i in range(1, cdef.Properties.Count() + 1, 1):
            prop = cdef.Properties.GetAt(i).Name
            if prop in self.__dict__:
                setattr(message_object, prop, self.__dict__[prop])
