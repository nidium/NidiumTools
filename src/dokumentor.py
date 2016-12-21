#!/usr/bin/env python2.7

# Copyright 2016 Nidium Inc. All rights reserved.
# Use of this source code is governed by a MIT license
# that can be found in the LICENSE file.

"""
Tool to generate documentation in a different way then JSDoc does

It is good practice to document API's near their implementation.
This is difficult if it concerns a scripting language that is embedded in an other program.
Such as embedding javascript (spidermonkey engine), where functionality of the hostprogram is exposed to javascript scripts.

This tool tries to make it easier
"""
import sys, os, imp, json
from pprint import pprint

DOC = {'classes': {}, 'unknown_types': []}

### some Global variables to enhance readability
IS_Optional = True
IS_Obligated = not IS_Optional
IS_Static = True
IS_Dynamic = not IS_Static
IS_Public = True
IS_Private = not IS_Public
IS_Slow = True
IS_Fast = not IS_Slow
IS_Readonly = True
IS_ReadWrite = not IS_Readonly
IS_Array = True
IS_Single = not IS_Array
NO_Sees = None
NO_Examples = None
NO_Inherrits = None
NO_Extends = None
NO_Params = None
NO_Returns = None
NO_Default = None
NO_Typed = None

### PART ###

class DocPart():
    "Root class for transformations"
    def __init__(self):
        self.data = None

    def __str__(self):
        return self.data

    def get(self):
        return self.__str__()

class NamePart(DocPart):
    "Class for name documentation"
    def __init__(self, name):
        """Assure that the name is a string
        >>> a = NamePart("test")
        >>> a.get()
        'test'
        """
        if not isinstance(name, str):
            raise TypeError(name + " is not a string")
        if '|' in name:
            raise TypeError(name + " may not have a '|'")
        if len(name.strip()) < 2 and name not in ["x", "y", "z"]:
            raise TypeError(name + " is too short for a good name.")
        elif name.lower() in ['foo', 'bar', 'foobar']:
            raise TypeError(name + " is not a good name.")
        elif name.lower() in ['callback']:
            raise TypeError(name + " is a reseved thing in webidl.")
        self.data = name.strip()

class TypedPart(NamePart):
    """class for type documentation
    >>> a = TypedPart("string")
    >>> a.get()
    'string'
    """
    def __init__(self, name):
        #todo: understand super()
        if isinstance(name, ObjectDoc):
            self.data = name
        elif isinstance(name, str):
            self.data = name.strip()
            if '|' in self.data:
                raise TypeError(name + " may not have a '|'")
            elif len(self.data) < 2 and name not in ["x", "y", "z"]:
                raise TypeError(name + " is too short for a good name.")
        else:
            raise TypeError(name + " is not a string")
    @staticmethod
    def register_name(name):
        if name != '' and name not in DOC['unknown_types']:
            if True and name == 'NDMElementType':
                raise ValueError("unknown type: '" + name + "'")
            DOC['unknown_types'].append(name)
    @staticmethod
    def register_name_part(full_name):
        list_of = BasicDoc.splittype(full_name, '.')
        name = ''
        for i, n in enumerate(list_of[:-1]):
            TypedPart.register_name(".".join(list_of[:i]))


class DescriptionPart(DocPart):
    "Class for description documentation"

    def __init__(self, description, dotify=True):
        """Assure that the description is a string"
        >>> a = DescriptionPart("test")
        >>> print(a)
        test.
        """

        if not isinstance(description, str):
            raise TypeError(description + " is not a string")

        if description and len(description.strip()) < 3 and description not in ["?", "??"]:
            raise TypeError(description + " is too short for a good description.")

        self.data = (self.dotstr(description) if dotify else description).strip()

    @staticmethod
    def dotstr(text):
        """ Asure that the text is starting with a captial and ending with a '.'
        >>> DescriptionPart.dotstr("a")
        'a.'
        >>> DescriptionPart.dotstr("a.")
        'a.'
        >>> DescriptionPart.dotstr("")
        ''
        """
        if isinstance(text, str):
            if len(text) > 0 and text[-1] != '.':
                text += '.'
        return text

class BoolPart(DocPart):
    def __init__(self, value):
        """Assure that this is a boolean.
        >>> a = BoolPart(True)
        >>> a.get()
        'true'
        >>> a = BoolPart(False)
        >>> a.get()
        'false'
        """
        if not isinstance(value, bool):
            raise TypeError(str(value) + " is not a boolean")
        self.data = value

    def __str__(self):
        """true if so, etc."""
        if self.data:
            return 'true'
        return 'false'

    def value(self):
        return self.data

class LanguagePart(DocPart):
    def __init__(self, value):
        """Assure that language is a string and is a valid language.
        >>> a = LanguagePart("python")
        >>> a.get()
        'python'
        """
        if not isinstance(value, str):
            raise TypeError(value + " is not a string")
        elif value.strip().lower() not in ['javascript', 'python', 'c', 'c++', 'gl', 'redcode']:
            raise TypeError(value + " is not an allowed languague")
        self.data = value.strip().lower()

