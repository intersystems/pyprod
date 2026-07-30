import warnings
from typing import Optional

from ._method_stubs import STUBS


def _escape_xml(value: str) -> str:
    s = str(value)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s


def _snake_to_pascal(name: str) -> str:
    # Check if the string is in snake_case
    if "_" in name and (name.lower() == name or name.upper() == name):
        return "".join(word.capitalize() for word in name.split("_") if word)
    # Return original if not snake_case
    return name
    

class Production:
    """Declarative base class for defining an IRIS production.

    Subclass this to declare the structure of your production - its settings and 
    the list of services, processes and operations it contains.

    Attributes
    ----------
    services : list[ServiceItem]
        Business services to include in the production
    processes : list[ProcessItems]
        Business processes to include in the production
    operations : list[OperationItems]
        Business operations to include in the production

    description : str, optional
        Human-readable description of the production
    actor_pool_size : int 
        Default = 2   
        Number of jobs in the common actor pool. This is the number of jobs 
        that will be shared by business processes not configured to use a private job pool.
        This value can be overridden using System Default Settings. Overriding by a matching 
        System Default Setting will occur even if this value is defined in the production definition
    testing_enabled : bool
        Default = False   
        Enable testing infrastructure for the production
        This value can be overridden using System Default Settings. Overriding by a matching 
        System Default Setting will occur even if this value is defined in the production definition
    log_general_trace_events : bool
        Default = False   
        Log trace events that are not associated with any particular config item.
        This value can be overridden using System Default Settings. Overriding by a matching 
        System Default Setting will occur even if this value is defined in the production definition
    shutdown_timeout : int
        Default = 120   
        Seconds to wait for jobs to stop during shutdown
    update_timeout : int
        Default = 10   
        Seconds to wait for jobs to stop during an update
    alert_notification_manager : str
        Full config item name of the alert notification manager
    alert_notification_operation : str
        Full config item name of the alert notification operation
    alert_notification_recipients : str
        Comma separated list of alert notification recipients
    alert_action_window : int
        Default = 60   
        Time window in minutes for alert action
    """
    # # https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ECONFIG_settings_prod
    services: list["ServiceItem"] = None
    processes: list["ProcessItem"] = None
    operations: list["OperationItem"] = None

    description: str = ""
    actor_pool_size: int = 2
    testing_enabled: bool = False
    log_general_trace_events: bool = False

    # properties from Ens.Production
    shutdown_timeout: int = 120
    update_timeout: int = 10
    alert_notification_manager: str = ""
    alert_notification_operation: str = ""
    alert_notification_recipients: str = ""
    alert_action_window: int = 60


    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attr in cls.__dict__:
            if attr.startswith("__"):
                continue

            if attr not in Production.__dict__:
                print("\n")
                warnings.warn(f"\n WARNING: There is no attribute named {attr} for Production class. Only edit attributes that have been defined in the Production superclass", stacklevel=2)
    


class _HostItem: 
    """Internal base class. Not part of the public API."""
    def __init__(self, name, class_name, *, host_settings: Optional[dict] = None, adapter_settings: Optional[dict] = None, category : str = "", pool_size : int = 1, enabled : bool = True, foreground : bool = False,
                 comment : str = "", log_trace_events : bool = False, schedule : str = ""):
        self.name = name
        self.class_name = class_name

        self.host_settings = host_settings
        self.adapter_settings = adapter_settings

        self.category = category
        self.pool_size = pool_size
        self.enabled = "true" if enabled else "false"
        self.foreground = "true" if foreground else "false"
        self.comment = comment
        self.log_trace_events = "true" if log_trace_events else "false"
        self.schedule = schedule


        
