from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


class TablesUtility:
    """Robot Framework library for table-driven keyword dispatch.

    Registers a keyword to be called once per row of a data table:

        When the following option should be selected in list:
            Register Table Keyword    My Keyword    ColA=arg1    ColB=arg2
            ^    ColA    ColB
            >    value1    value2
            >    value3    value4
    """

    ROBOT_LIBRARY_SCOPE = "TEST"

    def __init__(self):
        self._keyword = None
        self._arguments_names = None
        self._row_number = 1
        self._ignore_headers = False
        self._use_row_number = False
        self._args_map = {}
        self._named_argument_values = {}
        self._table_number = 1

    def register_table_keyword(
        self,
        keyword,
        ignore_headers=False,
        table_number=1,
        use_row_number=False,
        named_argument_values=None,
        **args_map,
    ):
        """Registers *keyword* to be called for every ``>`` row that follows.

        - ``args_map``: maps table column headers to keyword argument names
          (e.g. ``Option=value    List=target_element``).
        - ``named_argument_values``: fixed values injected into every row call
          without appearing in the table itself.
        - ``table_number``: distinguishes multiple tables in one test when the
          seeded row variables need to be unique.
        - ``use_row_number``: prepend the 1-based row index as the first arg.
        """
        self._keyword = keyword
        self._arguments_names = None
        self._row_number = 1
        self._ignore_headers = ignore_headers
        self._use_row_number = use_row_number
        self._args_map = args_map
        self._named_argument_values = named_argument_values or {}
        self._table_number = int(table_number)

    @keyword(name="^")
    def table_header(self, *headers):
        """Declares column names for the table that follows.

        Column names must exactly match the registered keyword's argument names
        (or the keys of *args_map* if remapping is in use).  Ignored when
        ``ignore_headers=True`` was passed to ``Register Table Keyword``.
        """
        if self._ignore_headers:
            return
        if not self._args_map:
            self._arguments_names = list(headers)
            return
        self._arguments_names = [
            self._args_map.get(h, h) for h in headers
        ]

    @keyword(name=">")
    def table_row(self, *arguments_values, **kwargs):
        """Calls the registered keyword with one row's worth of values.

        Stores the row values in ``${seeded_table_N_rowM_values}`` for later
        assertions, then increments the internal row counter.
        """
        builtin = BuiltIn()
        row_prefix = [str(self._row_number)] if self._use_row_number else []

        if self._arguments_names is None:
            builtin.run_keyword(self._keyword, *row_prefix, *arguments_values, **kwargs)
        else:
            pairs = dict(zip(self._arguments_names, arguments_values))
            for key in self._named_argument_values:
                if key in self._arguments_names:
                    raise AssertionError(
                        f"Table keyword has a registered value for '{key}' but that "
                        f"argument also appears in the table — only one source is allowed."
                    )
                pairs[key] = self._named_argument_values[key]
            # BuiltIn.run_keyword only accepts positional args; pass named args as "name=value"
            named_args = [f"{k}={v}" for k, v in pairs.items()]
            builtin.run_keyword(self._keyword, *row_prefix, *named_args)

        var_name = f"seeded_table_{self._table_number}_row{self._row_number}_values"
        builtin.set_test_variable(f"${{{var_name}}}", list(arguments_values))
        self._row_number += 1
