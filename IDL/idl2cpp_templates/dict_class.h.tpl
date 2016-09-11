<%!
from idl2cpp_transformer import ctype, jsvaltype, convert, capitalize, idl_type
from pywidl.model import SimpleType
%>

<%namespace name="defs" file="defs.tpl" import="arglst, jsval2c"/>

#pragma once

#include <Dict.h>

namespace Nidium {
namespace Binding {

// {{{ Dict_${ name }
class Dict_${ name } : public Dict
{
public:
    Dict_${ name }() {
        % for attrData in members:
        <% type = idl_type(attrData.type) %>
        % if type == 'DOMSTRING':
        m_${ attrData.name } = ${ 'NULL' if not attrData.default else "strdup(" + attrData.default.value + ");" }
        % else:
        m_${ attrData.name } = ${ 'NULL' if not attrData.default else attrData.default.value };
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
        % for attrData in members:
        <% type = idl_type(attrData.type) %>

        if (!JS_GetProperty(cx, curobj, "${ attrData.name }", &curopt)) {
            return false;
        } else {
            % if type == 'DOMSTRING':
            JS::RootedString curstr(cx, JS::ToString(cx, curopt));
            JSAutoByteString c_curstr(cx, curstr);

            m_${ attrData.name } = strdup(c_curstr.ptr());
            % elif type == 'UNSIGNED_SHORT':
            if (!JS::ToUint16(cx, curopt, &m_${ attrData.name })) {
                return false;
            }
            % endif
        }
        % endfor

        return true;
    }
    % for attrData in members:
    const ${ idl_type(attrData.type)|ctype } ${ attrData.name }() const {
        return m_${ attrData.name };
    }

    % endfor
private:
    % for attrData in members:
    ${ idl_type(attrData.type)|ctype } m_${ attrData.name };
    % endfor
};
// }}}

} // namespace Binding
} // namespace Nidium

