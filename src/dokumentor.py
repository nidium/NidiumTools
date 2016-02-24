#!/usr/bin/env python2.7
"""
Tool to generate documentation in a different way then JSDoc does

It is good practice to document API's near their implementation.
This is difficult if it concerns a scripting language that is embedded in an other program.
Such as embedding javascript (spidermonkey engine), where functionality of the hostprogram is exposed to javascript scripts.

This tool tries to make it easier
"""
import sys, os, imp, json

DOC = { 'classes': { } }

#some Global variables to enhance readability
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

def boolstr( val ):
	"""true if so, etc.
	>>> boolstr( True)
	'true'

	>>> boolstr( False )
	'false'
	"""
	if val:
		return 'true'
	return 'false'

def dotstr( text ):
	"""
	Asure that the text is ending with a '.'
	>>> dotstr( "a" )
	'a.'

	>>> dotstr( "a." )
	'a.'

	>>> dotstr( "" )
	''
	
	"""
	if len( text ) > 0 and text[-1] != '.':
		text += '.'
	return text

def splittype( typed ):
	"""splits a string nto a list, eventually by using a '|'
	>>> splittype( 'he' )
	['he']

	>>> splittype( None )

	>>> splittype( "h|e" )
	['h', 'e']
	"""
	if typed is None:
		return typed
	elif type( typed ).__name__ == 'str':
		if '|' in typed:
			typed = typed.split( '|' )
		else:
			typed = [ typed ]
	return typed

def check_type( var, var_name, base_type ):
	"""
	Wrapper for isinstance that throws an error message
	>>> check_type( 1, "h", int )
	>>> check_type( 1, "h", str )
	Traceback (most recent call last):
	 ...
	TypeError: h: str expected, got: int
	"""
	rok = True
	if not isinstance( var, base_type ):
		rok = False
		if base_type.__name__ == 'ParamDoc':
			if type( var ).__name__ == 'CallbackDoc':
				rok = True
	if not rok:
		raise TypeError( var_name + ": " + base_type.__name__ + " expected, got: " + type( var ).__name__ )

def check_list_type( list_name, var_name, base_class_type ):
	"""
	Forces the variable into a ( empty ) list. If it was a list, all items must be of the correct type.

	>>> a = [1, 2 ]
	>>> b = check_list_type( a, "i", int )
	>>> a == b
	True
	
	>>> b = check_list_type( None, "i", int )
	>>> b == []
	True
	
	>>> c = check_list_type( [], "i", int )
	>>> c == []
	True
	
	>>> d = check_list_type( 1, "i", int )
	>>> d[0] == 1
	True
	
	>>> e = check_list_type( ['', 1] , "i", int )
	Traceback (most recent call last):
	 ...
	TypeError: i: int expected, got: str
	"""
	if list_name is None:
		list_name = []
	elif isinstance( list_name, base_class_type ):
		list_name = [ list_name ]
	else:
		check_type( list_name, var_name, list )
		for item in list_name:
			check_type( item, var_name, base_class_type )
	return list_name

class BasicDoc( object ):
	"""
	An abstract class, that can spit out the formatted documentation
	"""
	def __init__( self ):
		"""
		>>> a = BasicDoc( )
		>>> type( a )
		<class '__main__.BasicDoc'>

		"""
		pass
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		return {}

class TechnicalDoc( BasicDoc ):
	"""
	An abstract class, that is just a convinient constructor and formatter
	"""
	def __init__( self, name, description ):
		"""
		>>> a = TechnicalDoc( "tech", "Tech" )
		>>> a.name
		'tech'

		>>> a.description
		'Tech'
		"""
		super( TechnicalDoc, self ).__init__( )
		check_type( name, "name", str )
		check_type( description, "description", str )
		self.name = name
		self.description = description
		class_name = self.name
		if '.' in self.name:
			class_name = self.name[:self.name.index( '.' )]
		key = ''
		typed = type( self ).__name__
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
			raise ValueError( 'A very specific bad thing happened' )	
		if add:
			DOC['classes'][class_name] = { 'events': {}, 'properties': {}, 'methods': {}, 'constructors': {}, 'base': {class_name: {} } }
		if key != '':
			DOC['classes'][class_name][key][self.name] = self
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( TechnicalDoc, self ).to_dict( )
		data['name'] = self.name
		data['description'] = self.description
		return data

