from .speedyapply_adapter import parse_speedyapply
from .jobright_adapter import parse_jobright
from .simplify_adapter import parse_simplify
from .zshah_adapter import parse_zshah
from .surya_adapter import parse_surya
from .table_adapter import parse_derec4, parse_negarprh, parse_mehek, parse_lorenzo

PARSERS = {
    "speedyapply": parse_speedyapply,
    "jobright": parse_jobright,
    "simplify": parse_simplify,
    "zshah": parse_zshah,
    "surya": parse_surya,
    "derec4": parse_derec4,
    "negarprh": parse_negarprh,
    "mehek": parse_mehek,
    "lorenzo": parse_lorenzo
}

def get_parser(parser_type):
    return PARSERS.get(parser_type)