class CodePart(DocPart):
    def __init__(self, code):
        """Assure that code is a string and that it is stripped of whitespace.
        >>> a = CodePart('size_t * p; ')
        >>> a.get()
        'size_t * p;'
        """
        if not isinstance(code, str):
            raise TypeError(code + " is not a string")
        self.data = code.strip()

class ProductPart(DocPart):
    def __init__(self, products):
        if isinstance(products, list) or products is None:
            self.data = products
        else:
            raise TypeError(str(products) + " must be a list or None")

    def __str__(self):
        if self.data:
            return ", ".join(self.data)
        else:
            return ""

    def get(self):
        return self.data;

class DefaultPart(DocPart):
    def __init__(self, value=None):
        """Assure that the default is None, integer, or a string
        >>> a = DefaultPart()
        >>> a.get()
        'None'
        >>> a = DefaultPart(1111)
        >>> a.get()
        '1111'
        >>> a = DefaultPart('2222')
        >>> a.get()
        '2222'
        """

        #TODO: link this default with the FieldDoc/ParamDoc type
        if value is None or isinstance(value, int) or isinstance(value, str):
            self.data = value
        else:
            raise TypeError(str(value) + " is not of NoneType, integer, or string")

    def __str__(self):
        return str(self.data)

### DOCS ###

class BasicDoc(object):
    """An abstract class, that can spit out the formatted documentation."""
    def __init__(self):
        """
        >>> a = BasicDoc()
        >>> type(a)
        <class '__main__.BasicDoc'>

        """
        pass

    def get_key(self):
        return "base"

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        return {}

    def assure_list_of_type(self, list_of, variable_name, cls):
        """Assure that the variable variable_name as parameter 'list_of' is a list of class cls
        >>> a = BasicDoc()
        >>> s = SeesDocs("aa|ee")
        >>> ss =a.assure_list_of_type(s, "sees", SeeDoc)
        >>> len(ss)
        2
        """
        if not isinstance(list_of, list):
            raise TypeError(variable_name.title() + "'s variable should be a list")
        for i in list_of:
            if type(i) != cls:
                if cls.__name__ == 'ParamDoc' and type(i).__name__ != 'CallbackDoc':
                    raise TypeError(variable_name.title() + "'s variable should be of type " + cls.__name__)
        return list_of
    @staticmethod
    def splittype(typed, sep='|'):
        """Splits a string into a list, eventually by using a '|'
        >>> BasicDoc.splittype('he')
        ['he']
        >>> dummy = BasicDoc()
        >>> dummy.splittype('he')
        ['he']

        >>> dummy.splittype(None)
        []
        >>> dummy.splittype("h|e")
        ['h', 'e']
        >>> dummy.splittype('h|e', "-")
        ['h|e']

        >>> dummy.splittype("h-e", "-")
        ['h', 'e']
        """
        if typed is None:
            return []
        elif type(typed).__name__ == 'str':
            if sep in typed:
                typed = typed.split(sep)
            else:
                typed = [typed]
        return typed


class TechnicalDoc(BasicDoc):
    """An abstract class, that is just a convinient constructor and formatter."""
    def __init__(self, name, description):
        """
        >>> a = TechnicalDoc("tech", "Tech")
        >>> a.name.get()
        'tech'
        >>> a.description.get()
        'Tech.'
        """
        super(TechnicalDoc, self).__init__()
        self.name = NamePart(name)
        typed = type(self).__name__
        class_name = self.name.get()
        entry_name = self.name.get()

        #todo refractor this whole 'typed' thing: https://xkcd.com/1421/
        if typed == 'NamespaceDoc' or typed == 'ClassDoc':
            pass
        elif '.' in self.name.get():
            class_name = self.name.get()[:self.name.get().index('.')]

        key = self.get_key()
        add = False
        dotifyDescription = True

        if not class_name in DOC['classes']:
            add = True

        if typed == 'EventDoc':
            # Store the name of the event instead of Class.event
            entry_name = entry_name[entry_name.index('.') + 1:]
        elif typed == 'ReturnDoc' or typed == 'ParamDoc' or typed == 'CallbackDoc':
            add = False
            dotifyDescription = False
        elif typed == 'DetailDoc' or typed == 'BasicDoc' or typed == 'TechnicalDoc':
            add = False

        self.description = DescriptionPart(description, dotify=dotifyDescription)

        if add:
            DOC['classes'][class_name] = {
                'events': {},
                'properties': {},
                'methods': {},
                'static_methods': {},
                'constructors': {},
                'base': {class_name: {}}
            }

        if key:
            DOC['classes'][class_name][key][entry_name] = self

    def get_key(self):
        return None

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        data = super(TechnicalDoc, self).to_dict(variant)
        data['name'] = self.name.get()
        data['description'] = self.description.get()
        return data

