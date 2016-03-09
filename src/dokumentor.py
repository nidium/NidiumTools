#!/usr/bin/python
"""
Tool to generate documentation in a different way then JSDoc does

It is good practice to document API's near their implementation.
This is difficult if it concerns a scripting language that is embedded in an other program.
Such as embedding javascript (spidermonkey engine), where functionality of the hostprogram is exposed to javascript scripts.

This tool tries to make it easier
"""
import sys, os, imp, json

DOC = {'classes': {}}

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
		if name == '':
			raise TypeError(name + " must have some characters")
		self.data = name

class TypedPart(NamePart):
	"""class for type documentation
	>>> a = TypedPart("string")
	>>> a.get()
	'string'
	>>> a.is_normal_type(["char"])
	False
	>>> a.is_normal_type(["string"])
	True
	"""
	def __init__(self, name):
		#todo: understand super()
		if not isinstance(name, str):
			raise TypeError(name + " is not a string")
		if '|' in name:
			raise TypeError(name + " may not have a '|'")
		self.data = name
	def is_normal_type(self, types):
		return self.data in types

class DescriptionPart(DocPart):
	"Class for description documentation"
	def __init__(self, description):
		"""Assure that the description is a string"
		>>> a = DescriptionPart("test")
		>>> print(a)
		Test.
		"""
		if not isinstance(description, str):
			raise TypeError(description + " is not a string")
		if '|' in description:
			raise TypeError(description + " may not have a '|'")
		if len(description) < 2:
			raise TypeError(description + " is too short")
		self.data = self.dotstr(description)
	@staticmethod
	def dotstr(text):
		""" Asure that the text is starting with a captial and ending with a '.'
		>>> DescriptionPart.dotstr("a")
		'A.'
		>>> DescriptionPart.dotstr("a.")
		'A.'
		>>> DescriptionPart.dotstr("")
		''
		"""
		if isinstance(text, str):
			text = text.title()
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
			raise TypeError(value + " is not a boolean")
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
		elif value.strip() not in ['javascript', 'python', 'c', 'c++', 'glgs', 'redcode']:
			raise TypeError(value + " is not an allowed languague")
		self.data = value.strip()

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
			raise TypeError(value + "is not of NoneType, integer, or string")
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
	def to_dict(self):
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
				raise TypeError(variable_name.title() +"'s variable should be of type ". cls.__name__)
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

		>>> dummy.splittype("h|e")
		['h', 'e']
		>>> dummy.splittype('h|e', "-")
		['h|e']

		>>> dummy.splittype("h-e", "-")
		['h', 'e']
		"""
		if typed is None:
			return typed
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
		self.description = DescriptionPart(description)
		typed = type(self).__name__
		class_name = self.name.get()
		if typed == 'NamespaceDoc' or typed == 'ClassDoc':
			pass
		elif '.' in self.name.get():
			class_name = self.name.get()[:self.name.get().index('.')]
		key = ''
		add = False
		if not class_name in DOC['classes']:
			add = True
		if typed == 'EventDoc':
			key = 'events'
		elif typed == 'FieldDoc':
			key = 'properties'
		elif typed == 'FunctionDoc':
			key = 'methods'
		elif typed == 'ConstructorDoc':
			key = 'constructors'
		elif typed == 'NamespaceDoc' or typed == 'ClassDoc':
			key = 'base'
		elif typed == 'ReturnDoc' or typed == 'ParamDoc' or typed == 'CallbackDoc':
			add = False
		elif typed == 'DetailDoc' or typed == 'BasicDoc' or typed == 'TechnicalDoc':
			add = False
		else:
			raise ValueError('A very specific bad thing happened')
		if add:
			DOC['classes'][class_name] = {'events': {}, 'properties': {}, 'methods': {}, 'constructors': {}, 'base': {class_name: {}}}
		if key != '':
			DOC['classes'][class_name][key][self.name.get()] = self
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(TechnicalDoc, self).to_dict()
		data['name'] = self.name.get()
		data['description'] = self.description.get()
		return data

class DetailDoc(TechnicalDoc):
	"""An abstract class, that is just a convinient constructor and formatter. """
	#@TODO: Since, deprecated
	def __init__(self, name, description, sees=NO_Sees, examples=NO_Examples, is_static=IS_Dynamic, is_public=IS_Public):
		"""
		>>> a = DetailDoc("Detail", "Devil is in the detail",NO_Sees, NO_Examples, IS_Static, IS_Private)
		>>> a.is_public.value()
		False

		>>> a.is_static.value()
		True
		"""
		super(DetailDoc, self).__init__(name, description)
		if sees is None:
			sees = []
		if examples is None:
			examples = []
		self.sees = self.assure_list_of_type(sees, "see", SeeDoc)
		self.examples = self.assure_list_of_type(examples, "examples", ExampleDoc)
		self.is_public = BoolPart(is_public)
		self.is_static = BoolPart(is_static)
	def to_markdown(self):
		"""Output prepared for copy and pasting to nidiums backoffice website"""
		lines = ""
		lines += "__" + self.name.get() + "__\n\n" + self.description.get() + "\n"
		lines += "__Public__: " + self.is_public.get() + "\n"
		lines += "__Static__: " + self.is_static.get() + "\n"
		if len(self.sees) > 0:
			lines += "__Sees__:" + "\n"
			for see in self.sees:
				if self.name.get() is not see.data:
					lines += see.to_markdown()
		if len(self.examples) > 0:
			lines += "\n__Examples__:" + "\n"
			for example in self.examples:
				lines += example.to_markdown()
		lines += "\n"
		return lines
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(DetailDoc, self).to_dict()
		data['is_public'] = self.is_public.get()
		data['is_static'] = self.is_static.get()
		data['sees'] = []
		data['examples'] = []
		if len(self.sees) > 0:
			for see in self.sees:
				if self.name.get() is not see.data:
					data['sees'].append(see.to_dict())
		if len(self.examples) > 0:
			for example in self.examples:
				data['examples'].append(example.to_dict())
		return data

class NamespaceDoc(DetailDoc):
	"""This handles 'namespaces, witch are placeholders/castrated classes."""
	def __init__(self, name, description, sees=None, examples=NO_Examples):
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
		super(self.__class__, self).__init__(name, description, sees, examples, True, True)
	def to_markdown(self):
		"""Output prepared for copy and pasting to nidiums backoffice website"""
		return super(NamespaceDoc, self).to_markdown()
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(self.__class__, self).to_dict()
		return data