class ServiceItem(_HostItem):
    """Declares a business service item in a Production definition.

    Parameters
    ----------
    name : str   
        The name for this service as it appears in the production
    class_name : str   
        The full IRIS class name of the business service, e.g. "MyPackage.MyBusinessService"
    host_settings : dict, optional
    adapter_settings : dict, optional 
    category : str, optional   
        Optional list of categories this item belongs to, comma-separated. This is only used for 
        display purposes and does not affect the behavior of this item.
    pool_size: int, optional   
        Number of jobs to start for this config item. This value can be overridden with a non zero value
        using System Default Settings. Overriding by a matching System Default Setting will occur even 
        if this value is defined in the production definition. Use the following values based on use case:   
        0 for Business Processes (i.e. use shared Actor Pool)   
        1 for FIFO message router Business Processes (i.e. use a dedicated job)   
        1 for Business Operations   
        0 for adapterless Business Services   
        1 for others    
        For TCP based Services with JobPerConnection=1, this value is used to limit the number of connection jobs if its value 
        is greater than 1. A value of 0 or 1 places no limit on the number of connection jobs.   
    enabled : bool
        Whether this config item is enabled or not. This value can be overridden using System Default Settings.
        Overriding by a matching System Default Setting will occur even if this value is defined in the production definition.
    foreground : bool
        Whether to run the job of this config item in the foreground or background. (non-container only)
    comment : str
        Optional comment text for this component
    log_trace_events : bool
        Whether to log trace events for this item. This value can be overridden using System Default Settings.
        Overriding by a matching System Default Setting will occur even if this value is defined in the production definition.
    schedule : str   
        Specifies times when this item should be stopped and restarted. You may enter a string formatted as a comma-separated 
        list of event specifications, or you may enter the name of a schedule specification preceded by the @ symbol. To create 
        a named schedule specification, use the Interoperability > Configure > Schedule Specs page.
        If you wish to simply enter an event specification string in this field, it must use the following format:

        action:YYYY-MM-DDThh:mm:ss[,action:YYYY-MM-DDThh:mm:ss]
        Where each item in the event specification, from left to right, has the values described below:

            action - must be either START or STOP
            : - Required separator
            YYYY-MM-DD - This part of the string must have one of the following two syntaxes:
                    YYYY is the year as 4 numerals, MM is the month as 2 numerals and DD is the day of the month as 2 numerals.
                    Any of these fields may be the single character * (asterisk) indicating all years, all months, or all days.
                    YYYY is the string WEEK, MM is the specific occurrence of the day of the week (indicated by DD) in the month 
                    (01 = first occurrence of the specific day of the week in the month, 02 = second occurrence in the month, etc.), 
                    and DD is a specific day of the week (00 = Sunday, 01 = Monday, etc.).
                    MM may be * for all occurrences and DD may be * for all days.
            Note that once a field is specified as *, all fields to the left of it are also assumed to be *. Thus, if the DD value is *, 
            the MM value is treated as * even if it has a specific numeric value. Similarly, if MM is *, YYYY is treated as *.
            T - Required separator
            hh:mm:ss - Hour, minute, and second
            , - Use the comma separator only if there is another event specification after the current one. Do not use it at the end of the Schedule string.
            
        For example, to start the configuration item every day at 8 a.m. and stop it every day at 5 p.m. you could use the following schedule string:

        START:*-*-*T08:00:00,STOP:*-*-*T17:00:00
        As described at the beginning of this topic, you can also create a named schedule string. Assuming you named your schedule 'Daytime', you could then refer to your named schedule as follows:

        @Daytime
        This value can be overridden using System Default Settings.
        Overriding by a matching System Default Setting will occur even if this value is defined in the production definition.
    """ 
             
class ProcessItem(_HostItem):
    """Declares a business process item in a Production definition.

    Parameters
    ----------
    name : str   
        The name for this service as it appears in the production
    class_name : str   
        The full IRIS class name of the business service, e.g. "MyPackage.MyBusinessService"
    host_settings : dict, optional
    category : str, optional   
        Optional list of categories this item belongs to, comma-separated. This is only used for 
        display purposes and does not affect the behavior of this item.
    pool_size: int, optional   
        Number of jobs to start for this config item. This value can be overridden with a non zero value
        using System Default Settings. Overriding by a matching System Default Setting will occur even 
        if this value is defined in the production definition. Use the following values based on use case:   
        0 for Business Processes (i.e. use shared Actor Pool)   
        1 for FIFO message router Business Processes (i.e. use a dedicated job)   
        1 for Business Operations   
        0 for adapterless Business Services   
        1 for others    
        For TCP based Services with JobPerConnection=1, this value is used to limit the number of connection jobs if its value 
        is greater than 1. A value of 0 or 1 places no limit on the number of connection jobs.   
    enabled : bool
        Whether this config item is enabled or not. This value can be overridden using System Default Settings.
        Overriding by a matching System Default Setting will occur even if this value is defined in the production definition.
    foreground : bool
        Whether to run the job of this config item in the foreground or background. (non-container only)
    comment : str
        Optional comment text for this component
    log_trace_events : bool
        Whether to log trace events for this item. This value can be overridden using System Default Settings.
        Overriding by a matching System Default Setting will occur even if this value is defined in the production definition.
    schedule : 
        Specifies times when this item should be stopped and restarted. You may enter a string formatted as a comma-separated 
        list of event specifications, or you may enter the name of a schedule specification preceded by the @ symbol. To create 
        a named schedule specification, use the Interoperability > Configure > Schedule Specs page.
        If you wish to simply enter an event specification string in this field, it must use the following format:

        action:YYYY-MM-DDThh:mm:ss[,action:YYYY-MM-DDThh:mm:ss]
        Where each item in the event specification, from left to right, has the values described below:

            action - must be either START or STOP
            : - Required separator
            YYYY-MM-DD - This part of the string must have one of the following two syntaxes:
                    YYYY is the year as 4 numerals, MM is the month as 2 numerals and DD is the day of the month as 2 numerals.
                    Any of these fields may be the single character * (asterisk) indicating all years, all months, or all days.
                    YYYY is the string WEEK, MM is the specific occurrence of the day of the week (indicated by DD) in the month 
                    (01 = first occurrence of the specific day of the week in the month, 02 = second occurrence in the month, etc.), 
                    and DD is a specific day of the week (00 = Sunday, 01 = Monday, etc.).
                    MM may be * for all occurrences and DD may be * for all days.
            Note that once a field is specified as *, all fields to the left of it are also assumed to be *. Thus, if the DD value is *, 
            the MM value is treated as * even if it has a specific numeric value. Similarly, if MM is *, YYYY is treated as *.
            T - Required separator
            hh:mm:ss - Hour, minute, and second
            , - Use the comma separator only if there is another event specification after the current one. Do not use it at the end of the Schedule string.
            
        For example, to start the configuration item every day at 8 a.m. and stop it every day at 5 p.m. you could use the following schedule string:

        START:*-*-*T08:00:00,STOP:*-*-*T17:00:00
        As described at the beginning of this topic, you can also create a named schedule string. Assuming you named your schedule 'Daytime', you could then refer to your named schedule as follows:

        @Daytime
        This value can be overridden using System Default Settings.
        Overriding by a matching System Default Setting will occur even if this value is defined in the production definition.
    """ 