class DetailDoc(TechnicalDoc):
    """An abstract class, that is just a convinient constructor and formatter. """
    #@TODO: Since, deprecated
    def __init__(self, name, description, sees=NO_Sees, examples=NO_Examples, is_static=IS_Dynamic, is_public=IS_Public, products=None):
        """
        >>> a = DetailDoc("Detail", "Devil is in the detail",NO_Sees, NO_Examples, IS_Static, IS_Private)
        >>> a.is_public.value()
        False

        >>> a.is_static.value()
        True
        """
        if sees is None:
            sees = []

        if examples is None:
            examples = []

        self.sees = self.assure_list_of_type(sees, "see", SeeDoc)
        self.examples = self.assure_list_of_type(examples, "examples", ExampleDoc)
        self.is_public = BoolPart(is_public)
        self.is_static = BoolPart(is_static)
        self.products = ProductPart(products)

        super(DetailDoc, self).__init__(name, description)

    def get_key(self):
        return None

    def to_markdown(self):
        """Output prepared for copy and pasting to nidiums backoffice website"""
        lines = ""
        lines += "__" + self.name.get() + "__\n\n" + self.description.get() + "\n"
        lines += "__Public__: " + self.is_public.get() + "\n"
        lines += "__Static__: " + self.is_static.get() + "\n"
        if len(self.sees) > 0:
            lines += "__Sees__:" + "\n"
            for see in self.sees:
                if self.name.get() is not see.data.get():
                    lines += see.to_markdown()
        if len(self.examples) > 0:
            lines += "\n__Examples__:" + "\n"
            for example in self.examples:
                lines += example.to_markdown()
        lines += "\n"
        return lines

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        data = super(DetailDoc, self).to_dict(variant)
        data['is_public'] = self.is_public.value()
        data['is_static'] = self.is_static.value()
        data['sees'] = []
        data['examples'] = []

        if self.products.get():
            data['products'] = self.products.get()

        if len(self.sees) > 0:
            for see in self.sees:
                if self.name.get() !=  see.data.get():
                    data['sees'].append(see.to_dict(variant))
        if len(self.examples) > 0:
            for example in self.examples:
                data['examples'].append(example.to_dict(variant))
        return data

class NamespaceDoc(DetailDoc):
    """This handles 'namespaces, witch are placeholders/castrated classes."""

    def __init__(self, name, description, sees=None, examples=NO_Examples, section=None, products=None):
        """
        >>> a = NamespaceDoc('Math', 'Math namespace', NO_Sees, NO_Examples)
        >>> type(a.examples)
        <type 'list'>
        >>> len(a.examples)
        0
        >>> type(a.sees)
        <type 'list'>
        >>> len(a.sees)
        0
        >>> a.is_static.value()
        True
        >>> a.is_public.value()
        True
        """

        super(self.__class__, self).__init__(name, description, sees, examples, is_static=IS_Static, is_public=IS_Public, products=products)
        TypedPart.register_name(self.name.get())

        self.section = NamePart(section) if section else None

    def get_key(self):
        return "base"

    def to_markdown(self):
        """Output prepared for copy and pasting to nidiums backoffice website"""

        return super(NamespaceDoc, self).to_markdown()

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""

        data = super(self.__class__, self).to_dict(variant)

        if self.section:
            data["section"] = self.section.get()

        return data

class ClassDoc(DetailDoc):
    "This handles classes"

    def __init__(self, name, description, sees=None, examples=NO_Examples, inherrits=None, extends=None, section=None, products=None):
        """
        >>> a = ClassDoc('Console', 'Log interface', NO_Sees, NO_Examples, NO_Inherrits, NO_Extends)
        >>> type(a.inherrits)
        <type 'list'>
        >>> len(a.inherrits)
        0
        >>> type(a.extends)
        <type 'list'>
        >>> len(a.extends)
        0
        >>> a = ClassDoc('Console', 'Log interface', NO_Sees, NO_Examples, "Dummy", "Drop|Pord")
        >>> len(a.inherrits)
        1
        >>> a.inherrits[0].get()
        'Dummy'
        >>> len(a.extends)
        2
        >>> a.extends[0].get()
        'Drop'
        >>> a.extends[1].get()
        'Pord'
        """

        super(self.__class__, self).__init__(name, description, sees, examples, is_static=IS_Static, is_public=IS_Public, products=products)
        TypedPart.register_name(self.name.get())

        if inherrits is None:
            inherrits = []

        if extends is None:
            extends = []

        self.inherrits = OopDocs(inherrits)
        self.extends = OopDocs(extends)
        self.section = NamePart(section) if section else None

    def get_key(self):
        return "base"

    def to_markdown(self):
        """Output prepared for copy and pasting to nidiums backoffice website"""

        lines = super(self.__class__, self).to_markdown()

        if len(self.inherrits) > 0:
            lines += "\n__Inherrits__:" + "\n"
            for inherrit in self.inherrits:
                lines += inherrit

        if len(self.extends) > 0:
            lines += "\n__Extends__:" + "\n"
            for examp in self.extends:
                lines += examp

        return lines

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""

        data = super(self.__class__, self).to_dict(variant)

        data['inherrits'] = []
        data['extends'] = []

        if self.section:
            data["section"] = self.section.get()

        for inh in self.inherrits:
            data['inherrits'].append(inh.get())

        for ext in self.extends:
            data['extends'].append(ext.get())

        return data

