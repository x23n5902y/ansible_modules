from collections import OrderedDict
try:
    from ansible.module_utils.dsmsys_parser.standalone import Transformer
except ImportError:
    HAS_PARSER=False


class TreeToJson(Transformer):
    def VALUE(self, token):
        if token.isnumeric():
            token.value = int(token.value)
        return token

    def section(self, token, sections=OrderedDict()):
        section, section_name = token[0:2]
        sections.update(
            {
                section_name.value: {
                    k.children[0].value.upper(): k.children[1].value for k in token[2:]
                }
            }
        )
        return sections