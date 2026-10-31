# SQL schedule engine

Issue [#129](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/129)
is **not complete**. `views/schedules/bim_query.dl` implements a SELECT engine
over columns and cells supplied by its caller. No model-table adapter, saved
query definition or SQL editor is connected to the application yet.

The engine accepts a single source table, projection, WHERE, GROUP BY,
HAVING, ORDER BY, LIMIT and DISTINCT. It supports COUNT, SUM, AVG, MIN and
MAX, arithmetic, comparisons, LIKE, IN, BETWEEN, NULL checks and the scalar
functions listed at the top of its source. Errors return a message and a
character position. ORDER BY accepts a source expression, an output alias or
an output ordinal; an alias takes precedence over a source column with the
same name. Aliases are not available to WHERE.

This is a restricted dialect. All numbers use floating-point arithmetic,
including division. A plain column in an aggregate group reads the first
row. Joins are not implemented. Table names are parsed but the caller must
validate the requested table and supply its data. CSV output is available
for an engine result; it is not exposed as an application command.

## Validation

`views/schedules/tests/schedule_query_engine.dl` exercises 27 queries,
including invalid input, and CSV quoting. Its expected output includes the
result tables and positioned error messages. Fifteen successful query
results were also compared with SQLite on the same five-wall input, using
floating-point division for the integer-literal division example. This
checks those examples, not general SQL compatibility or model integration.

The recursive expression parser has an early error return so the pinned
compiler can infer its integer return type before descending. Without it,
the Linux compilation exhausted a bounded memory allocation before emitting
a diagnostic. The fixture also keeps an invalid query in a local variable
before taking its address.

Remaining work for #129: model tables and quantities, property access and
joins, persistent query definitions, an editor with column hints and inline
errors, and displaying/exporting results through schedules and sheets.
