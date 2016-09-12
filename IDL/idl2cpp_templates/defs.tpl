{% macro argcall(args) %}
    {% for arg in args %}
       {{ arg.name }}{{ ' ' if loop.last else ', ' }}
    {% endfor %}
{% endmacro %}


{% macro arglst(args) %}
    {% for arg in args %}
        {# if isinstance(arg.type, SimpleType) #}
            {{ arg.type|idl_type|ctype }} {{ arg.name }}{{ ' ' if loop.last else ', ' }}
        {# else #}
            {#{ arg.type.name }} {{ arg.name }}{{ ' ' if loop.last else ', ' }#}
        {# endif #}
    {% endfor %}
{% endmacro %}

{% macro jsval2c(jval, need, dest, returning='false') %}
    {% if need == 'DOMSTRING' %}
        JS::RootedString __curstr(cx, JS::ToString(cx, {{ jval }}));
        if (!__curstr) {
            JS_ReportError(cx, "TypeError");
            return {{ returning }};
        }
        JSAutoByteString __curstr_c;
        __curstr_c.encodeUtf8(cx, __curstr);

        char *{{ dest }} = __curstr_c.ptr();
    {% elif not need.__class__ == 'SimpleType' %}
        //TODO: Interface {{ need.name }}
    {% else %}
        {{ need|ctype }} {{ dest }};
        if (!JS::{{ need | convert }}(cx, {{ jval }}, &{{ dest }})) {
            JS_ReportError(cx, "TypeError");
            return {{ returning }};
        }
    {% endif %}
{% endmacro %}