class FunctionDoc(DetailDoc):
    """
    This handles functions and methods
    """
    def __init__(self, name, description, sees=None, examples=NO_Examples, is_static=IS_Dynamic, is_public=IS_Public, is_slow=IS_Fast, params=NO_Params, returns=NO_Returns, products=None):
        """
        >>> a = FunctionDoc('console.log', 'Log shit', NO_Sees, NO_Examples, IS_Dynamic, IS_Public, IS_Slow, [ParamDoc('text', 'The Text', 'string', "")])
        >>> a.params[0].default.get()
        ''
        >>> type(a.returns).__name__
        'NoneType'
        >>> len(a.params)
        1
        >>> len(a.params[0].typed)
        1
        >>> a.params[0].typed[0].get()
        'string'
        >>> a.is_constructor.value()
        False
        >>> a.is_slow.value()
        True
        >>> a = FunctionDoc('max', 'max 2 valuest', NO_Sees, NO_Examples, IS_Dynamic, IS_Public, IS_Slow, [ParamDoc('v1', 'value 1', 'integer|float', "1"), ParamDoc('v2', 'value 2', 'integer|float', "1")], ReturnDoc("highest", "integer|float"))
        >>> type(a.returns).__name__
        'ReturnDoc'
        >>> len(a.returns.typed)
        2
        >>> a.returns.typed[0].get()
        'integer'
        >>> a.returns.typed[1].get()
        'float'
        """
        super(FunctionDoc, self).__init__(name, description, sees, examples, is_static, is_public, products=products)
        self.is_constructor = BoolPart(False)
        self.is_slow = BoolPart(is_slow)
        if params is None:
            params = []
        self.returns = returns
        self.params = self.assure_list_of_type(params, "params", ParamDoc)

    def get_key(self):
        return "static_methods" if self.is_static.value() else "methods"

    def to_markdown(self):
        """Output prepared for copy and pasting to nidiums backoffice website"""
        lines = super(FunctionDoc, self).to_markdown()
        if self.params > 0:
            lines += "\n__Parameters__:" + "\n"
            for param in self.params:
                lines += param.to_markdown()
        lines += "__Constructor__:" + self.is_constructor.get() + "\n"
        if self.is_slow.value():
            lines += ">**Warning:**\n>as `" + self.name.get() + "` is a synchronous method, it will block nidium and the UI until the reading process is complete"
        if self.returns:
            lines += "\n__Returns__:" + self.returns.to_markdown() + "\n"
        return lines

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        data = super(FunctionDoc, self).to_dict(variant)
        data['is_constructor'] = self.is_constructor.value()
        data['is_slow'] = self.is_slow.value()
        data['params'] = []
        for param in self.params:
            data['params'].append(param.to_dict(variant))
        if self.returns:
            data['returns'] = self.returns.to_dict(variant)
        else:
            data['returns'] = None
        return data

class ConstructorDoc(FunctionDoc):
    """
    This handles constructors for classes. A constructor is just a function
    """
    def __init__(self, name, description, sees=None, examples=NO_Examples, params=NO_Params, returns=NO_Returns):
        """
        >>> a = ConstructorDoc('Webserver', 'Webserver constructor', NO_Sees, NO_Examples, NO_Params, ReturnDoc('instance', 'Webserver'))
        >>> a.is_constructor.value()
        True

        >>> type(a.returns).__name__
        'ReturnDoc'
        >>> len(a.returns.typed)
        1
        >>> a.returns.typed[0].get()
        'Webserver'
        """
        super(self.__class__, self).__init__(name, description, sees, examples, IS_Dynamic, IS_Public, IS_Fast, params, returns)
        self.is_constructor = BoolPart(True)
        TypedPart.register_name_part(self.name.get())

    def get_key(self):
        return "constructors"

    def to_markdown(self):
        """Output prepared for in markdown format."""
        return super(self.__class__, self).to_markdown()

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        return super(self.__class__, self).to_dict(variant)