class OperationItem(_HostItem):
    """Declares a business operation item in a Production definition.

    Parameters
    ----------
    name : str   
        The name for this service as it appears in the production
    class_name : str   
        The full IRIS class name of the business service, e.g. "MyPackage.MyBusinessService"
    host_settings : dict, optional
    adapter_settings : dict, optional 
    category : str, optional   
        Optional list of categories this item belongs to, comma-separated. This is only used for 
        display purposes and does not affect the behavior of this item.
    pool_size: int, optional   
        Number of jobs to start for this config item. This value can be overridden with a non zero value
        using System Default Settings. Overriding by a matching System Default Setting will occur even 
        if this value is defined in the production definition. Use the following values based on use case:   
        0 for Business Processes (i.e. use shared Actor Pool)   
        1 for FIFO message router Business Processes (i.e. use a dedicated job)   
        1 for Business Operations   
        0 for adapterless Business Services   
        1 for others    
        For TCP based Services with JobPerConnection=1, this value is used to limit the number of connection jobs if its value 
        is greater than 1. A value of 0 or 1 places no limit on the number of connection jobs.   
    enabled : bool
        Whether this config item is enabled or not. This value can be overridden using System Default Settings.
        Overriding by a matching System Default Setting will occur even if this value is defined in the production definition.
    foreground : bool
        Whether to run the job of this config item in the foreground or background. (non-container only)
    comment : str
        Optional comment text for this component
    log_trace_events : bool
        Whether to log trace events for this item. This value can be overridden using System Default Settings.
        Overriding by a matching System Default Setting will occur even if this value is defined in the production definition.
    schedule : 
        Specifies times when this item should be stopped and restarted. You may enter a string formatted as a comma-separated 
        list of event specifications, or you may enter the name of a schedule specification preceded by the @ symbol. To create 
        a named schedule specification, use the Interoperability > Configure > Schedule Specs page.
        If you wish to simply enter an event specification string in this field, it must use the following format:

        action:YYYY-MM-DDThh:mm:ss[,action:YYYY-MM-DDThh:mm:ss]
        Where each item in the event specification, from left to right, has the values described below:

            action - must be either START or STOP
            : - Required separator
            YYYY-MM-DD - This part of the string must have one of the following two syntaxes:
                    YYYY is the year as 4 numerals, MM is the month as 2 numerals and DD is the day of the month as 2 numerals.
                    Any of these fields may be the single character * (asterisk) indicating all years, all months, or all days.
                    YYYY is the string WEEK, MM is the specific occurrence of the day of the week (indicated by DD) in the month 
                    (01 = first occurrence of the specific day of the week in the month, 02 = second occurrence in the month, etc.), 
                    and DD is a specific day of the week (00 = Sunday, 01 = Monday, etc.).
                    MM may be * for all occurrences and DD may be * for all days.
            Note that once a field is specified as *, all fields to the left of it are also assumed to be *. Thus, if the DD value is *, 
            the MM value is treated as * even if it has a specific numeric value. Similarly, if MM is *, YYYY is treated as *.
            T - Required separator
            hh:mm:ss - Hour, minute, and second
            , - Use the comma separator only if there is another event specification after the current one. Do not use it at the end of the Schedule string.
            
        For example, to start the configuration item every day at 8 a.m. and stop it every day at 5 p.m. you could use the following schedule string:

        START:*-*-*T08:00:00,STOP:*-*-*T17:00:00
        As described at the beginning of this topic, you can also create a named schedule string. Assuming you named your schedule 'Daytime', you could then refer to your named schedule as follows:

        @Daytime
        This value can be overridden using System Default Settings.
        Overriding by a matching System Default Setting will occur even if this value is defined in the production definition.
        
    """ 


