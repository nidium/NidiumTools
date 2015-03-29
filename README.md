# Nidum Tools

Several tools that were specially crafted for the nidium project

# Contents

## dokumentor

Simple, but effective way to for the developer to keep the documentation and 
the code in sync without to much hassle.

### Confusing...

While programming C/C++ to expose Javascript, you write python code in comments.
While running another python script, markdown is generated

### Show me the code

In the c/c++ you can write comments like:

```
/*$
FunctionDoc( "HTTPRequest.write", "Respond to a client that made a request to the webserver",
	[ SeeDoc( "HTTPListener" ), SeeDoc( "HTTPRequest.write"), SeeDoc( "HTTPRequest.end" ), SeeDoc( "HTTPRequest.writeHead" ) ],
	NO_Examples,
	IS_Dynamic, IS_Public, IS_Fast,
	[ ParamDoc( "data", "The data to send out", "string|ArrayBuffer", IS_Obligated ) ],
	NO_Returns
);
$*/
```

And by pointing `src/dokumentor.py` to the file's direcory it could create:

```
_HTTPRequest.write__

Respond to a client that made a request to the webserver.

__Public__: true

__Static__: false

__Sees__:

__HTTPListener__
__HTTPRequest.end__
__HTTPRequest.writeHead__

__Parameters__:

data	'string', 'ArrayBuffer'	false	The data to send out.

```
