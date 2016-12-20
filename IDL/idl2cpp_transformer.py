from pywidl.model import SimpleType, InterfaceType
from pywidl.model import Interface, PartialInterface, ImplementsStatement, \
                         Typedef, Dictionary, Callback, Enum, \
                        Exception as idl_Exception

import os
import sys
import string
from jinja2 import Template, Environment, PackageLoader

"""Generate CPP/H files from WebIDL filess"""
def dump_introspect(member):
    print("")
    public_props = (name for name in dir(member) if not name.startswith('_'))
    for k in public_props:
        print(k, getattr(member, k))

# {{{ Conversion configuration
# TODO: ANY, DATE, OBJECT, VOID
TypeMapping = {
    "BOOLEAN": {
        "c": "bool",
        "convert": "ToBoolean",
        "jsval": "boolean"
    },

    "DOMSTRING": {
        "c": "char *",
        "jsval": "string"
    },

    "BYTE": {
        "c": "int8_t",
        "convert": "ToInt16"
    },

    "OCTET": {
        "c": "uint8_t",
        "convert": "ToUint16"
    },

    "SHORT": {
        "c": "int16_t",
        "convert": "ToInt16"
    },

    "UNSIGNED_SHORT": {
        "c": "uint16_t",
        "convert": "ToUint16"
    },

    "LONG": {
        "c": "int32_t",
        "convert": "ToInt32"
    },

    "UNSIGNED_LONG": {
        "c": "uint32_t",
        "convert": "ToUint32"
    },

    "LONG_LONG": {
        "c": "int64_t",
        "convert": "ToInt64"
    },

    "UNSIGNED_LONG_LONG": {
        "c": "uint64_t",
        "convert": "ToUint64"
    },

    "FLOAT": {
        "c": "double",
        "convert": "ToNumber"
    },

    "DOUBLE": {
        "c": "double",
        "convert": "ToNumber"
    },

    "VOID": {
        "c": "void",
        "convert": "JSObjectOrNull",
        "jsval": "JS::RootedObject"
    }
}
# }}}

# {{{ Custom Jinja filters
def capitalize(text):
    """
    >>> capitalize("aaa ee")
    'Aaa Ee'
    """
    return string.capwords(text)

def ctype(text):
    """
    >>> ctype('pink')
    'pink'
    >>> ctype('VOID')
    'void'
    """
    if not TypeMapping.has_key(text) or not TypeMapping[text].has_key('c'):
         return text
    return TypeMapping[text]['c']

def jsvaltype(text):
    """
    >>> jsvaltype("floid")
    'undefined'
    >>> jsvaltype("VOID")
    'JS::RootedObject'
    """
    if not TypeMapping.has_key(text) or not TypeMapping[text].has_key('jsval'):
        return 'undefined'
    return TypeMapping[text]['jsval']

def convert(text):
    """
    >>> convert("floid")
    'floid'
    >>> convert("VOID")
    'JSObjectOrNull'
    """
    if not TypeMapping.has_key(text) or not TypeMapping[text].has_key('convert'):
        return text
    return TypeMapping[text]['convert']

def idl_type(typed):
    """
    >>> idl_type("DOUBLE")
    'UNKNOWN'
    >>> #idl_type()
    #'UNSIGNED_SHORT'
    """
    if isinstance(typed, SimpleType):
        value = typed.type
        for key in dir(SimpleType):
            if getattr(SimpleType, key) == value:
                #print("-->%s %s" % (typed, key))
                return key
    #print("FIXME", typed, type(typed))
    #dump_introspect(typed)
    return 'UNKNOWN'
# }}}

