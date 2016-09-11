/*
   Copyright 2016 Nidium Inc. All rights reserved.
   Use of this source code is governed by a MIT license
   that can be found in the LICENSE file.
*/
{% import 'defs.tpl' as defs %}

#include <Binding/ClassMapper.h>
#include "{{ classname }}.h"

namespace Nidium {
namespace Binding {

// {{ '{{{' }} JSBinding

{% if ctor %}
// {{ '{{{' }} Start Constructor
{{ classname }} *{{ classname }}::Constructor(JSContext *cx, JS::CallArgs &args,
    JS::HandleObject obj)
{
    unsigned argc = args.length();
    unsigned argcMin = (({{ constructors['maxArgs'] }} > argc) ? (argc) : ({{ constructors['maxArgs'] }}));

    switch (argcMin) {
        {% for op in constructors['lst'] %}
            case {{ op.arguments|length }}:
            {
                /* Start arguments conversion */
                {% for arg in op.arguments %}
                    /* Handle argument #{{ loop.index0 }} of type "{{ arg.type|idl_type }}" */
                    {% if not arg.type.nullable %}
                        if (args[{{ loop.index0 }}].isNull()) {
                            JS_ReportError(cx, "TypeError");
                            return nullptr;
                        }
                    {% endif %}
                    {{ defs.jsval2c('args[' ~ loop.index0 ~ ']', arg.type|idl_type, 'inArg_' ~  loop.index0 , 'nullptr') }}
                {% endfor %}
                /* End of arguments conversion */

                {{ classname }} *n_{{ classname }}_{{ foo }} = new {{ classname }}(
                    {% for i in range(0, op.arguments|length) %}
                            inArg_{{ i }}{{ ' ' if loop.last else ', ' }}
                    {% endfor %}
                );
                n_{{ classname }}_{{ foo }}->root();
                return n_{{ classname }}_{{ foo }};
                break;
            }
        {% endfor %}
        default:
            JS_ReportError(cx, "TypeError: wrong number of arguments");
            return nullptr;
            break;
    }

    return nullptr;
}
// {{ '}}}' }} End Constructor
{% endif %}

{% if (operations.items) > 0 %}
// {{ '{{{'  }} Start Operations
JSFunctionSpec * {{ classname }}::ListMethods()
{
    static JSFunctionSpec funcs[] = {
    {% for attrName, attrData in operations.items() %}
        CLASSMAPPER_FN({{ classname }}, {{ attrName }}, {{ attrData['maxArgs'] }} ),
    {% endfor %}

    JS_FS_END
    };

    return funcs;
}

{% for attrName, attrData in operations.items() %}
bool {{ classname }}::JS_{{ attrName }}(JSContext *cx, JS::CallArgs &args)
{
    unsigned argc = args.length();
    unsigned argcMin = (({{ attrData['maxArgs'] }} > argc) ? (argc) : ({{ attrData['maxArgs'] }}));

    switch (argcMin) {
        {% for op in attrData['lst'] %}
        case {{ op.arguments|length }}:
        {
            /* Start arguments conversion */
            {% for arg in op.arguments %}
                /* Handle argument #{{ loop.index0 }} of type "{{ arg.type|idl_type }}" */
                {% if not arg.type.nullable %}
                    if (args[{{ loop.index0 }}].isNull()) {
                        JS_ReportError(cx, "TypeError");
                        return false;
                    }
                {% endif %}
                {{ defs.jsval2c('args[' ~loop.index0 + ']', arg.type|idl_type, 'inArg_' ~ loop.index0) }}
            {% endfor %}

            /* End of arguments conversion */
            {% if op.return_type.type|idl_type != 'void' %}
                {{ op.return_type|idl_type|ctype }} _opret =
            {%endif %}
            this->{{ attrName }}(
                {% for i in range(0, op.arguments|length) %}
                    inArg_{{ i }}{{ ' ' if loop.last else ', ' }}
                {% endfor %}
                );
            {% if op.return_type.type|idl_type != 'void' %}
               args.rval().set{{ op.return_type|idl_type|jsvaltype|capitalize }}(_opret);
            {% endif %}

            break;
        }
        {% endfor %}
        default:
            JS_ReportError(cx, "TypeError: wrong number of arguments");
            return false;
            break;
    }

    return true;
}
{% endfor %}
// {{ '}}}' }} End Operations
{% endif %}

{% if (members.items) > 0 %}
// {{ '{{{' }} Start Members
JSPropertySpec *{{ classname }}::ListProperties()
{
    static JSPropertySpec props[] = {
    //todo ONLY-SETTER
    {% for attrName, attrData in members.items() %}
        {% if not attrData.readonly %}
            CLASSMAPPER_PROP_GS({{ classname }}, {{ attrData.name }}),
        {% endif %}
        CLASSMAPPER_PROP_G({{ classname }}, {{ attrData.name }}),
    {% endfor %}

        JS_PS_END
    };

    return props;
}

{% for attrName, attrData in members.items() %}
    {% if not attrData.readonly %}
bool {{ classname }}::JSSetter_{{ attrName }}(JSContext *cx, JS::MutableHandleValue vp)
{
    {{ defs.jsval2c('vp', attrData.type|idl_type, 'inArg_0') }}

    return this->set_{{ attrName }}(inArg_0);
}
    {% endif %}


bool {{ classname }}::JSGetter_{{ attrName }}(JSContext *cx, JS::MutableHandleValue vp)
{
        {% set need = attrData.type|idl_type %}
        {% if need == 'DOMSTRING' %}
            JS::RootedString jstr(cx, JS_NewStringCopyZ(cx, this->get_{{ attrName }}()));
            vp.setString(jstr);
        {% else %}
            {{ attrData.type|idl_type|ctype }} cval = this->get_{{ attrName }}();
            JS::RootedValue jval(cx);
            if (!JS::{{ need | convert }}(cx, jval, &cval)) {
                JS_ReportError(cx, "TypeError");
                return false;
            }
           vp.set(jval);
        {% endif %}

    return true;
}
    {% endfor %}
// {{ '}}}' }} End Members
{% endif %}

void {{ classname }}::RegisterObject(JSContext *cx)
{
     {{ classname }}::ExposeClass<{{ constructors['maxArgs'] }}>(cx, "{{ classname }}");
     //TODO HAS_RESERVED_SLOTS
}
// {{ '}}}' }}

} // namespace Binding
} // namespace Nidium

