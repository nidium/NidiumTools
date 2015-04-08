#!/usr/bin/python
"""
Tool to generate documentation in a different way then JSDoc does

It is good practice to document API's near their implementation.
This is difficult if it concerns a scripting language that is embedded in an other program.
Such as embedding javascript (spidermonkey engine), where functionality of the hostprogram is exposed to javascript scripts.

This tool tries to make it easier
"""
import sys, os
import codeop, traceback

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
	"""
	if text[-1] != '.':
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
	elif isinstance( typed, str ):
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
		if base_type == ParamDoc:
			if isinstance( var, CallbackDoc ):
				rok = True
	if not rok:
		raise TypeError( var_name + ": " + base_type.__name__ + " expected, got: " + type( var ).__name__ )

def check_list_type( list_name, var_name, base_class_type ):
	"""
	Forces the variable into a (empty) list. If it was a list, all items must be of the correct type.

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
		self.file_name = FILE_NAME
		self.line_nr = LINE_NR
		class_name = self.name
		if '.' in self.name:
			class_name = self.name[:self.name.index( '.' )]
		#print( class_name )
		if not class_name in DOC['classes']:
			DOC['classes'][class_name] = { 'events': {}, 'fields': {}, 'functions': {}, 'constructors': {}, 'base': {} }
		if isinstance( self, EventDoc ):
			DOC['classes'][class_name]['events'][self.name] = self
		elif isinstance( self, FieldDoc ):
			DOC['classes'][class_name]['fields'][self.name] = self
		elif isinstance( self, FunctionDoc ):
			DOC['classes'][class_name]['functions'][self.name] = self
		elif isinstance( self, ConstructorDoc ):
			DOC['classes'][class_name]['constructors'][self.name] = self
		else:
			DOC['classes'][class_name]['base'][self.name] = self

class DetailDoc( TechnicalDoc ):
	"""
	An abstract class, that is just a convinient constructor and formatter
	"""
	#TODO Since, deprecated
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
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		print( "__" + self.name + "__\n\n" + dotstr( self.description ) + "\n" )
		print( "__Public__: " + boolstr( self.is_public ) + "\n" )
		print( "__Static__: " + boolstr( self.is_static ) + "\n")
		if len( self.sees ) > 0:
			print( "__Sees__:" + "\n" )
			for se in self.sees:
				if (self.name is not se.data ):
					se.to_nidium()
		if len( self.examples ) > 0:
			print( "\n__Examples__:" + "\n" )
			for ex in self.examples:
				ex.to_nidium()
		if hasattr( self, 'params' ) and len( self.params ) > 0:
			print( "\n__Parameters__:" + "\n"  )
			for pa in self.params:
				pa.to_nidium()
		if hasattr( self, 'returns' ) and len( self.returns ) > 0:
			print( "\n__Returns__:" + "\n" )
			for re in self.returns:
				re.to_nidium()
		print( "\n" )

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
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		super( NamespaceDoc, self ).to_nidium( );

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
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		super( self.__class__, self ).to_nidium( );
		if len( self.inherrits ) > 0 :
			print( "\n__Inherrits__:" + "\n" )
			for ih in self.inherrits:
				print( ih )
		if len( self.extends ) > 0 :
			print( "\n__Extends__:" + "\n" )
			for ex in self.extends:
				print( ex )