class DetailDoc( TechnicalDoc ):
	"""
	An abstract class, that is just a convinient constructor and formatter
	"""
	#@TODO: Since, deprecated
	def __init__( self, name, description, sees = NO_Sees, examples = NO_Examples, is_static = IS_Dynamic, is_public = IS_Public ):
		"""
		>>> a = DetailDoc( "Detail", "Devil is in the detail", None, None, True, False )
		>>> a.is_public
		False

		>>> a.is_static
		True
		"""
		super( DetailDoc, self ).__init__( name, description )
		self.sees = check_list_type( sees, "sees", SeeDoc )
		self.examples = check_list_type( examples, "examples", ExampleDoc )
		check_type( is_public, "is_public", bool )
		check_type( is_static, "is_static", bool )
		self.is_public = is_public
		self.is_static = is_static
	def to_markdown( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		print( "__" + self.name + "__\n\n" + dotstr( self.description ) + "\n" )
		print( "__Public__: " + boolstr( self.is_public ) + "\n" )
		print( "__Static__: " + boolstr( self.is_static ) + "\n" )
		if len( self.sees ) > 0:
			print( "__Sees__:" + "\n" )
			for see in self.sees:
				if (self.name is not see.data ):
					see.to_markdown( )
		if len( self.examples ) > 0:
			print( "\n__Examples__:" + "\n" )
			for example in self.examples:
				example.to_markdown( )
		print( "\n" )
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data =  super( DetailDoc, self ).to_dict( )
		data['is_public'] = self.is_public
		data['is_static'] = self.is_static
		data['sees'] = []
		data['examples'] = []
		if len( self.sees ) > 0:
			for see in self.sees:
				if ( self.name is not see.data ):
					data['sees'].append( see.to_dict( ) )
		if len( self.examples ) > 0:
			for example in self.examples:
				data['examples'].append( example.to_dict( ) )
		return data

class NamespaceDoc( DetailDoc ):
	"""
	This handles 'namespaces, witch are placeholders/castrated classes
	"""
	def __init__( self, name, description, sees = None, examples = NO_Examples ):
		"""
		>>> a = NamespaceDoc( 'Math', 'Math namespace', NO_Sees, NO_Examples )
		>>> type( a.examples )
		<type 'list'>
		
		>>> len( a.sees )
		0

		>>> a.is_static
		True

		>>> a.is_public
		True
		"""
		super( self.__class__, self ).__init__( name, description, sees, examples, True, True )
	def to_markdown( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		super( NamespaceDoc, self ).to_markdown( )
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( self.__class__, self ).to_dict( )
		return data

class ClassDoc( DetailDoc ):
	"This handles classes"
	def __init__( self, name, description, sees = None, examples = NO_Examples, inherrits = None, extends = None ):
		"""
		>>> a = ClassDoc( 'Console', 'Log interface', NO_Sees, NO_Examples, NO_Inherrits, NO_Extends )
		>>> type( a.inherrits )
		<type 'list'>

		>>> len( a.extends )
		0
		"""
		super( self.__class__, self ).__init__( name, description, sees, examples, IS_Static, IS_Public )
		self.inherrits = check_list_type( inherrits, "inherrits", str )
		self.extends = check_list_type( extends, "extends", str )
	def to_markdown( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		super( self.__class__, self ).to_markdown( )
		if len( self.inherrits ) > 0 :
			print( "\n__Inherrits__:" + "\n" )
			for inherrit in self.inherrits:
				print( inherrit )
		if len( self.extends ) > 0 :
			print( "\n__Extends__:" + "\n" )
			for examp in self.extends:
				print( examp )
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( self.__class__, self ).to_dict( )
		data['inherrits'] = []
		for inh in self.inherrits:
			data['inherrits'].append( inh )
		data['extends'] = []
		for ext in self.extends:
			data['extends'].append( ext )
		return data

class FunctionDoc( DetailDoc ):
	"""
	This handles functions and methods
	"""
	def __init__( self, name, description, sees = None, examples = NO_Examples, is_static = IS_Dynamic, is_public = IS_Public, is_slow = IS_Fast, params = NO_Params, returns = NO_Returns ):
		"""
		>>> a = FunctionDoc( 'console.log', 'Log shit', NO_Sees, NO_Examples, IS_Dynamic, IS_Public, IS_Slow, ParamDoc( 'text', 'The Text', 'string', "" ) )
		>>> a.params[0].default
		''

		>>> type( a.returns )
		<type 'list'>

		>>> len( a.returns )
		0

		>>> a.params[0].typed
		['string']

		>>> a.is_constructor
		False
		
		>>> a.is_slow
		True
		"""
		super( FunctionDoc, self ).__init__( name, description, sees, examples, is_static, is_public )
		self.is_constructor = False
		self.is_slow = is_slow
		self.params = check_list_type( params, "params", ParamDoc )
		self.returns = check_list_type( returns, "returns", ReturnDoc )
	def to_markdown( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		super( FunctionDoc, self ).to_markdown( )
		if ( self.params ) > 0:
			print( "\n__Parameters__:" + "\n"  )
			for param in self.params:
				param.to_markdown( )
		print( "__Constructor__:" + boolstr( self.is_constructor ) + "\n" )
		if self.is_slow:
			print( ">**Warning:**\n>as `" + self.name + "` is a synchronous method, it will block nidium and the UI until the reading process is complete" )
		if len( self.returns ) > 0:
			print( "\n__Returns__:" + "\n" )
			for ret in self.returns:
				ret.to_markdown( )
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( FunctionDoc, self ).to_dict( )
		data['is_constructor'] = self.is_constructor
		data['is_slow'] = self.is_slow
		data['params'] = []
		for param in self.params:
			data['params'].append( param.to_dict( ) )
		data['returns'] = []
		for ret in self.returns:
			data['returns'].append( ret.to_dict( ) )
		return( data )

class ConstructorDoc( FunctionDoc ):
	"""
	This handles constructors for classes. A constructor is just a function
	"""
	def __init__( self, name, description, sees = None, examples = NO_Examples, params = NO_Params, returns = NO_Returns ):
		"""
		>>> a = ConstructorDoc( 'Webserver', 'Webserver constructor', NO_Sees, NO_Examples, NO_Params, ReturnDoc( 'Webserver', 'object' ) )
		>>> a.is_constructor
		True

		>>> type( a.returns )
		<type 'list'>
			
		"""
		super( self.__class__, self ).__init__( name, description, sees, examples, True, True, False, params, returns )
		self.is_constructor = True
	def to_markdown( self ):
		"""output prepared for in markdown format."""
		super( self.__class__, self ).to_markdown( )
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		return super( self.__class__, self ).to_dict( )

class FieldDoc( DetailDoc ):
	"""
	This handles fields, also known as properties
	"""
	def __init__( self, name, description, sees = None, examples = NO_Examples, is_static = IS_Dynamic, is_public = IS_Public, is_readonly = IS_Readonly, typed = NO_Typed, default = NO_Default ):
		"""
		>>> a = FieldDoc( 'age', "The persons age", NO_Sees, NO_Examples, IS_Dynamic, IS_Static, IS_Readonly, 'int', NO_Default )
		>>> type( a )
		<class '__main__.FieldDoc'>
		
		>>> a.typed
		['int']
		
		>>> a.default
		
		>>> a.is_readonly
		True
		
		>>> a = FieldDoc( 'age', "The persons age", NO_Sees, NO_Examples, IS_Dynamic, IS_Static, IS_ReadWrite, 'int', 30 )
		>>> a.default
		30
		
		>>> a.is_readonly
		False
		"""
		super( self.__class__, self ).__init__( name, description, sees, examples, is_static, is_public )
		check_type( is_readonly, "is_readonly", bool )
		self.is_readonly = is_readonly
		if default is not None:
			if type( default ).__name__ == 'int' or type( default ).__name__ == 'str':
				self.default = default
			else:
				check_type( default, "default", str ) #or int
				self.default = default
		else:
			self.default = NO_Default
		if typed is None:
			raise ValueError( "Type is not defined" )
		typed = splittype( typed )
		check_list_type( typed, "typed", str ) #TODO: check for JStypes or types that were defined....
		self.typed = typed
	def to_markdown( self ):
		"""output prepared in markdown format."""
		print( self.name + "\t'" + "', '".join( self.typed ) + "'\t" + boolstr( self.is_readonly  ) + "\t" + dotstr( self.description ) ) 
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( self.__class__, self ).to_dict( )
		data['typed'] = self.typed
		data['is_readonly'] = self.is_readonly
		return( data )

class ReturnDoc( TechnicalDoc ):
	"""
	This handles returns of functions/methods/constructors
	"""
	def __init__( self, description, typed ):
		"""
		>>> a = ReturnDoc( 'The new Person', 'Person' )
		>>> a.typed
		['Person']
		"""
		super( self.__class__, self ).__init__( "", description )
		typed = splittype( typed )
		self.typed = check_list_type( typed, "typed", str ) #TODO: check for JStypes or types that were defined ....
	def to_markdown( self ):
		"""output prepared in markdown format."""
		print( "'" +  "', '".join( self.typed ) + "'\t" + dotstr( self.description ) ) 
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( self.__class__, self ).to_dict( )
		data['typed'] = self.typed
		return( data )

class ParamDoc( TechnicalDoc ):
	"""
	This handles Parameters to functions/methods/constructors
	"""
	def __init__( self, name, description, typed = NO_Typed, default = NO_Default, is_optional = IS_Obligated ):
		"""
		>>> a = ParamDoc( 'sql', 'Sql statement to run', 'string', NO_Default, IS_Obligated )
		>>> a.typed
		['string']
		
		>>> a.default
		
		>>> a.is_optional
		False
		
		>>> a = ParamDoc( 'port', 'Port to listen to', 'string|int', 8080 )
		>>> a.typed
		['string', 'int']
		
		>>> a.is_optional
		False
		
		>>> a.default
		8080
		
		>>> a = ParamDoc( 'port', 'Port to listen to', ['string', 'int'], 8080, IS_Optional )
		>>> a.typed
		['string', 'int']
		
		>>> a.is_optional
		True
		"""
		super( ParamDoc, self ).__init__( name, description )
		typed = splittype( typed )
		self.typed = check_list_type( typed, "typed", str ) #TODO: check for JStypes or types that were defined ....
		self.default = default
		self.is_optional = is_optional
	def to_markdown( self ):
		"""output prepared in markdown format."""
		print( self.name + "\t'" + "', '".join( self.typed ) + "'\t" + boolstr( self.is_optional ) + "\t" + dotstr( self.description ) ) 
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( ParamDoc, self ).to_dict( )
		data['typed'] = self.typed
		data['default'] = self.default
		data['is_optional'] = self.is_optional
		return( data )

class EventDoc( FunctionDoc ):
	"""
	This handles events.
	Events are basically callbacks/functions that can be triggered everywhere in the class code
	"""
	def __init__( self, name, description, sees = NO_Sees, examples = NO_Examples, params = NO_Params ):
		"""
		>>> a = EventDoc( 'onError', 'This will be called if an error occurs', NO_Sees, NO_Examples, [ ParamDoc( 'err', 'errorcode', 'integer', 111 ) ] )
		>>> type( a.params )
		<type 'list'>
		
		>>> a.params[ 0 ].default
		111
			
		"""
		super( self.__class__, self ).__init__( name, description, sees, examples )
		self.params = check_list_type( params, "params", ParamDoc )
	def to_markdown( self ):
		"""output prepared in markdown format."""
		super( self.__class__, self ).to_markdown( )
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( self.__class__, self ).to_dict( )
		return( data )


class CallbackDoc( ParamDoc ):
	"""
	This handles parameters that are callback-functions/methods. 
	These differ because a callback function has parameters that need to be documented as well
	"""
	def __init__( self, name, description, params = NO_Params ):
		"""
		>>> a = CallbackDoc( 'callback', 'The function that will be called', [ ParamDoc( 'res', 'result', 'string', NO_Default ) ] )
		>>> type( a.params )
		<type 'list'>
		
		>>> type( a.params[ 0 ] )
		<class '__main__.ParamDoc'>
			
		>>> a.is_optional
		False
		
		>>> a = CallbackDoc( 'callback', 'The function that will be called', NO_Params )
		>>> type( a.params )
		<type 'list'>
		
		>>> a = CallbackDoc( 'callback', 'The function that will be called', ParamDoc( 'res', 'result', 'string', NO_Default, IS_Obligated ) )
		>>> type( a.params )
		<type 'list'>
		"""
		super( CallbackDoc, self ).__init__( name, description, 'function', NO_Default, IS_Obligated )
		self.params = check_list_type( params, "params", ParamDoc )
	def to_markdown( self ):
		"""output prepared in markdown format."""
		extra = ""
		for param in self.params:
			extra += param.name + "\t'" + "', '".join( param.typed ) + "'\t" + boolstr( param.is_optional ) + "\t" + dotstr( param.description ) + "\n"
		print( self.name + "\t" + "'callback'" + "\t" + boolstr( self.is_optional ) + "\t" + dotstr( self.description ) + extra )
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( self.__class__, self ).to_dict( )
		data['is_optional'] = self.is_optional
		data['params'] = []
		for i in self.params:
			data['params'].append( i.to_dict( ) )
		return( data )

class ExampleDoc( BasicDoc ):
	"""
	This handles examples
	"""
	def __init__( self, example, lang='javascript' ):
		"""
		>>> a = ExampleDoc( 'print( "hello" )' )
		>>> a.data
		'print( "hello" )'
		"""
		super( self.__class__, self ).__init__( )
		check_list_type( example, "example", str ) 
		self.data = example.strip()
		self.language = lang
	def to_markdown( self ):
		"""output prepared for in markdown format."""
		print( "```" + self.language + "\n" + self.data + "\n```" )
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( self.__class__, self ).to_dict( )
		data['data'] = self.data
		data['language'] = self.language
		return( data )

def SeesDocs( list_of_sees ):
	"""
	Builds a list of Seedoc's based on a string with '|'
	>>> a = SeesDocs( "dummy1" )
	>>> a[0].data
	'dummy1'
	
	>>> a = SeesDocs( "dummy1|dummy2" )
	>>> a[1].data
	'dummy2'
	""" 
	if list_of_sees:
		list_of_sees = splittype( list_of_sees )
		for i, see in enumerate( list_of_sees ):
			list_of_sees[i] = SeeDoc( see )
	return list_of_sees

class SeeDoc( BasicDoc ):
	"""
	This handles see's
	"""
	def __init__( self, see ):
		"""
		>>> a = SeeDoc( 'dummy' )
		>>> a.data 
		'dummy'
		"""
		super( self.__class__, self ).__init__( )
		check_list_type( see, "see", str )
		self.data = see
	def to_markdown( self ):
		"""output prepared for in markdown format."""
		print( "__" + self.data + "__" )
	def to_dict( self ):
		"""Prepare a normal interface to export data."""
		data = super( self.__class__, self ).to_dict( )
		data['data'] = self.data
		return( data )

def check( docs ):
	"do some checks"
	types_list = ['integer', 'boolean', 'float', 'string', 'mixed', 'null', 'Date', 'Object', 'ArrayBuffer', 'Uint16Array', 'Array', 
		'object', '?',
		'SocketClient', 'Canvas', 'NDMElement.color', 'Canvas2DContext', 'AudioBuffer'
				]
	for typed in list( types_list ):
		types_list.append( "[" + typed + "]" )
	items_list = []
	for class_name, class_details in docs['classes'].items( ):
		types_list.append( class_name )
		types_list.append( "[" + class_name + "]" )
		items_list.append( class_name )
		for type_details in class_details.values( ):
			for item, item_details in type_details.items( ):
				items_list.append( item )
	for class_name, class_details in docs['classes'].items( ):
		for chapter, type_details in class_details.items( ):
			if chapter == 'base':
				if type(type_details[class_name]) == type( dict() ):
					sys.stderr.write( "Class/Namespace '" + class_name + "' is not defined.\n" )
					sys.exit( 1 )
			for item, item_details in type_details.items( ):
				#TODO: Refractor
				if hasattr( item, "sees" ) :
					for sees in item_details.sees:
						if sees.data not in items_list:
							sys.stderr.write( "See '" + sees.data + "' in " +  item + "'s SeeDoc is not defined.\n" )
							sys.exit( 1 )
				if hasattr( item_details, "inherrits" ):
					for typed in item_details.inherrits:
						if typed not in types_list:
							sys.stderr.write( "The type '" + typed + "' in " + item + "'s Extends is not defined.\n" )
							sys.exit( 1 )
				if hasattr( item_details, "extends" ):
					for typed in item_details.extends:
						if typed not in types_list:
							sys.stderr.write( "The type '" + typed + "' in " + item + "'s Extends is not defined.\n" )
							sys.exit( 1 )
				if hasattr( item_details, "constructors" ):
					for constructor in item_details.constructors:
						for typed in constructor.typed:
							if typed not in types_list:
								sys.stderr.write( "The type '" + typed + "' in " + item + "'s ReturnDoc is not defined.\n" )
								sys.exit( 1 )
				if hasattr( item_details, "returns" ):
					for returns in item_details.returns:
						for typed in returns.typed:
							if typed not in types_list:
								sys.stderr.write( "The type '" + typed + "' in " + item + "'s ReturnDoc is not defined.\n" )
								sys.exit( 1 )
				if hasattr( item_details, "events" ):
					for params in item_details.events:
							for typed in params.typed:
								if typed not in types_list:
									sys.stderr.write( "The type '" + typed + "' in " + item + " 's EventDoc is not defined.\n" )
									sys.exit( 1 )
				if hasattr( item_details, "params" ):
					for params in item_details.params:
						if type( params ).__name__ == 'CallbackDoc':
							for param in params.params:
								for typed in param.typed:
									if typed not in types_list:
										sys.stderr.write( "The type '" + typed + "' in " + item + "'s CallbackDoc is not defined.\n" )
										sys.exit( 1 )
						else:
							for typed in params.typed:
								if typed not in types_list:
									sys.stderr.write( "The type '" + typed + "' in " + item + " 's ParamDoc is not defined.\n" )
									sys.exit( 1 )
				if hasattr( item_details, "properties" ):
					for prop in item_details.properties:
						if prop.typed not in types_list:
							sys.stderr.write( "The type '" + prop.typed + "' in " + item + "'s FieldDoc is not defined.\n" )
							sys.exit( 1 )

def report( variant , docs ):
	"dump it in a layout"
	data = {}
	for class_name, class_details in docs['classes'].items( ):
		data[class_name] = {}
		count = 0
		for type_doc, type_details in class_details.items( ):
			data[class_name][type_doc] = {}
			for item, item_details in type_details.items( ):
				data[class_name][type_doc][item] = item_details.to_dict( )
				if type_doc != 'base':
					count += len( data[class_name][type_doc].keys( ) )
		if count == 0 and class_name != 'global':
			del data[class_name]
	if variant == 'json':
		print( json.dumps( data ) )
	elif variant == 'exampletest':
		code = ''
		counter = 0;
		for class_name, class_details in data.items( ):
			code += "Tests.register('Running tests for %s', function() {});\n" % class_name
			for type_doc, type_details in class_details.items( ):
				for item, item_details in type_details.items( ):
					for i, example in enumerate( item_details['examples'] ):
						if example['language'] == 'javascript':
							name = class_name + '.' + type_doc + "." + item + "." + str( i );
							examplecode = "\n\t\t".join( example['data'].splitlines( ) )
#							examplecode = "\n\ttry {\n\t\t" + examplecode + "\n\t} catch( err ) {\n\t\tconsole.log('Syntax error in example code; Go fix `" + name + "`!' + err.message );\n\t}"
							code += '\nTests.register("' + name + '", function( ) {'
							code += "\n\tvar dummy = " + str( counter ) + ';'
							code += "\n\t\t" + examplecode
							code += "\n\n\tAssert.equal(dummy, " +str( counter ) +');'
							code += '\n});\n'
							counter += 1;
		print( code )
	elif variant == 'markdown':
		for class_name, class_details in docs['classes'].items( ):
			if data.has_key( class_name ):
				print( "\n\n\n\n#" + class_name + "\n" )
				for type_doc, type_details in class_details.items( ):
					if type_doc != 'base' and len( type_details.keys( ) ) > 0:
						print( "\n\n\n## " + type_doc + "\n" )
						for item, item_details in type_details.items( ):
							print( "\n\n### " + item + "\n" )
							item_details.to_markdown( )

def process_dir_recurse( dir_name ):
	"""
	Go through all the files in the dirName process the raw sourcecode
	"""
	for file_name in os.listdir( dir_name ):
		full_file_name = os.path.join( dir_name, file_name )
		if not os.path.isdir( full_file_name ):
			if os.path.splitext( full_file_name )[-1] == '.py' and file_name != '.ycm_extra_conf.py':
				#print( "#Reading " + full_file_name )
				imp.load_source( 'DOCC', full_file_name )
		else:
			process_dir_recurse( full_file_name )

VARIANTS = ['doctest', 'markdown', 'json', 'exampletest']
def usage( ):
	"""Usage."""
	print( "Usage: "+ sys.argv[0] + "cmd DIR [DIR2, ]\n\tcmd:	'" + "', '".join( VARIANTS ) + "'." )
	sys.exit( 1 )
	
def main( ):
	"""The main routine"""
	if len( sys.argv ) == 1:
		usage( )
	cmd = sys.argv[1]
	if cmd == 'doctest':
		import doctest
		doctest.testmod( )
	elif len( sys.argv ) > 2 and cmd in VARIANTS:
		for i in range( 2, len( sys.argv ) ):
			process_dir_recurse( sys.argv[i] )
		if not sys.modules.has_key( 'DOCC' ):
			sys.stderr.write( "No documentation found.\n" )
			sys.exit( 1 )
		docs = sys.modules['DOCC'].DOC
		check( docs )
		report( cmd, docs )
	else:
		usage( )


NamespaceDoc( 'global', 'Javascript Global namespace.', NO_Sees, NO_Examples )
NamespaceDoc( 'Strings', 'Javascript strings type.', NO_Sees, NO_Examples )
NamespaceDoc( 'ArrayBuffer', 'Javascript ArrayBuffer type.', NO_Sees, NO_Examples )
NamespaceDoc( 'Object', 'Javascript Object type.', NO_Sees, NO_Examples )
NamespaceDoc( 'Uint8Array', 'Javascript Uint8Array type.', NO_Sees, NO_Examples )
NamespaceDoc( 'Number', 'Javascript Number type.', NO_Sees, NO_Examples )
NamespaceDoc( 'Array', 'Javascript Array type.', NO_Sees, NO_Examples )
NamespaceDoc( 'Math', 'Javascript Math namespace.', NO_Sees, NO_Examples )

if __name__ == '__main__':
	main( )

