/*
   Copyright 2016 Nidium Inc. All rights reserved.
   Use of this source code is governed by a MIT license
   that can be found in the LICENSE file.
*/
<%!
from idl2cpp_transformer import ctype, jsvaltype, convert, capitalize, idl_type
from pywidl.model import SimpleType
%>

<%namespace name="defs" file="defs.tpl" import="*"/>

#include <Binding/ClassMapper.h>
#include "${classname}.h"

namespace Nidium {
namespace Binding {

// {{{ JSBinding

% if ctor:
// {{{ Start Constructor
${classname} *${ classname }::Constructor(JSContext *cx, JS::CallArgs &args,
    JS::HandleObject obj)
{
    unsigned argc = args.length();
    unsigned argcMin = ((${ constructors['maxArgs'] } > argc) ? (argc) : (${ constructors['maxArgs'] }));

    switch (argcMin) {
        % for op in constructors['lst']:
            case ${ len(op.arguments) }:
            {
                /* Start arguments conversion */
                % for arg in op.arguments:
                    /* Handle argument #${ loop.index } of type "${ idl_type(arg.type) }" */
                    % if not arg.type.nullable:
                        if (args[${ loop.index }].isNull()) {
                            JS_ReportError(cx, "TypeError");
                            return nullptr;
                        }
                    % endif
                    ${ defs.jsval2c('args['+ str(loop.index) +']', idl_type(arg.type), 'inArg_' + str(loop.index), 'nullptr') }
                % endfor
                /* End of arguments conversion */

                ${ classname} *n_${ classname }_${ foo } = new ${ classname }(
                    % for i in range(0, len(op.arguments)):
                            inArg_${ i }${ ' ' if loop.last else ', ' }
                    % endfor
                );
                n_${ classname }_${ foo }->root();
                return n_${ classname }_${ foo };
                break;
            }
        % endfor
        default:
            JS_ReportError(cx, "TypeError: wrong number of arguments");
            return nullptr;
            break;
    }

    return nullptr;
}
// }}} End Constructor
% endif

% if (operations.items) > 0:
// # {{{ Start Operations
JSFunctionSpec * ${ classname }::ListMethods()
{
    static JSFunctionSpec funcs[] = {
    % for attrName, attrData in operations.items():
        CLASSMAPPER_FN(${ classname }, ${ attrName }, ${attrData['maxArgs']} ),
    % endfor

    JS_FS_END
    };

    return funcs;
}

% for attrName, attrData in operations.items():
bool ${ classname }::JS_${ attrName }(JSContext *cx, JS::CallArgs &args)
{
    unsigned argc = args.length();
    unsigned argcMin = ((${ attrData['maxArgs'] } > argc) ? (argc) : (${ attrData['maxArgs'] }));

    switch (argcMin) {
        % for op in attrData['lst']:
        case ${ len(op.arguments) }:
        {
            /* Start arguments conversion */
            % for arg in op.arguments:
                % if isinstance(arg.type, SimpleType):
                /* Handle argument #${ loop.index } of type "${ idl_type(arg.type) }" */
                % else:
                /* Handle argument #${ loop.index } of type "${ arg.type }" */
                % endif
                % if not arg.type.nullable:
                    if (args[${ loop.index }].isNull()) {
                        JS_ReportError(cx, "TypeError");
                        return false;
                    }
                %endif
                % if isinstance(arg.type, SimpleType):
                    ${ defs.jsval2c('args[' + str(loop.index) + ']', idl_type(arg.type), 'inArg_' + str(loop.index)) }
                % else:
                    ${ defs.jsval2c('args[' + str(loop.index) + ']', arg.type.name, 'inArg_' + str(loop.index)) }
                % endif
            % endfor

            /* End of arguments conversion */
            % if op.return_type.type != SimpleType.VOID:
                ${ idl_type(op.return_type)|ctype } _opret =
            %endif
            this->${ attrName }(
                % for i in range(0, len(op.arguments)):
                    inArg_${ i }${ ' ' if loop.last else ', ' }
                % endfor
                );
            % if op.return_type.type != SimpleType.VOID:
            args.rval().set${ jsvaltype(idl_type(op.return_type))|capitalize }(_opret);
            %endif

            break;
        }
        % endfor
        default:
            JS_ReportError(cx, "TypeError: wrong number of arguments");
            return false;
            break;
    }

    return true;
}
% endfor
// }}} End Operations
% endif

% if (members.items) > 0:
// {{{ Start Members
JSPropertySpec *${ classname }::ListProperties()
{
    static JSPropertySpec props[] = {
    //todo ONLY-SETTER
    % for attrName, attrData in members.items():
        % if not attrData.readonly:
            CLASSMAPPER_PROP_GS(${ classname }, ${ attrData.name }),
        % endif
        CLASSMAPPER_PROP_G(${ classname }, ${ attrData.name }),
    % endfor

        JS_PS_END
    };

    return props;
}

% for attrName, attrData in members.items():
    % if not attrData.readonly:
bool ${ classname }::JSSetter_${ attrName }(JSContext *cx, JS::MutableHandleValue vp)
{
    % if isinstance(attrData.type, SimpleType):
        ${ defs.jsval2c('vp', idl_type(attrData.type), 'inArg_0') }
    % else:
        ${ defs.jsval2c('vp', attrData.type.name, 'inArg_0') }
    % endif

    return this->set_${ attrName }(inArg_0);
}
    % endif


bool ${ classname }::JSGetter_${ attrName }(JSContext *cx, JS::MutableHandleValue vp)
{
   <% 
        need = idl_type(attrData.type)
    %>
    % if need == 'DOMSTRING':
        JS::RootedString jstr(cx, JS_NewStringCopyZ(cx, this->get_${ attrName }()));
        vp.setString(jstr);
    % elif not hasattr(SimpleType, need):
        //TODO Interface ${ need.name }
    % else:
        ${ idl_type(attrData.type)|ctype } cval = this->get_${ attrName }();
        JS::RootedValue jval(cx);
        if (!JS::${ need | convert }(cx, jval, &cval)) {
            JS_ReportError(cx, "TypeError");
            return false;
        }
       vp.set(jval);
    % endif

    return true;
}
    % endfor
// }}} End Members
% endif

void ${ classname }::RegisterObject(JSContext *cx)
{
     ${ classname }::ExposeClass<${ constructors['maxArgs'] }>(cx, "${ classname}");
     //TODO HAS_RESERVED_SLOTS
}
// }}}

} // namespace Binding
} // namespace Nidium