class FieldDoc(DetailDoc):
    """
    This handles fields, also known as properties
    """
    def __init__(self, name, description, sees=None, examples=NO_Examples, is_static=IS_Dynamic, is_public=IS_Public, is_readonly=IS_Readonly, typed=NO_Typed, default=NO_Default, products=None):
        """
        >>> a = FieldDoc('age', "The persons age", NO_Sees, NO_Examples, IS_Dynamic, IS_Static, IS_Readonly, 'int', NO_Default)
        >>> type(a)
        <class '__main__.FieldDoc'>
        >>> len(a.typed)
        1
        >>> a.typed[0].get()
        'int'
        >>> a.default.get()
        'None'
        >>> a.is_readonly.value()
        True
        >>> a = FieldDoc('age', "The persons age", NO_Sees, NO_Examples, IS_Dynamic, IS_Static, IS_ReadWrite, 'int', 30)
        >>> a.default.get()
        '30'
        >>> a.is_readonly.value()
        False
        """
        super(self.__class__, self).__init__(name, description, sees, examples, is_static, is_public, products=products)
        self.is_readonly = BoolPart(is_readonly)
        self.default = DefaultPart(default)
        self.typed = TypedDocs(typed)

    def get_key(self):
        return "properties"

    def to_markdown(self):
        """Output prepared in markdown format."""
        lines = ""
        types = []
        for typed in self.typed:
            if type(typed).__name__ == 'ObjectDoc':
                types.append(typed.to_markdown())
            else:
                types.append(typed.get())
        lines += self.name.get() + "\t'" + "', '".join(types) + "'\t" + self.is_readonly.get() + "\t" + self.description.get()
        return lines

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        data = super(self.__class__, self).to_dict(variant)
        data['typed'] = []
        data['is_readonly'] = self.is_readonly.value()
        for typed in self.typed:
            if type(typed).__name__ == 'ObjectDoc':
                data['typed'].append(typed.to_dict(variant))
            else:
                data['typed'].append(typed.get())
        return data

class ReturnDoc(TechnicalDoc):
    """This handles returns of functions/methods/constructors."""
    def __init__(self, description, typed, nullable=False):
        """
        >>> a = ReturnDoc('The new Person', 'Person')
        >>> len(a.typed)
        1
        >>> a.typed[0].get()
        'Person'
        >>> a = ReturnDoc('The new Person', 'Person|Animal')
        >>> len(a.typed)
        2
        >>> a.nullable
        False
        >>> a.typed[0].get()
        'Person'
        >>> a.typed[1].get()
        'Animal'
        >>> a = ReturnDoc('The new Person', ['Person', 'Animal'], nullable=True)
        >>> len(a.typed)
        2
        >>> a.typed[0].get()
        'Person'
        >>> a.typed[1].get()
        'Animal'
        >>> a.nullable
        True
"""
        super(self.__class__, self).__init__("returnVariable", description)
        self.typed = TypedDocs(typed)
        self.nullable = nullable

    def get_key(self):
        return None

    def to_markdown(self):
        """Output prepared in markdown format."""
        lines = ""
        types = []
        for typed in self.typed:
            if type(typed).__name__ == 'ObjectDoc':
                types.append(typed.to_markdown())
            else:
                types.append(typed.get())
        if self.nullable and 'null' not in types:
            types.append('null')
        lines += "'" +  "', '".join(types) + "'\t" + self.description.get()
        return lines

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        data = super(self.__class__, self).to_dict(variant)
        data['typed'] = []
        data['nullable'] = self.nullable
        for typed in self.typed:
            if type(typed).__name__ == 'ObjectDoc':
                data['typed'].append(typed.to_dict(variant))
            else:
                data['typed'].append(typed.get())
        return data

class ParamDoc(TechnicalDoc):
    """This handles Parameters to functions/methods/constructors."""
    def __init__(self, name, description, typed=NO_Typed, default=NO_Default, is_optional=IS_Obligated):
        """
        >>> a = ParamDoc('sql', 'Sql statement to run', 'string', NO_Default, IS_Obligated)
        >>> len(a.typed)
        1
        >>> a.typed[0].get()
        'string'
        >>> a.default.get()
        'None'
        >>> a.is_optional.value()
        False
        >>> a = ParamDoc('port', 'Port to listen to', 'string|int', 8080)
        >>> len(a.typed)
        2
        >>> a.typed[0].get()
        'string'
        >>> a.typed[1].get()
        'int'
        >>> a.is_optional.value()
        False
        >>> a.default.get()
        '8080'
        >>> a = ParamDoc('port', 'Port to listen to', ['string', 'int'], 8080, IS_Optional)
        >>> len(a.typed)
        2
        >>> a.typed[0].get()
        'string'
        >>> a.typed[1].get()
        'int'
        >>> a.is_optional.value()
        True
        """
        super(ParamDoc, self).__init__(name, description)
        self.default = DefaultPart(default)
        self.is_optional = BoolPart(is_optional)
        self.typed = TypedDocs(typed)

    def get_key(self):
        return None

    def to_markdown(self):
        """Output prepared in markdown format."""
        lines = ''
        types = []
        for typed in self.typed:
            if type(typed).__name__ == 'ObjectDoc':
                types.append(typed.to_markdown())
            else:
                types.append(typed.get())
        lines += self.name.get() + "\t'" + "', '".join(types) + "'\t" + self.is_optional.get() + "\t" + self.description.get()
        return lines

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        data = super(ParamDoc, self).to_dict(variant)
        data['typed'] = []
        for typed in self.typed:
            if type(typed).__name__ == 'ObjectDoc':
                data['typed'].append(typed.to_dict(variant))
            else:
                data['typed'].append(typed.get())
        data['default'] = self.default.get()
        data['is_optional'] = self.is_optional.value()
        return data

