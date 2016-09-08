<%!
from idl2cpp_transformer import ctype, jsvaltype, convert, capitalize, idl_type
%>
#pragma once

#include <Dict.h>

namespace Nidium {
namespace Binding {

// {{{ Dict_${ name }
class Dict_${ name } : public Dict
{
public:
    Dict_${ name }() {
        % for attr in members:
        <% type = idl_type(attr.type) %>
        % if type == 'DOMSTRING':
        m_${ attr.name } = ${ 'NULL' if not attr.default else "strdup(" + attr.default.value + ");" }
        % else:
        m_${ attr.name } = ${ 'NULL' if not attr.default else attr.default.value };
        % endif
        % endfor
    }

    /*
        TODO dtor
    */
    bool initWithJSVal(JSContext *cx, JS::HandleValue v)
    {
        if (!v.isObject()) {
            return false;
        }
        JS::RootedObject curobj(cx, &v.toObject());
        JS::RootedValue curopt(cx);
        % for attr in members:
        <% type = idl_type(attr.type) %>

        if (!JS_GetProperty(cx, curobj, "${ attr.name }", &curopt)) {
            return false;
        } else {
            % if type == 'DOMSTRING':
            JS::RootedString curstr(cx, JS::ToString(cx, curopt));
            JSAutoByteString c_curstr(cx, curstr);

            m_${ attr.name } = strdup(c_curstr.ptr());
            % elif type == 'UNSIGNED_SHORT':
            if (!JS::ToUint16(cx, curopt, &m_${ attr.name })) {
                return false;
            }
            % endif
        }
        % endfor

        return true;
    }

    % for attr in members:
    <% type = idl_type(attr.type) %>
    const ${ type|ctype } ${ attr.name }() const {
        return m_${ attr.name };
    }

    % endfor
private:
    % for attr in members:
    <% type = idl_type(attr.type) %>
    ${ type|ctype } m_${ attr.name };
    % endfor
};
// }}}

} // namespace Binding
} // namespace Nidium

