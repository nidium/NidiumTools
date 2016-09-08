<%!
from idl2cpp_transformer import ctype, jsvaltype, convert, capitalize, idl_type
from pywidl.model import SimpleType
%>

<%def name="arglst(args)" >
    % for arg in args:
        % if isinstance(arg.type, SimpleType):
            ${ idl_type(arg.type) | ctype } ${ arg.name }${ ' ' if loop.last else ', ' }
        % else:
            ${ arg.type.name } ${ arg.name }${ ' ' if loop.last else ', ' }
        % endif
    % endfor
</%def>

<%def name="jsval2c(jval, need, dest)" >
    % if need == 'DOMSTRING':
        JS::RootedString __curstr(cx, JS::ToString(cx, ${ jval }));
        if (!__curstr) {
            JS_ReportError(cx, "TypeError");
            return false;
        }
        JSAutoByteString __curstr_c;
        __curstr_c.encodeUtf8(cx, __curstr);

        char *${ dest } = __curstr_c.ptr();
    % elif not hasattr(SimpleType, need):
        //TODO: Interface
    % else:
        ${ need|ctype } ${ dest };
        if (!JS::${ need | convert }(cx, ${ jval }, &${ dest })) {
            JS_ReportError(cx, "TypeError");
            return false;
        }
    % endif
</%def>

#pragma once
#include <Binding/JSExposer.h>

namespace Nidium {
namespace Binding {

// {{{ ${ classname }

class Interface_${ classname }
{
public:
    template <typename T>
    static bool registerObject(JSContext *cx, JS::HandleObject exports = JS::NullPtr());

    % if ctor:
        /* These static(s) must be implemented */
        % for constructor in constructors['lst']:
        /*
          static Interface_${ classname } *Constructor(${ arglst(constructor.arguments) });
        */
        % endfor

        template <typename T>
        static bool js_${ classname }_Constructor(JSContext *cx, unsigned argc, JS::Value *vp);
    % endif
    /* Properties */
    % for attrName, attr in members.items():
        virtual ${ attr.type.type|ctype } ${ attr.name };
    % endfor

    /* Methods */
    % for attrName, attr in operations.items():
         % for op in attr['lst']:
             virtual ${ idl_type(op.return_type)|ctype } ${ op.name }(${ arglst(op.arguments) }) = 0;
         % endfor
    % endfor

    /* JS Natives */
    % for attrName, attrData in operations.items():
        static bool js_${attrName}(JSContext *cx, unsigned argc, JS::Value *vp);
    % endfor

    static void JSFinalize(JSFreeOp *fop, JSObject *obj)
    {

    }
private:
};
// }}}

// {{{ Preamble
static JSClass ${ classname }_class = {
    "${ classname }", JSCLASS_HAS_PRIVATE,
    JS_PropertyStub, JS_DeletePropertyStub, JS_PropertyStub, JS_StrictPropertyStub,
    JS_EnumerateStub, JS_ResolveStub, JS_ConvertStub, Interface_${ classname }::JSFinalize,
    nullptr, nullptr, nullptr, nullptr, JSCLASS_NO_INTERNAL_MEMBERS
};

static JSFunctionSpec ${ classname }_funcs[] = {
    % for attrName, attrData in operations.items():
        JS_FN("${ attrName }", Interface_${ classname }::js_${ attrName }, ${ attrData['maxArgs'] }, 0),
    % endfor
    JS_FS_END
};
// }}}}

// {{{ Implementation
// {{{ Construction
% if ctor:
template <typename T>
bool Interface_${ classname }::js_${ classname }_Constructor(JSContext *cx, unsigned argc, JS::Value *vp)
{
    JS::CallArgs args = JS::CallArgsFromVp(argc, vp);
    if (!args.isConstructing()) {
        JS_ReportError(cx, "Bad constructor");
        return false;
    }

    unsigned argcMin = ((${ constructors['maxArgs'] } > argc) ? (argc) : (${ constructors['maxArgs'] }));

    switch (argcMin) {
        % for op in constructors['lst']:
            case ${ len(op.arguments) }:
            {
                /* Start arguments convertion */

                % for arg in op.arguments:
                    /* Handle argument #${ loop.index } of type "${ idl_type(arg.type) }" */
                    % if not arg.type.nullable:
                        if (args[${ loop.index }].isNull()) {
                            JS_ReportError(cx, "TypeError");
                            return false;
                        }
                    % endif
                    ${ jsval2c('args['+ str(loop.index) +']', idl_type(arg.type), 'inArg_' + str(loop.index)) }
                % endfor

                /* End of arguments convertion */

                T *ret = T::Constructor(
                    % for i in range(0, len(op.arguments)):
                            inArg_${ i }${ ' ' if loop.last else ', ' }
                    % endfor
               );

                if (!ret) {
                    JS_ReportError(cx, "TypeError");
                    return false;
                }

                JS::RootedObject rthis(cx, JS_NewObjectForConstructor(cx, &${ classname }_class, args));

                JS_SetPrivate(rthis, ret);

                args.rval().setObjectOrNull(rthis);

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

% endif
// }}}

// {{{ Operations
% for attrName, attrData in operations.items():
bool Interface_${ classname }::js_${ attrName }(JSContext *cx, unsigned argc, JS::Value *vp)
{
    JS::CallArgs args = JS::CallArgsFromVp(argc, vp);
    JS::RootedObject caller(cx, JS_THIS_OBJECT(cx, vp));

    if (!caller) {
        JS_ReportError(cx, "Illegal invocation");
        return false;
    }

    Interface_${ classname } *obj = (Interface_${ classname } *)JS_GetInstancePrivate(cx, caller, &${ classname }_class, NULL);
    if (!obj) {
        JS_ReportError(cx, "Illegal invocation");
        return false;
    }

    unsigned argcMin = ((${ attrData['maxArgs'] } > argc) ? (argc) : (${ attrData['maxArgs'] }));

    switch (argcMin) {
        % for op in attrData['lst']:
        case ${ len(op.arguments) }:
        {
            /* Start arguments convertion */
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
                    ${ jsval2c('args[' + str(loop.index) + ']', idl_type(arg.type), 'inArg_' + str(loop.index)) }
                % else:
                    ${ jsval2c('args[' + str(loop.index) + ']', arg.type.name, 'inArg_' + str(loop.index)) }
                % endif
            % endfor

            /* End of arguments convertion */
            % if op.return_type.type != SimpleType.VOID:
                ${ idl_type(op.return_type)|ctype } _opret =
            %endif
            obj->${ attrName }(
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
// }}}
% endfor
// }}}

// {{{ Registration
template <typename T>
bool Interface_${ classname }::registerObject(JSContext *cx,
    JS::HandleObject exports)
{
    % if ctor:
        JS::RootedObject to(cx);

        to = exports ? exports : JS::CurrentGlobalOrNull(cx);

        JS_InitClass(cx, to, JS::NullPtr(), &${ classname }_class,
            Interface_${classname}::js_${classname}_Constructor<T>,
            0, NULL, ${ classname }_funcs, NULL, NULL);
    % endif
    return true;
}
// }}}

} // namespace Binding
} // namespace Nidium