class EventDoc(FunctionDoc):
    """
    This handles events.
    Events are basically callbacks/functions that can be triggered everywhere in the class code
    """
    def __init__(self, name, description, sees=NO_Sees, examples=NO_Examples, params=NO_Params):
        """
        >>> a = EventDoc('Classer.onError', 'This will be called if an error occurs', NO_Sees, NO_Examples, [ParamDoc('err', 'errorcode', 'integer', 111)])
        >>> type(a.params)
        <type 'list'>
        >>> a.params[0].default.get()
        '111'
        """
        super(self.__class__, self).__init__(name, description, sees, examples)
        if params is None:
            params = []
        self.params = self.assure_list_of_type(params, "params", ParamDoc)

    def get_key(self):
        return "events"

    def to_markdown(self):
        """Output prepared in markdown format."""
        lines = ''
        if self.params > 0:
            lines += "\n__Parameters__:" + "\n"
            for param in self.params:
                lines += param.to_markdown()
        return super(self.__class__, self).to_markdown()
    def to_dict(self, variant=''):

        """Prepare a normal interface to export data."""
        data = super(self.__class__, self).to_dict(variant)
        data['params'] = []
        for param in self.params:
            data['params'].append(param.to_dict(variant))
        return data

class CallbackDoc(ParamDoc):
    """
    This handles parameters that are callback-functions/methods.
    These differ because a callback function has parameters that need to be documented as well
    """
    def __init__(self, name, description, params=NO_Params, default=NO_Default, is_optional=IS_Obligated):
        """
        >>> a = CallbackDoc('cb', 'The function that will be called', [ParamDoc('res', 'result', 'string', NO_Default)])
        >>> type(a.params)
        <type 'list'>
        >>> type(a.params[0])
        <class '__main__.ParamDoc'>
        >>> a.is_optional.value()
        False
        >>> a = CallbackDoc('cb', 'The function that will be called', NO_Params)
        >>> type(a.params)
        <type 'list'>
        >>> len(a.params)
        0
        >>> a = CallbackDoc('cb', 'The function that will be called', [ParamDoc('res', 'result', 'string', NO_Default, IS_Obligated)])
        >>> type(a.params)
        <type 'list'>
        >>> len(a.params)
        1
        """
        super(CallbackDoc, self).__init__(name, description, 'function', default, is_optional)
        if params is None:
            params = []
        self.params = self.assure_list_of_type(params, "params", ParamDoc)

    def get_key(self):
        return None

    def to_markdown(self):
        """Output prepared in markdown format."""
        lines = ''
        extra = ""
        for param in self.params:
            types = []
            if isinstance(param.typed, list):
                for tpy in param.typed:
                    if type(tpy).__name__ == 'ObjectDoc':
                        types.append(tpy.to_markdown())
                    else:
                        types.append(tpy.get())
            elif type(param.types).__name__ == 'ObjectDoc':
                types = [param.typed.to_markdown()]
            else:
                types = [param.typed.get()]
            extra += param.name.get() + "\t'" + "', '".join(types) + "'\t" + param.is_optional.get() + "\t" + param.description.get() + "\n"
        lines += self.name.get() + "\t" + "'callback'" + "\t" + self.is_optional.get() + "\t" + self.description.get() + extra
        return lines

    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        data = super(self.__class__, self).to_dict(variant)
        data['is_optional'] = self.is_optional.value()
        data['params'] = []
        for i in self.params:
            data['params'].append(i.to_dict(variant))
        return data

class ExampleDoc(BasicDoc):
    """
    This handles examples
    """
    def __init__(self, example, title="", lang='javascript', run_code=True):
        """
        >>> a = ExampleDoc('''var a = {} ''')
        >>> a.data.get()
        'var a = {}'
        >>> a.language.get()
        'javascript'
        >>> a.run_code
        True
        >>> a = ExampleDoc('''mov 0, 1''', "wtf", '''redcode''', False)
        >>> a.language.get()
        'redcode'
        >>> a.title.get()
        'wtf.'
        >>> a.run_code
        False
        >>> a = ExampleDoc('''var a = {} ''', run_code=False)
        >>> a.wrap_code()[:11]
        'if(false) {'
        """
        super(self.__class__, self).__init__()
        self.data = CodePart(example)
        self.title = DescriptionPart(title)
        self.language = LanguagePart(lang)
        self.run_code = run_code
    def wrap_code(self):
        """wrap the code in a block, so that it will not be executed, but syntax is checked"""
        lines = self.data.get()
        if lines == None or self.run_code:
            return lines
        return "if(false) {\n\t" + "\n\t\t".join(lines.splitlines()) + "\n}"
    def to_markdown(self):
        """Output prepared for in markdown format."""
        return "```" + self.language.get() + "\n" + self.data.get() + "\n```"
    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        data = super(self.__class__, self).to_dict(variant)
        if variant == 'exampletest':
            data['data'] = self.wrap_code()
        else:
            data['data'] = self.data.get()
        data['language'] = self.language.get()
        data["title"] = self.language.get()
        return data