def _validate_properties(host):
    """ 
    This method checks if a given setting name for a host or an adapter
    actually exists in the backend
    """
    import iris
    validation_warnings = []
    if host.host_settings is not None:
        for key, value in host.host_settings.items():
            if iris._Dictionary.CompiledProperty._ExistsId(f"{host.class_name}||{_snake_to_pascal(key)}") == 0:
                validation_warnings.append(f"\n WARNING: Property name {key} does not exist in Host {host.name}'s class: {host.class_name}")
    
    if host.adapter_settings is not None:
        adapter_name = iris._Dictionary.CompiledParameter._OpenId(f"{host.class_name}||ADAPTER").Default
        for key, value in host.adapter_settings.items():
            if iris._Dictionary.CompiledProperty._ExistsId(f"{adapter_name}||{_snake_to_pascal(key)}") == 0:
                validation_warnings.append(f"\n WARNING: Property name {key} does not exist in {host.name} ADAPTERS's class: {adapter_name}")
    
    return validation_warnings

def _create_item_target_settings(target, host_obj):
    if target == "host" and not host_obj.host_settings: return ""
    if target == "adapter" and not host_obj.adapter_settings: return ""

    item_target_settings = []
    for name, value in getattr(host_obj, f"{target}_settings").items():
        setting = f"""       <Setting Target="{target.capitalize()}" Name="{_snake_to_pascal(name)}">{_escape_xml(value)}</Setting>"""
        item_target_settings.append(setting)
  
    return "\n"+"\n".join(item_target_settings) if item_target_settings else ""
    

def _create_production_item(cls_obj):
    all_items = []
    validation_warnings = []
    
    def create_item(item):
        complete_string = f"""
    <Item Name="{_escape_xml(item.name)}" Category="{_escape_xml(item.category)}" ClassName="{_escape_xml(item.class_name)}" PoolSize="{item.pool_size}" Enabled="{item.enabled}" Foreground="{item.foreground}" Comment="{_escape_xml(item.comment)}" LogTraceEvents="{item.log_trace_events}" Schedule="{_escape_xml(item.schedule)}">{_create_item_target_settings("host",item)}{_create_item_target_settings("adapter",item)}
    </Item>
"""
        return complete_string
    
    if getattr(cls_obj,"services",None):
        for service in cls_obj.services:
            service_warnings = _validate_properties(service) 
            validation_warnings.extend(service_warnings)
            all_items.append(create_item(service))
    if getattr(cls_obj,"processes",None):
        for process in cls_obj.processes:
            process_warnings = _validate_properties(process) 
            validation_warnings.extend(process_warnings)
            all_items.append(create_item(process))
    if getattr(cls_obj,"operations",None):
        for operation in cls_obj.operations: 
            operation_warnings = _validate_properties(operation)
            validation_warnings.extend(operation_warnings)
            all_items.append(create_item(operation))

    items_block = "\n"+"\n".join(all_items) if all_items else ""
    return items_block, validation_warnings 
    


def _create_production_settings(cls_obj):
    setting_keys = ["shutdown_timeout", "update_timeout", "alert_notification_manager",
                    "alert_notification_operation", "alert_notification_recipients", "alert_action_window"]
    settings_list = []
    for key in setting_keys:
        current_value = getattr(cls_obj, key)
        if current_value != getattr(Production, key):
            settings_list.append(f"""<Setting Name="{_snake_to_pascal(key)}">{current_value}</Setting>""")
    return "\n"+"\n".join(settings_list) if settings_list else ""


def _create_production_class_strings(iris_package_name,subclasses):
    all_production_classes = {}
    validation_warnings = []
    for cls_name, cls_obj in subclasses.items():
        prod_class_template = STUBS.get("production_class")
        prod_items, item_warnings = _create_production_item(cls_obj)
        validation_warnings.extend(item_warnings)
        prod_cls_string = prod_class_template.format(
            PackageName = iris_package_name,
            ClassName = cls_name,
            TestingEnabled = "true" if cls_obj.testing_enabled else "false",
            LogGeneralTraceEvents = "true" if cls_obj.log_general_trace_events else "false",
            Description = cls_obj.description,
            ActorPoolSize = cls_obj.actor_pool_size,
            prod_level_settings = _create_production_settings(cls_obj),
            prod_items = prod_items,
        )

        all_production_classes[cls_name] = prod_cls_string

    return all_production_classes, validation_warnings
    