class FunctionDoc( DetailDoc ):
	"""
	This handles functions and methods
	"""
	def __init__( self, name, description, sees = None, examples = NO_Examples, is_static = IS_Dynamic, is_public = IS_Public, is_slow = IS_Fast, params = NO_Params, returns = NO_Returns ):
		"""
		>>> a = FunctionDoc( 'console.log', 'Log shit', NO_Sees, NO_Examples, IS_Dynamic, IS_Public, IS_Slow, ParamDoc( 'text', 'The Text', 'string', "") )
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
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		super( FunctionDoc, self ).to_nidium( );
		print( "__Constructor__:" + boolstr( self.is_constructor ) + "\n" )
		if self.is_slow:
			print( ">**Warning:**\n>as `" + self.name + "` is a synchronous method, it will block nidium and the UI until the reading process is complete" )

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
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		super( self.__class__, self ).to_nidium( );


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
			if isinstance(  default, int ) or isinstance(  default, str ):
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
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		print( self.name + "\t'" + "', '".join( self.typed ) + "'\t" + boolstr( self.is_readonly  ) + "\t" + dotstr( self.description ) ) 

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
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		print( "'" +  "', '".join( self.typed ) + "'\t" + dotstr( self.description ) ) 

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
		super( self.__class__, self ).__init__( name, description )
		typed = splittype( typed )
		self.typed = check_list_type( typed, "typed", str ) #TODO: check for JStypes or types that were defined ....
		self.default = default
		self.is_optional = is_optional
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		print( self.name + "\t'" + "', '".join( self.typed ) + "'\t" + boolstr( self.is_optional ) + "\t" + dotstr( self.description ) ) 

class EventDoc( DetailDoc ):
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
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		super( self.__class__, self ).to_nidium( )


class CallbackDoc( TechnicalDoc ):
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
		super( self.__class__, self ).__init__( name, description )
		self.params = check_list_type( params, "params", ParamDoc )
		self.is_optional = IS_Obligated
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		extra = ""
		for pa in self.params:
			extra += pa.name + "\t'" + "', '".join( pa.typed ) + "'\t" + boolstr( pa.is_optional ) + "\t" + dotstr( pa.description ) + "\n"
		print( self.name + "\t" + "'callback'" + "\t" + boolstr( self.is_optional ) + "\t" + dotstr( self.description ) + extra )

class ExampleDoc( BasicDoc ):
	"""
	This handles examples
	"""
	def __init__( self, example ):
		"""
		>>> a = ExampleDoc( 'print( "hello" )' )
		>>> a.data
		'print( "hello" )'
		"""
		super( self.__class__, self ).__init__( )
		check_list_type( example, "example", str ) 
		self.data = example
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		print( "```javascript\n" + self.data + "\n```" )

def SeesDocs( list_of_sees ):
	"""
	Builds a list of Seedoc's based on a string with '|'
	>>> a = SeesDocs( "dummy1" );
	>>> a[0].data
	'dummy1'
	
	>>> a = SeesDocs( "dummy1|dummy2" );
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
		check_list_type( see, "see", str ) #TODO: check is if see' is defined
		self.data = see
	def to_nidium( self ):
		"""output prepared for copy and pasting to nidiums backoffice website"""
		print( "__" + self.data + "__" )

def run_it( code, file_name, line_nr, dry ):
	"Try to lint/parse the code"
	rok = False
	FILE_NAME = file_name
	LINE_NR = line_nr
	try:
		if dry:
			codeop.compile_command( code, file_name, 'exec' )
		else:
			exec( code )
		rok = True
	except ( SyntaxError ) as error:
		print( "An " + type( error ).__name__ + " occurred in file: " + file_name + ":" + str( error.lineno) + "-" + str( error.offset ) + "\n" + error.text + "-" * error.offset + "^" )
	except ( TypeError, OverflowError, ValueError, NameError ) as error:
		print( "An " + type( error ).__name__ + " occurred in file: " + file_name + ":" + str( line_nr ) + "\n" + error.message )
	except Exception as error:
		print( "An " + type( error ).__name__ + " occurred in file: " + file_name + ":" + str( line_nr ) + "\n" + error.message )
	if not rok:
	#	print( error.args )
		print( code )
		print traceback.format_exc( )
		sys.exit( 1 )

def process_raw_content( content, file_name ):
	"""
	Go through the characters and look for /*$	$*/ blocks
	each block is python code that should be run in the current scope
	
	>>> process_raw_content( "/*$$*/", "dummy" )
	''
	
	>>> process_raw_content( "/*$print( 43 - 1 )$*/", "dummy" )
	42
	'print( 43 - 1 )'
	"""
	all_code = ""
	i = 0
	line_nr = 0;
	state = '0'
	start = 0
	end = 0 
	for token in content:
		if token == '\n':
			line_nr += 1
		if state == '0':
			if token == '/':
				state = 's1'
		elif state == 's1':
			if token == '*':
				state = 's2'
			else:
				state = '0'
		elif state == 's2':
			if token == '$':
				state = 'i'
				start = i
			else:
				state = '0'
		elif state == 'i':
			if token == '$':
				end = i
				state = 'e1'
		elif state == 'e1':
			if token == '*':
				state = 'e2'
			else:
				state = 'i'
		elif state == 'e2':
			if token == '/':
				state = '0'
				code = content[ start + 1 : end ]
				run_it( code, file_name, line_nr, False )
				all_code += code
			else:
				state = 'i'
		i += 1
	return all_code