class ClassDoc(DetailDoc):
	"This handles classes"
	def __init__(self, name, description, sees=None, examples=NO_Examples, inherrits=None, extends=None):
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
		super(self.__class__, self).__init__(name, description, sees, examples, IS_Static, IS_Public)
		if inherrits is None:
			inherrits = []
		if extends is None:
			extends = []
		self.inherrits = OopDocs(inherrits)
		self.extends = OopDocs(extends)
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
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(self.__class__, self).to_dict()
		data['inherrits'] = []
		for inh in self.inherrits:
			data['inherrits'].append(inh)
		data['extends'] = []
		for ext in self.extends:
			data['extends'].append(ext)
		return data

class FunctionDoc(DetailDoc):
	"""
	This handles functions and methods
	"""
	def __init__(self, name, description, sees=None, examples=NO_Examples, is_static=IS_Dynamic, is_public=IS_Public, is_slow=IS_Fast, params=NO_Params, returns=NO_Returns):
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
		super(FunctionDoc, self).__init__(name, description, sees, examples, is_static, is_public)
		self.is_constructor = BoolPart(False)
		self.is_slow = BoolPart(is_slow)
		if params is None:
			params = []
		self.params = self.assure_list_of_type(params, "params", ParamDoc)
		self.returns = returns
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
		if len(self.returns) > 0:
			lines += "\n__Returns__:" + "\n"
			for ret in self.returns:
				lines += ret.to_markdown()
		return lines
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(FunctionDoc, self).to_dict()
		data['is_constructor'] = self.is_constructor.get()
		data['is_slow'] = self.is_slow.get()
		data['params'] = []
		for param in self.params:
			data['params'].append(param.to_dict())
		data['returns'] = []
		for ret in self.returns:
			data['returns'].append(ret.to_dict())
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
		super(self.__class__, self).__init__(name, description, sees, examples, True, True, False, params, returns)
		self.is_constructor = BoolPart(True)
	def to_markdown(self):
		"""Output prepared for in markdown format."""
		return super(self.__class__, self).to_markdown()
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		return super(self.__class__, self).to_dict()

class FieldDoc(DetailDoc):
	"""
	This handles fields, also known as properties
	"""
	def __init__(self, name, description, sees=None, examples=NO_Examples, is_static=IS_Dynamic, is_public=IS_Public, is_readonly=IS_Readonly, typed=NO_Typed, default=NO_Default):
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
		super(self.__class__, self).__init__(name, description, sees, examples, is_static, is_public)
		self.is_readonly = BoolPart(is_readonly)
		self.default = DefaultPart(default)
		self.typed = TypedDocs(typed)
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
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(self.__class__, self).to_dict()
		data['typed'] = []
		data['is_readonly'] = self.is_readonly.get()
		for typed in self.typed:
			if type(typed).__name__ == 'ObjectDoc':
				data['typed'].append(typed.to_dict())
			else:
				data['typed'].append(typed)
		return data

