#include <Core/Utils.h>
#include <Binding/JSUtils.h>
<%!
from idl2cpp_transformer import ctype, jsvaltype, convert, capitalize, idl_type
from pywidl.model import SimpleType
%>
<%namespace name="defs" file="defs.tpl" import="*"/>

/*
   Copyright 2016 Nidium Inc. All rights reserved.
   Use of this source code is governed by a MIT license
   that can be found in the LICENSE file.
*/

#ifndef binding_${ classname }_h__
#define binding_${ classname }_h__

#include "${foo}.h"

#include "Binding/ClassMapper.h"

namespace Nidium {
namespace Binding {

// {{{ fake ${ foo }
/*
//This is a model of our imaginary base class '${ foo }'

class ${ foo }
{
public:
    % if ctor:
        % for constructor in constructors['lst']:
          ${ foo } (${ defs.arglst(constructor.arguments) });
        % endfor
    % endif
    ~${ foo } ();
protected:
    // Methods
    % for attrName, attrData in operations.items():
         % for op in attrData['lst']:
             ${ idl_type(op.return_type)|ctype } ${ op.name }(${ defs.arglst(op.arguments) });
         % endfor
    % endfor
    // Properties
    //todo SETTER ONLY
    % for attrName, attrData in members.items():
        % if not attrData.readonly:
            bool set_${attrData.name}(${ idl_type(attrData.type)|ctype } );
        % endif
        ${ idl_type(attrData.type)|ctype } get_${attrData.name}();
    % endfor
private:
    // Properties
    % for attrName, attrData in members.items():
        ${ idl_type(attrData.type)|ctype } ${ attrData.name };
    % endfor
};
// }}}
*/

class ${ classname } : public ClassMapper<${ classname }>, public ${ foo }
{
public:
% if ctor:
    % for constructor in constructors['lst']:
         ${ classname}( ${ defs.arglst(constructor.arguments) }) 
    : ${ foo }( ${ defs.argcall(constructor.arguments) } )
{

}
   % endfor
% endif

    ~${ classname }();
    % if ctor:
    static ${ classname } * Constructor(JSContext *cx, JS::CallArgs &args,
        JS::HandleObject obj);
    static void RegisterObject(JSContext *cx);
    %endif
    % if (operations.items) > 0:
    static JSFunctionSpec * ListMethods();
    % endif
    % if (members.items) > 0:
    static JSPropertySpec *ListProperties();
    % endif
protected:
    % for attrName, attrData in operations.items():
    NIDIUM_DECL_JSCALL(${attrName});
    % endfor
    //todo ONLY-SETTER
    % for attrName, attrData in members.items():
        % if not attrData.readonly:
            NIDIUM_DECL_JSGETTERSETTER(${ attrData.name });
        % else:
            NIDIUM_DECL_JSGETTER(${ attrData.name });
        % endif
    % endfor
private:
};
} // namespace Binding
} // namespace Nidium

#endif
