#!/usr/bin/python

import sys
import imp

from datetime import datetime
from mako import exceptions
from mako.template import Template
from dokumentor import ParamDoc, NO_Default, IS_Obligated, IS_Optional

# """Transfer a (dokumentor).cpp.py file into a WebIDL file"""

Main_Template = """/* DO NOT EDIT MANUALLY, THIS FILE IS GENERATED
    at ${ when }
    by ${ prog }
    for ${ input }
*/

% for inst in instances:
${ inst }
% endfor
/* END OF GENERATED FILE ${ when } */"""

class IDLClass:
    """"
    >>> c = IDLClass("bla", {"methods": [], "constructors" : [], "callbacks": [], "methods": [], "events": []})
    >>> c.name
    'bla'
    >>> isinstance(c.details, dict)
    True
    >>> isinstance(c.templates, dict)
    True
    """
    def __init__(self, classname, class_details):
        self.name = classname
        self.details = class_details
        try:
            self.templates = {
            'prop_sig': Template("${ static } ${ readonly } attribute ${ typed } ${ short_name };"),
            'fun_sig': Template("${ static } ${ typed } ${ short_name }(${ arglist });"),
            'event_sig': Template("attribute ${ callback_name} ${ callback };"),
            'constructor': Template("Constructor(${ param_list })"),
            'callback': Template("""callback interface ${ callback_name } {
% for meth in methods:
    ${ meth },
% endfor
};\n"""),
            'extended': Template("""
[
% for constructor in constructors:
    ${ constructor },
% endfor
% if classname:
    classname = ${ classname }
% endif
]"""),
            'interface': Template("""
% for callback in callbacks:
    ${ callback }
% endfor
${header} interface ${ classname } {
% for prop in properties:
    ${ prop }
% endfor
% for method in methods:
    ${ method }
% endfor
% for event in events:
    ${ event }
% endfor
};\n"""),
}
        except:
            print(exceptions.text_error_template().render())
            sys.exit(1)
    def to_idl(self):
        constructors = []
        for name, details in self.details['constructors'].items():
            params = self.param_list(details.params)
            constructor = self.templates['constructor'].render(param_list=",".join(params))
            constructors.append(constructor)
        header = "\n" + self.templates['extended'].render(constructors=constructors,
                                                          classname=self.name)
        properties = []
        for name, details in self.details['properties'].items():
            static = ["", "static"][details.is_static.data is True]
            readonly = ["", "readonly"][details.is_readonly.data is True]
            types = []
            for typed in details.typed:
                typed = self.idl_type(typed)
                types.append(typed)
            typed = " or ".join(types)
            short_name = self.short_name(name)
            properties.append(self.templates['prop_sig'].render(static=static,
                                                                readonly=readonly,
                                                                typed=typed,
                                                                short_name=short_name)
                                                                )
        methods = []
        for name, details in self.details['methods'].items():
            static = ["", "static"][details.is_static.data is True]
            types = []
            if details.returns:
                for typed in details.returns.typed:
                    typed = self.idl_type(typed)
                    types.append(typed)
            else:
                types.append('void')
            typed = " or ".join(types)
            params = self.param_list(details.params)
            arglist = ", ".join(params)
            short_name = self.short_name(name)
            methods.append(self.templates['fun_sig'].render(static=static,
                                                            typed=typed,
                                                            short_name=short_name,
                                                            arglist=arglist)
                                                            )
        events = []
        callbacks = []
        for name, details in self.details['events'].items():
            #print(name, dir(details))
            short_name = self.short_name(name)
            callback_name = self.name + short_name.capitalize() + "EventHandler"
            callback = self.new_callback(short_name, callback_name, details)
            callbacks.append(callback)
            events.append(self.templates['event_sig'].render(callback_name=callback_name, callback=callback))
        return self.templates['interface'].render(header=header,
                                                           classname=self.name,
                                                           properties=properties,
                                                           methods=methods,
                                                           events=events,
                                                           callbacks=callbacks)
    def new_callback(self, name, callback_name, details):
        methods = []
        types = []
        if details.returns:
            for typed in details.returns.typed:
                typed = self.idl_type(typed)
                types.append(typed)
        else:
            types.append('void')
        typed = " or ".join(types)
        params = self.param_list(details.params);
        arglist = ", ".join(params)
        short_name = self.short_name(name)
        methods.append(self.templates['fun_sig'].render(static="",
                                                        typed=typed,
                                                        short_name=short_name,
                                                        arglist=arglist))
        code = self.templates['callback'].render(callback_name=callback_name,
                                                 methods=methods)
        return code
    def short_name(self, name):
        """
        >>> c = IDLClass("bla", {})
        >>> c.short_name("bla.go")
        'go'
        """
        short_name = str(name.replace(self.name + ".", ""))
        return short_name
    def param_list(self, details_params):
        """
        >>> c = IDLClass("bla", {})
        >>> params = [ParamDoc("host", "the hostname", "string", NO_Default, IS_Obligated), ParamDoc("port", "the port", "integer|string", 80, IS_Optional)]
        >>> c.param_list(params)
        ['string host', 'optional integer or string port']
        """
        params = []
        for param_details in details_params:
            optional = ("", "optional")[param_details.is_optional.data is True]
            types = []
            for typed in param_details.typed:
                typed = self.idl_type(typed)
                types.append(typed)
            typed = " or ".join(types)
            items = [optional, typed, str(param_details.name)]
            params.append(" ".join(items).strip())
        return params
    @staticmethod
    def idl_type(typed):
        return str(typed)

def main(program, dokumentor_in, idl_out):
    imp.load_source('DOCC', dokumentor_in)
    docs = sys.modules['DOCC'].DOC
    content = ''
    instances = []
    for class_name, class_details in docs['classes'].items():
        inst = IDLClass(class_name, class_details)
        instances.append(inst.to_idl())

    content = Template(Main_Template).render(instances=instances,
                                             when=datetime.now().isoformat(),
                                             prog=program,
                                             input=dokumentor_in)
    with open(idl_out, 'a') as file_h:
        file_h.write(content)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: " + sys.argv[0] + " in_documentor_file out_idl_file")
        sys.exit()
    if (not os.path.isfile(sys.argv[1])) or (not os.path.isfile(sys.argv[2])):
        print("One of the file does not exsist")
        sys.exit()
    main(sys.argv[0], sys.argv[1], sys.argv[2])