class SeeDoc(BasicDoc):
    """
    This handles see's
    """
    def __init__(self, see):
        """
        >>> a = SeeDoc('dummy')
        >>> a.data.get()
        'dummy'
        >>> a.to_dict()
        {'data': 'dummy'}
        >>> a.to_markdown()
        '__dummy__'
        """
        if "|" in see:
            raise TypeError("SeeDoc may not have a '|'. 'SeesDocs' to for your convienience.")
        super(self.__class__, self).__init__()
        self.data = NamePart(see)
        TypedPart.register_name_part(self.data.get())
    def to_markdown(self):
        """Output prepared for in markdown format."""
        return "__" + self.data.get() + "__"
    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        data = super(self.__class__, self).to_dict(variant)
        data['data'] = self.data.get()
        return data

def SplitDocs(list_of, cls):
    """
    Builds a list of InherritsDoc's based on a string with '|'
    >>> a = SplitDocs("dummy1", SeeDoc)
    >>> a[0].data.get()
    'dummy1'
    >>> a = SplitDocs("dummy1|dummy2", SeeDoc)
    >>> a[0].data.get()
    'dummy1'
    >>> a[1].data.get()
    'dummy2'
    """
    if not list_of:
        list_of = []
    elif isinstance(list_of, str):
        list_of = BasicDoc.splittype(list_of)
    if isinstance(list_of, list):
        for i, item in enumerate(list_of):
            list_of[i] = cls(item)
    else:
        raise TypeError("Expected a string to generate a list of class: '" + cls.__name__ + "'")
    return list_of

class ObjectDoc(BasicDoc):
    """
    This handles object definitions (for instance in return types)"
    """
    def __init__(self, obj, is_array=IS_Single):
        """
        >>> a = ObjectDoc([])
        >>> a.data
        []
        >>> a = ObjectDoc([("key", "text", 'integer')])
        >>> a.data[0][0].get()
        'key'
        >>> a.data[0][1].get()
        'text'
        >>> a.data[0][2][0].get()
        'integer'
        >>> a.is_array
        False
        >>> a.to_markdown()
        '[key: text (integer)]'
        >>> a.to_dict()
        {'type': 'Object', 'name': 'JS Object', 'details': [{'default': 'None', 'typed': ['integer'], 'name': 'key', 'description': 'text'}]}
        >>> a = ObjectDoc([("key", "text", 'integer')], IS_Array)
        >>> a.is_array
        True
        """
        #todo automatically [] if it is not a list
        super(self.__class__, self).__init__()
        self.sees = self.assure_list_of_type(obj, "Object", tuple)
        self.data = []
        self.is_array = is_array
        for tpl in obj:
            if len(tpl) < 3:
                raise ValueError("ObjectDoc() key/value description expect at least 3 element (name, description, type, [default])")
            name = NamePart(tpl[0])
            description = DescriptionPart(tpl[1], dotify=False)
            typed = TypedDocs(tpl[2])
            default = DefaultPart()
            if len(tpl) > 3:
                default = DefaultPart(tpl[3])

            self.data.append((name, description, typed, default))

    def to_markdown(self):
        """Output prepared for in markdown format."""
        lines = ""
        data = []
        for name, description, typed, default in self.data:
            types = []
            for tpy in typed:
                if isinstance(tpy, list):
                    types.append(tpy.to_markdown())
                elif type(tpy).__name__ == 'ObjectDoc':
                    types.append(tpy.to_markdown())
                else:
                    types.append(tpy.get())
            data.append(name.get() + ": " + description.get() + " (" + ",".join(types) + ")")
        lines += "[" + ", ".join(data) + "]"
        if self.is_array:
            lines = "[" + lines + "]"
        return lines
    def to_dict(self, variant=''):
        """Prepare a normal interface to export data."""
        details = []
        for name, description, typed, default in self.data:
            types = []
            for tpy in typed:
                if isinstance(tpy, list):
                    types.append(tpy.to_dict(variant))
                elif type(tpy).__name__ == 'ObjectDoc':
                    types.append(tpy.to_dict(variant))
                else:
                    types.append(tpy.get())
            details.append({'name': name.get(), 'description': description.get(), 'typed': types, 'default': default.get()})
        data = {'name': 'JS Object', 'details': details, 'type': 'Object'}
        if self.is_array:
            data = [data]
        return data

def SeesDocs(list_of=None):
    return SplitDocs(list_of, SeeDoc)

def OopDocs(list_of=None):
    list_of = SplitDocs(list_of, NamePart)
    for i in list_of:
        TypedPart.register_name(i.get())
    return list_of

def TypedDocs(list_of=None):
    if type(list_of).__name__ == 'ObjectDoc':
        return [list_of]
    list_of = SplitDocs(list_of, TypedPart)
    for i in list_of:
        TypedPart.register_name(i.get())
    return list_of