class ReturnDoc(TechnicalDoc):
	"""This handles returns of functions/methods/constructors."""
	def __init__(self, description, typed):
		"""
		>>> a = ReturnDoc('The new Person', 'Person')
		>>> len(a.typed)
		1
		>>> a.typed[0].get()
		'Person'
		>>> a = ReturnDoc('The new Person', 'Person|Animal')
		>>> len(a.typed)
		2
		>>> a.typed[0].get()
		'Person'
		>>> a.typed[1].get()
		'Animal'
		>>> a = ReturnDoc('The new Person', ['Person', 'Animal'])
		>>> len(a.typed)
		2
		>>> a.typed[0].get()
		'Person'
		>>> a.typed[1].get()
		'Animal'
"""
		super(self.__class__, self).__init__("returnVariable", description)
		self.typed = TypedDocs(typed)
	def to_markdown(self):
		"""Output prepared in markdown format."""
		lines = ""
		types = []
		for typed in self.typed:
			if type(typed).__name__ == 'ObjectDoc':
				types.append(typed.to_markdown())
			else:
				types.append(typed)
		lines += "'" +  "', '".join(types) + "'\t" + self.description.get()
		return lines
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(self.__class__, self).to_dict()
		data['typed'] = []
		for typed in self.typed:
			if type(typed).__name__ == 'ObjectDoc':
				data['typed'].append(typed.to_dict())
			else:
				data['typed'].append(typed)
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
		self.typed = TypedDocs(typed)
		self.default = DefaultPart(default)
		self.is_optional = BoolPart(is_optional)
	def to_markdown(self):
		"""Output prepared in markdown format."""
		lines = ''
		types = []
		for typed in self.typed:
			if type(typed).__name__ == 'ObjectDoc':
				typed.append(typed.to_markdown())
			else:
				types.append(typed)
		lines += self.name.get() + "\t'" + "', '".join(types) + "'\t" + self.is_optional.get() + "\t" + self.description.get()
		return lines
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(ParamDoc, self).to_dict()
		data['typed'] = []
		for typed in self.typed:
			if type(typed).__name__ == 'ObjectDoc':
				data['typed'].append(typed.to_dict())
			else:
				data['typed'].append(typed)
		data['default'] = self.default.get()
		data['is_optional'] = self.is_optional.get()
		return data

class EventDoc(FunctionDoc):
	"""
	This handles events.
	Events are basically callbacks/functions that can be triggered everywhere in the class code
	"""
	def __init__(self, name, description, sees=NO_Sees, examples=NO_Examples, params=NO_Params):
		"""
		>>> a = EventDoc('onError', 'This will be called if an error occurs', NO_Sees, NO_Examples, [ParamDoc('err', 'errorcode', 'integer', 111)])
		>>> type(a.params)
		<type 'list'>
		>>> a.params[0].default.get()
		'111'
		"""
		super(self.__class__, self).__init__(name, description, sees, examples)
		if params is None:
			params = []
		self.params = self.assure_list_of_type(params, "params", ParamDoc)
	def to_markdown(self):
		"""Output prepared in markdown format."""
		return super(self.__class__, self).to_markdown()
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(self.__class__, self).to_dict()
		print(data)
		return data

class CallbackDoc(ParamDoc):
	"""
	This handles parameters that are callback-functions/methods.
	These differ because a callback function has parameters that need to be documented as well
	"""
	def __init__(self, name, description, params=NO_Params):
		"""
		>>> a = CallbackDoc('callback', 'The function that will be called', [ParamDoc('res', 'result', 'string', NO_Default)])
		>>> type(a.params)
		<type 'list'>
		>>> type(a.params[0])
		<class '__main__.ParamDoc'>
		>>> a.is_optional.value()
		False
		>>> a = CallbackDoc('callback', 'The function that will be called', NO_Params)
		>>> type(a.params)
		<type 'list'>
		>>> len(a.params)
		0
		>>> a = CallbackDoc('callback', 'The function that will be called', [ParamDoc('res', 'result', 'string', NO_Default, IS_Obligated)])
		>>> type(a.params)
		<type 'list'>
		>>> len(a.params)
		1
		"""
		super(CallbackDoc, self).__init__(name, description, 'function', NO_Default, IS_Obligated)
		if params is None:
			params = []
		self.params = self.assure_list_of_type(params, "params", ParamDoc)
	def to_markdown(self):
		"""Output prepared in markdown format."""
		lines = ''
		extra = ""
		for param in self.params:
			if isinstance(param.typed, list):
				typed = []
				for tpy in param.typed:
					if type(tpy).__name__ == 'ObjectDoc':
						typed.append(tpy.to_markdown)
					else:
						typed.append(tpy)
			elif type(param.typed).__name__ == 'ObjectDoc':
				typed = [param.typed.to_markdown()]
			else:
				typed = param.typed
			extra += param.name + "\t'" + "', '".join(typed) + "'\t" + param.is_optional.get() + "\t" + param.description.get() + "\n"
		lines += self.name.get() + "\t" + "'callback'" + "\t" + self.is_optional.get() + "\t" + self.description.get() + extra
		return lines
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(self.__class__, self).to_dict()
		data['is_optional'] = self.is_optional.get()
		data['params'] = []
		for i in self.params:
			data['params'].append(i.to_dict())
		return data