# {{{ Format output class
class Nidium:
    def __init__(self, source, output, definition, foo, **kwargs):
        self.source = source
        self.output = output
        self.definition = definition
        self.foo = foo
        self.kwargs = kwargs
        self.base_dir = './'
        if 'base_dir' in self.kwargs.keys():
            self.base_dir = self.kwargs['base_dir']
        self.path = self.output.replace('.', '_')
        self.log_fh = open(self.output, 'a', 0)
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
    def log(self, text):
        self.log_fh.write(text + "\n")
    def format(self):
        if isinstance(self.definition, Interface):
           self.format_interface()
        elif isinstance(self.definition, PartialInterface):
           self.format_partialinterface()
        elif isinstance(self.definition, ImplementsStatement):
           self.format_statement()
        elif isinstance(self.definition, Typedef):
           self.format_typedef()
        elif isinstance(self.definition, Dictionary):
           self.format_dictionary()
        elif isinstance(self.definition, Callback):
           self.format_callback()
        elif isinstance(self.definition, Enum):
           self.format_enum()
        elif isinstance(self.definition, idl_Exception):
            self.format_exception()
        else:
            raise Exception("%s is not a known pywidl type [%s]" %
                            (self.definition.name, self.definition.__class__))
    def to_dict(self):
        data = {}
        data['foo'] = self.foo
        data['kwargs'] = self.kwargs
        data['ctor'] = False
        data['constructors'] = {'maxArgs': 0, 'lst': []}
        data['operations'] = {}
        data['members'] = {}
        data['operations'] = {}
        data['parent'] = self.definition.parent
        if self.definition.name:
            data['name'] = self.definition.name
        for member in self.definition.members:
            if hasattr(member, 'type'):
                if not member.name in data['members'].keys():
                    data['members'][member.name] = member
            else:
                if not member.name in data['operations'].keys():
                    operation = {'type': 'operation', 'lst': [], 'maxArgs': 0, 'name': member.name}
                    data['operations'][member.name] = operation
                data['operations'][member.name]['lst'].append(member)
                data['operations'][member.name]['maxArgs'] = max(operation['maxArgs'], len(member.arguments))
        for attr in self.definition.extended_attributes:
            if attr.value.name == 'Constructor':
                data['ctor'] = True
                data['constructors']['lst'].append(attr.value)
                data['constructors']['maxArgs'] = max(data['constructors']['maxArgs'],
                                                      len(attr.value.arguments))
                continue
            elif attr.name == 'className':
                data['classname'] = attr.value.name
        if not 'classname' in data.keys() and 'name' in data.keys():
            data['classname'] = data['name']
        return data
    def put_file_contents(self, file_name, contents):
        print("writing to " + file_name)
        self.log(file_name)
        file_h = open(file_name, 'wb')
        file_h.write(contents)
        file_h.close()
    def template(self, file_name, template_name, data):
            env = Environment(loader=PackageLoader('idl2cpp_transformer', 'idl2cpp_templates'))
            env.filters['capitalize'] = capitalize
            env.filters['ctype'] = ctype
            env.filters['jsvaltype'] = jsvaltype
            env.filters['convert'] = convert
            env.filters['idl_type'] = idl_type
            code_tpl = env.get_template(template_name)
            output = code_tpl.render(**data)
            self.put_file_contents(file_name, output)
    def format_interface(self):
        data = self.to_dict()
        file_name = os.path.join(self.path, self.definition.name + ".cpp")
        self.template(file_name, 'base_class.cpp.tpl', data)
        file_name = os.path.join(self.path, self.definition.name + ".h")
        self.template(file_name, 'base_class.h.tpl', data)
    def format_partialinterface(self):
        raise Exception("%s formatting is not defined yet [%s]" %
                        (self.definition.name, self.definition.__class__))
    def format_statement(self):
        raise Exception("%s formatting is not defined yet [%s]" %
                        (self.definition.name, self.definition.__class__))
    def format_typedef(self):
        raise Exception("%s formatting is not defined yet [%s]" %
                        (self.definition.name, self.definition.__class__))
    def format_dictionary(self):
        data = self.to_dict()
        file_name = os.path.join(self.path, self.definition.name + ".h")
        self.template(file_name, 'dict_class.h.tpl', data)
    def format_callback(self):
        pass
        #raise Exception("%s formatting is not defined yet [%s]" %
        #                (self.definition.name, self.definition.__class__))
    def format_enum(self):
        raise Exception("%s formatting is not defined yet [%s]" %
                        (self.definition.name, self.definition.__class__))
    def format_exception(self):
        pass
        #TODO:
        #raise Exception("%s formatting is not defined yet [%s]" %
        #                (self.definition.name, self.definition.__class__))
# }}}

# {{{ Entry point
def render(definitions=[], source=None, output=None, template=None, template_type=None, foo=None, **kwargs):
    for definition in definitions:
        nidl = Nidium(source, output, definition, foo, **kwargs)
        nidl.format()
# }}}
