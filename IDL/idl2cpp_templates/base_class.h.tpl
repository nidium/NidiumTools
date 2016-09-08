#include <Core/Utils.h>
#include <Binding/JSUtils.h>
<%!
from idl2cpp_transformer import ctype, jsvaltype, convert, capitalize
%>

//#include "${foo}"

namespace Nidium {
namespace Binding {

class ${ classname } {
% for memberName, member in members:
    //{$ memberName }
% endfor
}

} // namespace Binding
} // namespace Nidium