class ExampleDoc(BasicDoc):
	"""
	This handles examples
	"""
	def __init__(self, example, lang='javascript'):
		"""
		>>> a = ExampleDoc('''var a = {} ''')
		>>> a.data.get()
		'var a = {}'
		>>> a.language.get()
		'javascript'
		>>> a = ExampleDoc('''mov 0, 1''', '''redcode''')
		>>> a.language.get()
		'redcode'
		"""
		super(self.__class__, self).__init__()
		self.data = CodePart(example)
		self.language = LanguagePart(lang)
	def to_markdown(self):
		"""Output prepared for in markdown format."""
		return "```" + self.language.get() + "\n" + self.data.get() + "\n```"
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(self.__class__, self).to_dict()
		data['data'] = self.data.get()
		data['language'] = self.language.get()
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
	def to_markdown(self):
		"""Output prepared for in markdown format."""
		return "__" + self.data.get() + "__"
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		data = super(self.__class__, self).to_dict()
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


def SeesDocs(list_of=None):
	return SplitDocs(list_of, SeeDoc)

def OopDocs(list_of=None):
	return SplitDocs(list_of, NamePart)

def TypedDocs(list_of=None):
	return SplitDocs(list_of, TypedPart)

class ObjectDoc(BasicDoc):
	"""
	This handles object definitions (for instance in return types)"
	"""
	def __init__(self, obj):
		"""
		>>> a = ObjectDoc([])
		>>> a.data
		[]
		>>> a = ObjectDoc([("key", "text", 'integer')])
		>>> a.data[0][0].get()
		'key'
		>>> a.data[0][1].get()
		'Text.'
		>>> a.data[0][2][0].get()
		'integer'
		>>> a.to_markdown()
		'[key: Text. (integer)]'
		>>> a.to_dict()
		{'type': 'Object', 'name': 'JS Object', 'details': [{'typed': ['integer'], 'name': 'key', 'description': 'Text.'}]}
		"""
		#todo automatically [] if it is not a list
		super(self.__class__, self).__init__()
		self.sees = self.assure_list_of_type(obj, "Object", tuple)
		self.data = []
		for name, description, typed in obj:
			name = NamePart(name)
			description = DescriptionPart(description)
			typed = TypedDocs(typed)
			self.data.append((name, description, typed))
	def to_markdown(self):
		"""Output prepared for in markdown format."""
		lines = ""
		data = []
		for name, description, typed in self.data:
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
		return lines
	def to_dict(self):
		"""Prepare a normal interface to export data."""
		details = []
		for name, description, typed in self.data:
			types = []
			for tpy in typed:
				if isinstance(tpy, list):
					types.append(tpy.to_dict())
				elif type(tpy).__name__ == 'ObjectDoc':
					types.append(tpy.to_dict())
				else:
					types.append(tpy.get())
			details.append({'name': name.get(), 'description': description.get(), 'typed': types})
		data = {'name': 'JS Object', 'details': details, 'type': 'Object'}
		return data


