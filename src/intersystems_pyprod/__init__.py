

from typing import TYPE_CHECKING
import importlib

__all__ = ["IRISParameter", "IRISProperty", "InboundAdapter", "BusinessService",
          "BusinessProcess","BusinessOperation","OutboundAdapter","ProductionMessage",
          "Column","JsonSerialize","PickleSerialize","IRISLog","Status","debug_host"]

if TYPE_CHECKING:
    # --- static hints, allows cli tool to run without breaking because of imports ---
    from ._production_connector import ( IRISParameter,IRISProperty,
    InboundAdapter,BusinessService,BusinessProcess,BusinessOperation,
    OutboundAdapter,ProductionMessage,Column,JsonSerialize,
    PickleSerialize,IRISLog,Status,debug_host,)

def __getattr__(name: str):
    if name in __all__:
        mod = importlib.import_module(f"{__name__}._production_connector")
        return getattr(mod, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    return __all__