def check(docs):
    defined_types = []
    for known in docs['classes'].keys():
        defined_types.append(known)
        defined_types.append("[" + known + "]")
    for known in IGNORE_TYPES:
        defined_types.append(known)
        defined_types.append("[" + known + "]")
    missing = []
    for i in docs['unknown_types']:
        if i not in defined_types:
            missing.append(i)
    return missing

def report(variant, docs):
    "dump it in a layout"
    data = {}
    sections = {}
    classLookup = {}

    # First create a lookup table with all namespace or top level class
    # and populate the sections list
    for class_name, class_details in docs['classes'].items():
        klass = class_details["base"][class_name]

        if isinstance(klass, dict):
            continue

        classLookup[class_name] = klass

        section = class_details["base"][class_name].section
        if section:
            section = section.get()
            if section not in sections:
                sections[section] = []

            sections[section].append(class_name)
        elif class_name not in sections:
            sections[class_name] = []

    for class_name, class_details in docs['classes'].items():
        count = 0
        section = None
        data[class_name] = {}
        klass = class_details["base"][class_name]

        if not isinstance(klass, dict):
            section = class_details["base"][class_name].section
            if section:
                section = section.get()

        if klass.products.get() == None:
            # No products defined for this item, lets check if the section has it
            if section in classLookup:
                klass.products = classLookup[section].products

        for type_doc, type_details in class_details.items():
            data[class_name][type_doc] = {}

            for item, item_details in type_details.items():
                if isinstance(item_details, dict):
                    data[class_name][type_doc][item] = item_details
                else:
                    data[class_name][type_doc][item] = item_details.to_dict(variant)

                #if "products" not in data[class_name][type_doc][item]:
                #    data[class_name][type_doc][item]["products"] = klass.products.get()

                if type_doc != 'base':
                    count += len(data[class_name][type_doc].keys())

    if variant == 'json':
        data["_sections"] = sections
        print(json.dumps(data))
    elif variant == 'exampletest':
        code = ''
        counter = 0
        for class_name, class_details in data.items():
            code += "Tests.register('Running tests for %s', function() {});\n" % class_name
            for type_doc, type_details in class_details.items():
                for item, item_details in type_details.items():
                    if item_details.has_key('examples'):
                        for i, example in enumerate(item_details['examples']):
                            if example['language'] == 'javascript':
                                name = class_name + '.' + type_doc + "." + item + "." + str(i)
                                examplecode = "\n\t\t".join(example['data'].splitlines())
                                code += '\nTests.register("' + name + '", function() {'
                                code += "\n\tvar dummy = " + str(counter) + ';'
                                code += "\n\t\t" + examplecode
                                code += "\n\n\tAssert.equal(dummy, " + str(counter) + ');'
                                code += '\n});\n'
                                counter += 1
        print(code)
    elif variant == 'markdown':
        lines = ''
        for class_name, class_details in docs['classes'].items():
            if data.has_key(class_name):
                lines += "\n\n\n\n#" + class_name + "\n\n"
                for type_doc, type_details in class_details.items():
                    if type_doc != 'base' and len(type_details.keys()) > 0:
                        lines += "\n\n\n## " + type_doc + "\n\n"
                        for item, item_details in type_details.items():
                            lines += "\n\n### " + item + "\n\n"
                            lines += item_details.to_markdown()
        print(lines)

def process(dir_name):
    """
    Go through all the files in the dirName process the raw sourcecode
    """
    if os.path.isfile(dir_name):
        imp.load_source('DOCC', dir_name)
    else:
        for file_name in os.listdir(dir_name):
            full_file_name = os.path.join(dir_name, file_name)
            if not os.path.isdir(full_file_name):
                if os.path.splitext(full_file_name)[-1] == '.py' and file_name != '.ycm_extra_conf.py':
                    imp.load_source('DOCC', full_file_name)
            else:
                process(full_file_name)

VARIANTS = ['doctest', 'markdown', 'json', 'exampletest']
def usage():
    """Usage."""
    print("Usage: "+ sys.argv[0] + "cmd DIR [DIR2,]\n\tcmd:	'" + "', '".join(VARIANTS) + "'.")
    sys.exit(1)

def main():
    """The main routine"""
    if len(sys.argv) == 1:
        usage()
    cmd = sys.argv[1]
    if cmd == 'doctest':
        import doctest
        doctest.testmod()
    elif len(sys.argv) > 2 and cmd in VARIANTS:
        for i in range(2, len(sys.argv)):
            process(sys.argv[i])
        if not sys.modules.has_key('DOCC'):
            sys.stderr.write("No documentation found.\n")
            sys.exit(1)
        docs = sys.modules['DOCC'].DOC
        report(cmd, docs)
        missing = check(docs)
        if len(missing) > 0:
            sys.stderr.write("\nWarning: missing types: '" + "', '".join(missing) + "'\n")
    else:
        usage()
IGNORE_TYPES = ['void', 'null', 'any', 'integer', 'string', 'boolean', 'float', 'function', 'Array', 'Object', 'ArrayBuffer', 'Uint16Array', 'global']

if __name__ == '__main__':
    main()