def check(docs):
	"do some checks"
	#todo refractor this whole 'typed' thing: https://xkcd.com/1421/
	types_list = ['integer', 'boolean', 'float', 'string', 'mixed', 'null', 'Date', 'ArrayBuffer', 'Uint16Array', 'Array',
				  'function',	 #todo: get rid of this; only allow CallbackDoc
				  'JS Object', #'?', 'object', #todo, get rid of these; only allow ObjectDoc
				  'SocketClient', 'Canvas', 'NDMElement.color', 'Canvas2DContext', 'AudioBuffer'
				]
	for typed in list(types_list):
		types_list.append("[" + typed + "]")
	items_list = []
	for class_name, class_details in docs['classes'].items():
		types_list.append(class_name)
		types_list.append("[" + class_name + "]")
		items_list.append(class_name)
		for type_details in class_details.values():
			for item, item_details in type_details.items():
				items_list.append(item)
	for class_name, class_details in docs['classes'].items():
		for chapter, type_details in class_details.items():
			if chapter == 'base':
				if type(type_details[class_name]) == type(dict()):
					sys.stderr.write("Class/Namespace '" + class_name + "' is not defined.\n")
					sys.exit(1)
			for item, item_details in type_details.items():
				chapters = [#'sees',
					'inherrits', 'extends', 'constructors', 'returns', 'events', 'params', 'properties']
				for ch in chapters:
					if hasattr(item_details, ch):
						ch_details = getattr(item_details, ch)
						for ch_detail in ch_details:
							if hasattr(ch_detail, "typed"):
								if type(getattr(ch_detail, "typed")).__name__ == 'ObjectDoc':
									for name_description_typed in ch_detail.typed.data:
										typed = name_description_typed[2]
										if not isinstance(typed, list):
											typed = [typed]
										for obtyped in typed:
											if type(obtyped).__name__ != 'ObjectDoc' and obtyped not in types_list:
												#todo, refractor, recurse
												sys.stderr.write("The type '" + obtyped + "' in " + item + "'s ObjectDoc is not defined.\n")
												sys.exit(1)
								else:
									for typed in ch_detail.typed:
										if type(typed).__name__ == 'ObjectDoc':
											pass
										elif type(typed).__name__ == 'CallbackDoc':
											for cbtyped in typed.params:
												for cbtyped in typed.typed:
													if cbtyped not in types_list:
														sys.stderr.write("The type '" + cbtyped + "' in " + item + "'s CallbackDoc is not defined.\n")
														sys.exit(1)
										elif typed not in types_list:
											print(typed)
											sys.stderr.write("'" + typed + "' in " +  item + "'s documentation (" + ch + ") is not defined.\n")
											sys.exit(1)

def report(variant, docs):
	"dump it in a layout"
	data = {}
	for class_name, class_details in docs['classes'].items():
		data[class_name] = {}
		count = 0
		for type_doc, type_details in class_details.items():
			data[class_name][type_doc] = {}
			for item, item_details in type_details.items():
				data[class_name][type_doc][item] = item_details.to_dict()
				if type_doc != 'base':
					count += len(data[class_name][type_doc].keys())
		if count == 0 and class_name != 'global':
			del data[class_name]
	if variant == 'json':
		print(json.dumps(data))
	elif variant == 'exampletest':
		code = ''
		counter = 0
		for class_name, class_details in data.items():
			for type_doc, type_details in class_details.items():
				for item, item_details in type_details.items():
					for i, example in enumerate(item_details['examples']):
						if example['language'] == 'javascript':
							name = class_name + '.' + type_doc + "." + item + "." + str(i)
							examplecode = "\n\t\t".join(example['data'].splitlines())
#							examplecode = "\n\ttry {\n\t\t" + examplecode + "\n\t} catch(err) {\n\t\tconsole.log('Syntax error in example code; Go fix `" + name + "`!' + err.message);\n\t}"
							code += '\nTests.register("' + name + '", function() {'
							code += "\n\tvar dummy = " + str(counter) + ';'
							code += "\n\t\t" + examplecode
							code += "\n\n\tAssert.equal(dummy, " +str(counter) +');'
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

def process_dir_recurse(dir_name):
	"""
	Go through all the files in the dirName process the raw sourcecode
	"""
	for file_name in os.listdir(dir_name):
		full_file_name = os.path.join(dir_name, file_name)
		if not os.path.isdir(full_file_name):
			if os.path.splitext(full_file_name)[-1] == '.py' and file_name != '.ycm_extra_conf.py':
				#print("#Reading " + full_file_name)
				imp.load_source('DOCC', full_file_name)
		else:
			process_dir_recurse(full_file_name)

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
			process_dir_recurse(sys.argv[i])
		if not sys.modules.has_key('DOCC'):
			sys.stderr.write("No documentation found.\n")
			sys.exit(1)
		docs = sys.modules['DOCC'].DOC
		check(docs)
		report(cmd, docs)
	else:
		usage()

GLOBAL_CLASSES = ['global', 'ArrayBuffer', 'Object', 'Number', 'Uint8Array', 'Array', 'Strings', 'Math']
for k in GLOBAL_CLASSES:
	NamespaceDoc(k, 'Javascript ' + k + ' namespace.', NO_Sees, NO_Examples)

if __name__ == '__main__':
	main()

