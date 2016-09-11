<%!
from idl2cpp_transformer import ctype, jsvaltype, convert, capitalize, idl_type
from pywidl.model import SimpleType
%>

<%def name="argcall(args)" >
    % for arg in args:
       ${ arg.name }${ ' ' if loop.last else ', ' }
    % endfor
</%def>


<%def name="arglst(args)" >
    % for arg in args:
        % if isinstance(arg.type, SimpleType):
            ${ idl_type(arg.type) | ctype } ${ arg.name }${ ' ' if loop.last else ', ' }
        % else:
            ${ arg.type.name } ${ arg.name }${ ' ' if loop.last else ', ' }
        % endif
    % endfor
</%def>

<%def name="jsval2c(jval, need, dest, returning='false')" >
    % if need == 'DOMSTRING':
        JS::RootedString __curstr(cx, JS::ToString(cx, ${ jval }));
        if (!__curstr) {
            JS_ReportError(cx, "TypeError");
            return ${ returning };
        }
        JSAutoByteString __curstr_c;
        __curstr_c.encodeUtf8(cx, __curstr);

        char *${ dest } = __curstr_c.ptr();
    % elif not hasattr(SimpleType, need):
        //TODO: Interface ${ need.name} 
    % else:
        ${ need|ctype } ${ dest };
        if (!JS::${ need | convert }(cx, ${ jval }, &${ dest })) {
            JS_ReportError(cx, "TypeError");
            return ${ returning };
        }
    % endif
</%def>


