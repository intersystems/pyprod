import ast
import importlib
import inspect
import pickle
import sys
from typing import get_type_hints

import iris

datatype_map = {
    "int": "%Integer",
    "str": "%VarString",
}

# increasing this to a higher value can lead to <MAXSTRING> error in IRIS
BELOW_MAX_STRING = 3 * 1024 * 1024

iris_reference = type(iris.ref())

def snake_to_pascal(name: str) -> str:
    # Check if the string is in snake_case
    if "_" in name and (name.lower() == name or name.upper() == name):
        return "".join(word.capitalize() for word in name.split("_") if word)
    # Return original if not snake_case
    return name
    

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
        return iris.system.Status.Error(5001, error_string)


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

    def __init__(self, default=None, datatype="%VarString", description="", settings=""):
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
        return getattr(instance.iris_host_object, snake_to_pascal(self.name), self.default)

    def __set__(self, instance, value):
        setattr(instance.iris_host_object, snake_to_pascal(self.name), value)



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

    def __init__(self, value, datatype="", description="", keyword_list=""):
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
            try:
                return getattr(instance, "_cached_adapter")
            except AttributeError:        
                iris_adapter_object = getattr(instance.iris_host_object, "Adapter")

                if self.value in _BaseClass_registry:
                    iris_adapter_object = AdapterNamesToPascal(iris_adapter_object)

                setattr(instance, "_cached_adapter", iris_adapter_object)
                return iris_adapter_object

        return getattr(instance.iris_host_object, snake_to_pascal(self.name), self.value)

    def __set__(self, instance, value):
        raise AttributeError(f"{self.name} is a class constant and cannot be modified")



class AdapterNamesToPascal:

    """
    Wraps an outbound adapter object. Any attribute/method access on this wrapper will:
      1) convert the requested name from snake_case to PascalCase
      2) forward the operation to the outbound adapter object

    If the forwarded attribute is callable, the wrapper will call it with a SINGLE
    argument: (args, kwargs).
    """
    def __init__(self, adapter_object):
        # Avoid recursion by writing directly to __dict__
        self.__dict__['_adapter_object'] = adapter_object

    def __getattr__(self, name):
        """
        Intercept attribute access.
        Called only if attribute is NOT found on AdapterNamesToPascal itself.
        """
        pascal_name = snake_to_pascal(name)

        attr = getattr(self._adapter_object, pascal_name)



        if callable(attr):
            # Wrap method calls so args pass through unchanged
            def method(*args, **kwargs):
                arguments = (args, kwargs)
                
                response = iris.ref()
                # arguments can be passed in as a single python object as the boundary between 
                # BO and out adapter can handle %SYS.Python objects..
                status = attr(arguments,response)

                response_value = response.value
                response.value = None
                del response

                if isinstance(response_value, tuple):
                    return (status, *response_value)
                else:
                    return status, response_value
            
            # (optional) easier debugging
            method.__name__ = name
            method.__qualname__ = f"{type(self).__name__}.{name}"
            method.__doc__ = getattr(attr, "__doc__", None)


            return method

        return attr

    def __setattr__(self, name, value):
        """
        Intercept attribute assignment.
        """
        pascal_name = snake_to_pascal(name)
        setattr(self._adapter_object, pascal_name, value)