def process_dir( dir_name ):
	"""
	Go through all the files in the dirName process the raw sourcecode
	"""
	all_code = ''
	for file_name in os.listdir( dir_name ):
		full_file_name = os.path.join( dir_name, file_name )
		if not os.path.isdir( full_file_name ):
			#print( "Parsing " + file_name )
			file_h = open( full_file_name, 'r' )
			content = file_h.read( )
			file_h.close( )
			all_code += process_raw_content( content, full_file_name )
	#print( "Running.." )
	run_it( all_code, os.path.join( dir_name, '*' ), 0,  True )

LINE_NR = 0
FILE_NAME = 'unknown'
DOC = { 'classes': { } }

def check( ):
	"do some checks"
	types_list = ['integer', 'boolean', 'float', 'string', 'mixed', 'null', 'Date', 'Object' ]
	for typed in list( types_list ):
		types_list.append( "[" + typed + "]" )
	items_list = [];
	for class_name, class_details in DOC['classes'].items( ):
		#print( class_name )
		types_list.append( class_name )
		types_list.append( "[" + class_name + "]" )
		items_list.append( class_name )
		for type_doc, type_details in class_details.items( ):
			for item, item_details in type_details.items( ):
				items_list.append( item )
	for class_name, class_details in DOC['classes'].items( ):
		for type_doc, type_details in class_details.items( ):
			for item, item_details in type_details.items( ):
				#TODO: Refractor
				if hasattr( item, "sees" ) :
					for sees in item_details.sees:
						if sees.data not in items_list:
							print( "See '" + sees.data + "' in " +  item + "'s SeeDoc is not defined" )
							#print( item_details.file_name + ":" + str( item_details.line_nr ) )
							sys.exit( 1 )
				if hasattr( item_details, "inherrits" ):
					for typed in item_details.inherrits:
						if typed not in types_list:
							print( "The type '" + typed + "' in " + item + "'s Extends is not defined" )
							sys.exit( 1 )
				if hasattr( item_details, "extends" ):
					for typed in item_details.extends:
						if typed not in types_list:
							print( "The type '" + typed + "' in " + item + "'s Extends is not defined" )
							sys.exit( 1 )
				if hasattr( item_details, "constructors" ):
					for constructor in item_details.constructors:
						for typed in constructor.typed:
							if typed not in types_list:
								print( "The type '" + typed + "' in " + item + "'s ReturnDoc is not defined" )
								sys.exit( 1 )
				if hasattr( item_details, "returns" ):
					for returns in item_details.returns:
						for typed in returns.typed:
							if typed not in types_list:
								print( "The type '" + typed + "' in " + item + "'s ReturnDoc is not defined" )
								sys.exit( 1 )
				if hasattr( item_details, "events" ):
					for params in item_details.events:
							for typed in params.typed:
								if typed not in types_list:
									print( "The type '" + typed + "' in " + item + " 's EventDoc is not defined" )
									sys.exit( 1 )
				if hasattr( item_details, "params" ):
					for params in item_details.params:
						if isinstance( params, CallbackDoc ):
							for p in params.params:
								for typed in p.typed:
									if typed not in types_list:
										print( "The type '" + typed + "' in " + item + "'s CallbackDoc is not defined" )
										sys.exit( 1 )
						else:
							for typed in params.typed:
								if typed not in types_list:
									print( "The type '" + typed + "' in " + item + " 's ParamDoc is not defined" )
									sys.exit( 1 )
				if hasattr( item_details, "fields" ):
					for fields in item_details.fields:
						if fields.typed not in types_list:
							print( "The type '" + fields.typed + "' in " + item + "'s FieldDoc is not defined" )
							sys.exit( 1 )

def report( variant ):
	"dump it in a layout"
	if variant == 'nidium_bo':
		for class_name, class_details in DOC['classes'].items( ):
			print( "\n\n\n\n#" + class_name + "\n" )
			for type_doc, type_details in class_details.items( ):
				print( "\n\n\n## " + type_doc + "\n" )
				for item, item_details in type_details.items( ):
					print( "\n\n### " + item + "\n" )
					item_details.to_nidium()

def main( ):
	"""The main routine"""
	if len( sys.argv ) == 1:
		print( "Usage: "+ sys.argv[0] + " DIR [DIR2, ]\n\tPlease note: if DIR = 'doctest' then this module will run the doctests." )
		sys.exit( )
	elif sys.argv[1] == 'doctest':
		import doctest
		doctest.testmod( )
	else:
		for i in range( 1, len( sys.argv ) ):
			process_dir( sys.argv[i] )
		check( )
		report( 'nidium_bo' )


if __name__ == '__main__':
	main( )

