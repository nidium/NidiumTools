{% import "defs.tpl" as defs %}

#pragma once

#include <Dict.h>

namespace Nidium {
namespace Binding {

// {{ '{{{' Dict_{{ name }}
class Dict_{{ name }} : public Dict
{
public:
    Dict_{{ name }}() {
        {% for attrData in members %}
        {% if attrData.type|idl_type == 'DOMSTRING' %}
        m_{{ attrData.name }} = {{ 'NULL' if not attrData.default else "strdup(" + attrData.default.value + ");" }}
        {% else %}
        m_{{ attrData.name }} = {{ 'NULL' if not attrData.default else attrData.default.value }};
        {% endif %}
        {% endfor %}
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
        {% for attrData in members %}
        if (!JS_GetProperty(cx, curobj, "{{ attrData.name }}", &curopt)) {
            return false;
        } else {
            {% if attrData.type|idl_type == 'DOMSTRING' %}
            JS::RootedString curstr(cx, JS::ToString(cx, curopt));
            JSAutoByteString c_curstr(cx, curstr);

            m_{{ attrData.name }} = strdup(c_curstr.ptr());
            {% elif attrData.type|idl_type == 'UNSIGNED_SHORT' %}
            if (!JS::ToUint16(cx, curopt, &m_{{ attrData.name }})) {
                return false;
            }
            {% endif %}
        }
        {% endfor %}

        return true;
    }
    {% for attrData in members %}
    const {{ attrData.type|idl_type|ctype }} {{ attrData.name }}() const {
        return m_{{ attrData.name }};
    }

    {% endfor %}
private:
    {% for attrData in members %}
{{ '{{{' {{ attrData.type|idl_type)|ctype }} m_{{ attrData.name }};
    {% endfor %}
};
// {{ '}}}' }}

} // namespace Binding
} // namespace Nidium