class Column:
    """
    Used in message classes to define class attributes as independent columns for the given field in IRIS database.
    This can be used when the user would want to create indexes on certain fields or would want to run SQL queries.


    """

    def __init__(
        self, *, default=None, datatype=None, description=None, index=False, **kwargs
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

    def OnProcessInputHelper(self, input):
        # This must return a status and an output in an array
        if hasattr(self, "OnProcessInput"):
            result = self.OnProcessInput(input)
        elif hasattr(self, "on_process_input"):
            result = self.on_process_input(input)
        else:
            raise NotImplementedError("Subclass must implement OnProcessInput or on_process_input")
     
        if isinstance(result, (tuple, list)):
            status, output = result
            return {"status": status,"pOutput": self.request_to_send(output),"pOutput_available": 1}
        else:
            status = result
            return {"status": status, "pOutput_available": 0}

    def SendRequestSync(self, target_dispatch_name, request, timeout=-1, description=""):
        response = iris.ref()
        send_sync_handling = iris.ref()
        status = self.iris_host_object.SendRequestSync(
            target_dispatch_name,
            self.request_to_send(request),
            response,
            timeout,
            description,
            send_sync_handling,
        )

        response_value = response.value
        response.value = None
        send_sync_handling_value = send_sync_handling.value
        send_sync_handling.value = None
        del response
        del send_sync_handling

        if send_sync_handling_value != None:
            if response_value != None:
                return (
                    status,
                    self._createmessage(message_object=response_value),
                    send_sync_handling_value,
                )
        else:
            if response_value != None:
                return status, self._createmessage(message_object=response_value)
            else:
                return status

        return status
    
    def send_request_sync(self, target_dispatch_name, request, timeout=-1, description=""):
        return self.SendRequestSync(target_dispatch_name, request, timeout, description)

    def SendRequestAsync(self, target_dispatch_name, request, description=""):
        status = self.iris_host_object.SendRequestAsync(target_dispatch_name, self.request_to_send(request), description)
        return status
    
    def send_request_async(self, target_dispatch_name, request, description=""):
        return self.SendRequestAsync(target_dispatch_name, request, description)


class BusinessProcess(BaseClass):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._hostname = "BusinessProcess"

    def OnRequestHelper(self, request):
        python_request = self._createmessage(message_object=request)

        if hasattr(self, "OnRequest"):
            result = self.OnRequest(python_request)
        elif hasattr(self, "on_request"):
            result = self.on_request(python_request)
        else:
            raise NotImplementedError("Subclass must implement OnRequest or on_request")
    
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

    def OnResponseHelper(self, request, response, call_request, call_response, completion_key):

        python_request = self._createmessage(message_object=request)
        python_response = self._createmessage(message_object=response)
        python_call_request = self._createmessage(message_object=call_request)
        python_call_response = self._createmessage(message_object=call_response)


        if hasattr(self, "OnResponse"):
            result = self.OnResponse(python_request,python_response,python_call_request,python_call_response,completion_key)
        elif hasattr(self, "on_response"):
            result = self.on_response(python_request,python_response,python_call_request,python_call_response,completion_key)
        else:
            raise NotImplementedError("Subclass must implement OnResponse or on_response")

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

    def SendRequestAsync(self,target_dispatch_name,request,response_required=1,completion_key=0,description=""):
        status = self.iris_host_object.SendRequestAsync(target_dispatch_name,self.request_to_send(request),response_required,completion_key,description)
        return status
    
    def send_request_async(self,target_dispatch_name,request,response_required=1,completion_key=0,description=""):
        return self.SendRequestAsync(target_dispatch_name,request,response_required,completion_key,description)

    def SendRequestSync(self, target_dispatch_name, request, timeout=-1, description=""):
        response = iris.ref()
        status = self.iris_host_object.SendRequestSync(target_dispatch_name,self.request_to_send(request),response,timeout,description)

        response_value = response.value
        response.value = None
        del response

        if response_value != None:
            return status, self._createmessage(message_object=response_value)
        else:
            return status
        
    def send_request_sync(self, target_dispatch_name, request, timeout=-1, description=""):
        return self.SendRequestSync( target_dispatch_name, request, timeout, description)


class BusinessOperation(BaseClass):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._hostname = "BusinessOperation"

    def OnMessageHelper(self, request, response):

        python_request = self._createmessage(message_object=request)

        if hasattr(self, "OnMessage"):
            result = self.OnMessage(python_request)
        elif hasattr(self, "on_message"):
            result = self.on_message(python_request)
        else:
            raise NotImplementedError("Subclass must implement OnMessage or on_message")

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

    def AnyMethodHelper(self, request, method_name):
        python_request = self._createmessage(message_object=request)
        result = getattr(self, method_name)(python_request)
        if isinstance(result, (tuple, list)):
            status, response = result
            return {"response": self.request_to_send(response),"status": status,"response_available": 1}
        else:
            status = result
            return {"status": status, "response_available": 0}

    def SendRequestSync(self, target_dispatch_name, request, timeout=-1, description=""):
        response = iris.ref()
        status = self.iris_host_object.SendRequestSync(
            target_dispatch_name,
            self.request_to_send(request),
            response,
            timeout,
            description,
        )

        response_value = response.value
        response.value = None
        del response

        if response_value != None:
            return status, self._createmessage(message_object=response_value)
        else:
            return status
        
    def send_request_sync(self, target_dispatch_name, request, timeout=-1, description=""):
        return self.SendRequestSync(target_dispatch_name, request, timeout, description)

    def SendRequestAsync(self, target_dispatch_name, request, description=""):
        status = self.iris_host_object.SendRequestAsync(target_dispatch_name, self.request_to_send(request), description)
        return status
    
    def send_request_async(self, target_dispatch_name, request, description=""):
        return self.SendRequestAsync(target_dispatch_name, request, description)


class InboundAdapter(BaseClass):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._hostname = "InboundAdapter"


    def OnTaskHelper(self):
        if hasattr(self, "OnTask"):
            return self.OnTask()
        elif hasattr(self, "on_task"):
            return self.on_task()
        else:
            raise NotImplementedError("Subclass must implement OnTask or on_task")
    
    def BusinessHost_ProcessInput(self, input, in_hint=""):
        
        output = iris.ref()
        output.value = ""
        temp_hint = in_hint
        hint = iris.ref()
        hint.value = temp_hint
        status = self.iris_host_object.BusinessHost.ProcessInput(input, output, hint)

        output_value = output.value
        output.value = None
        del output

        hint_value = hint.value
        hint.value = None
        del hint

        if in_hint != "":
            if (output_value is not None) and (output_value != ""):
                return status, output_value, hint_value
        else:
            if (output_value is not None) and (output_value != ""):
                return status, output_value
            else:
                return status

    def business_host_process_input(self, input, in_hint=""):
        return self.BusinessHost_ProcessInput(input, in_hint)
    
class OutboundAdapter(BaseClass):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._hostname = "OutboundAdapter"

    def AnyMethodHelper(self, arguments, method_name):

        args, kwargs = arguments
        
        result = getattr(self, method_name)(*args, **kwargs)

        if isinstance(result, (tuple, list)):
            status = result[0]
            response = result[1:]
            return {"response": response,"status": status,"response_available": 1}
        else:
            status = result
            return {"status": status, "response_available": 0}
            


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


    __slots__ = ("_iris_message_wrapper")

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

    def __init__(self,*args,iris_message_object=None,json_str_or_dict=None,serializer="json",**kwargs,):

        if (json_str_or_dict is None) != (iris_message_object is None):
            raise TypeError("iris_message_object or json_str_or_dict both need to be provided.")

        if (args or kwargs) and (iris_message_object or json_str_or_dict):
            raise TypeError("Either provide only iris_message_object + json_str_or_dict, or use args/kwargs to create a new object.")

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
                    if (val:=getattr(iris_message_object,snake_to_pascal(name))) != "":
                        setattr(self, name, val)
            else:
                if serializer != "pickle":
                    import json
                    # building using iris_message_object and json_str_or_dict. This is primarily to be used by IRIS side.
                    data = (json_str_or_dict if isinstance(json_str_or_dict, dict)
                        else json.loads(json_str_or_dict))

                    # 3) For each field, decide its runtime default:
                    #  Note: We do not re-instantiate defaults as we assume that the json_str_or_dict is populated as expected, and in case
                    #  there is a missing field, it is by design....
                    for name in field_names:
                        if name in data:
                            setattr(self, name, data[name])
                            
        else:

            package_name = cls._package
            class_name = cls.__name__
            current_package = getattr(iris, package_name)
            current_class = getattr(current_package, class_name)
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


    @staticmethod
    def _is_column_call(value: ast.AST) -> bool:
        return isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "Column"

    @classmethod
    def _class_body_field_order_top_level(cls):
        """Return names in the exact order they appear in the top-level class body.
        Handles both "AnnAssign" (e.g., "Name: T" or "Name: T = v") and "Assign"
        (e.g., "Name = v"). Does NOT descend into nested classes."""
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
        cls._serializer_class = "JsonSerialize"
    
    def __init__(self,*args,iris_message_object=None,json_str_or_dict=None,serializer="json",**kwargs,):
        if (iris_message_object is not None) and (json_str_or_dict is None):
            chunk_size = BELOW_MAX_STRING

            iteration = 0
            chunks = []
            while True:
                part = iris_message_object.chunksFromIRIS(iteration, chunk_size)
                if not part:
                    break
                chunks.append(part)
                iteration += 1
            json_str = "".join(chunks)

            json_str_or_dict = json_str
        super().__init__(*args,iris_message_object=iris_message_object,json_str_or_dict=json_str_or_dict,
            serializer=serializer,**kwargs,)

    def chunks_from_python(self, iteration, start, end):
        if iteration == 0:
            import json
            object.__setattr__(self, "_serial_stream", json.dumps(self.__dict__))
        return object.__getattribute__(self, "_serial_stream")[start:end]

    @property
    def iris_message_object(self):
        return object.__getattribute__(self, "_iris_message_wrapper")

    def update_iris_message_object(self):
        new_stream = iris._Stream.GlobalCharacter._New()
        chunk_size = BELOW_MAX_STRING
        start = 0
        iteration = 0
        chunk = self.chunks_from_python(iteration, start, start + chunk_size)
        while chunk:
            new_stream.Write(chunk)
            iteration = iteration + 1
            start = start + chunk_size
            chunk = self.chunks_from_python(iteration, start, start + chunk_size)
        self._iris_message_wrapper.SerializedStream = new_stream
        self.create_iris_message_object_properties(self._iris_message_wrapper)
        ## reset _Serial_stream to empty string as it has no purpose
        object.__setattr__(self, "_serial_stream", "")

    def create_iris_message_object_properties(self, message_object):
        for prop in self._column_field_names:
            setattr(message_object, snake_to_pascal(prop), self.__dict__[prop])


def unpickle_binary(iris_message_object,MsgCls):

    chunk_size = BELOW_MAX_STRING
    iteration = 0
    chunks = []
    while True:
        part = iris_message_object.chunksFromIRIS(iteration, chunk_size)
        if not part:
            break
        chunks.append(part)
        iteration += 1

    binary_serial_msg = b"".join(chunks)

    if binary_serial_msg:
        this_object = pickle.loads(binary_serial_msg)
        this_object._iris_message_wrapper = iris_message_object
    else: 
        this_object = MsgCls()
        for name in this_object._column_field_names:
            if (val:=getattr(iris_message_object,snake_to_pascal(name))) != "":
                setattr(this_object, name, val)

    return this_object


class PickleSerialize(ProductionMessage):
    __slots__ = ("_serial_stream",)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._serializer_class = "PickleSerialize"

    def __init__(self, *args, iris_message_object=None, **kwargs):
        ## initialize _serial_stream to empty string as it is only temporarily holding a value, before and after that it must stay empty
        object.__setattr__(self, "_serial_stream", "")
        super().__init__(*args,iris_message_object=iris_message_object,json_str_or_dict=None,
                         serializer="pickle",**kwargs,
                         )

    def chunks_from_python(self, iteration, start, end):

        if iteration == 0:
            import pickle

            temp = self._iris_message_wrapper
            self._iris_message_wrapper = ""  ## can't pickle this
            object.__setattr__(self,"_serial_stream",
                pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL, fix_imports=False),
            )
            self._iris_message_wrapper = temp

        return object.__getattribute__(self, "_serial_stream")[start:end]

    def update_iris_message_object(self):
        new_stream = iris._Stream.GlobalBinary._New()
        chunk_size = BELOW_MAX_STRING
        start = 0
        iteration = 0
        chunk = self.chunks_from_python(iteration, start, start + chunk_size)
        pickle_data_bytes = iris._SYS.Python.Bytes(chunk)
        while pickle_data_bytes:
            new_stream.Write(pickle_data_bytes)
            iteration = iteration + 1
            start = start + chunk_size
            chunk = self.chunks_from_python(iteration, start, start + chunk_size)
            pickle_data_bytes = iris._SYS.Python.Bytes(chunk)
        self._iris_message_wrapper.SerializedStream = new_stream
        self.create_iris_message_object_properties(self._iris_message_wrapper)
        ## reset _Serial_stream to empty string as it has no purpose
        object.__setattr__(self, "_serial_stream", "")

    def create_iris_message_object_properties(self, message_object):
        for prop in self._column_field_names:
            setattr(message_object, snake_to_pascal(prop), self.__dict__[prop])
