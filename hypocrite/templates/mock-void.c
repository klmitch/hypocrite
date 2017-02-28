/* Copyright (C) 2017 by Kevin L. Mitchell <klmitch@mit.edu>
**
** Licensed under the Apache License, Version 2.0 (the "License"); you
** may not use this file except in compliance with the License. You
** may obtain a copy of the License at
**
**     http://www.apache.org/licenses/LICENSE-2.0
**
** Unless required by applicable law or agreed to in writing, software
** distributed under the License is distributed on an "AS IS" BASIS,
** WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
** implied. See the License for the specific language governing
** permissions and limitations under the License.
*/

%define arg_any {
{% for type, arg in args -%}
#define ANYARG_{{name|upper}}_{{arg|upper}} {{"0x%08x"|format(2**loop.index0)}}
{% endfor %}
%}

%define arg_struct {
{% for type, arg in args -%}
  {{type}} {{arg}};
{% endfor %}
%}

%define arg_storage {
{% for type, arg in args -%}
  _call_storage->{{arg}} = {{arg}};
{% endfor %}
%}

%define arg_compare {
{% for type, arg in args -%}
    if (!(expected[i]._any_flags & ANYARG_{{name|upper}}_{{arg|upper}}))
      hypo_assert(expected[i].{{arg}} == actual->{{arg}});
{% endfor %}
%}

%define mock_args {
{%- for type, arg in args -%}
, {{type}} {{arg}}
{%- endfor -%}
%}

%define call_args {
{%- for type, arg in args -%}
{% if not loop.first %}, {% endif %}{{arg}}
{%- endfor -%}
%}

%define macro_args {
{%- for type, arg in args -%}
{% if not loop.first %}, {% endif %}({{arg}})
{%- endfor -%}
%}

%section mock_decl {
#replace arg_any

/* Represent calls that we expect to be made; the _any_flags element
 * can be used to indicate that we don't care about the value of a
 * specific argument.
 */
typedef struct {
  unsigned long _any_flags;
#replace arg_struct
} hypo_mock_expectcalls_{{name}};

/* Represent actual calls to the mock.  The file and line from which
 * the call was made are recorded in the _file and _line elements.
 */
typedef struct {
  const char *_file;
  unsigned int _line;
#replace arg_struct
} hypo_mock_actualcalls_{{name}};

/* Represent the state of the mock.  Keeps track of what the mock
 * should return, and what arguments it's been called with.
 */
static struct {
  int spy;
  _hypo_list_t calls;
} _hypo_mock_descriptor_{{name}} = {
  1, /* indicates "spy" mode */
  _HYPO_LIST_INIT(hypo_mock_actualcalls_{{name}})
};

/* Implementation of the mock itself.  This is called by the mock
 * macro, and either calls the underlying function or returns the
 * configured return values.  Stores the call location and the
 * arguments the mock was called with.  This is the core of the mock
 * system.
 */
static void
_hypo_mock_{{name}}(const char *_file, unsigned int _line{{mock_args}})
{
  hypo_mock_actualcalls_{{name}} *_call_storage;

  /* Store the call details */
  _call_storage = (hypo_mock_actualcalls_{{name}}*)_hypo_list_alloc(
    &_hypo_mock_descriptor_{{name}}.calls
  );
  _call_storage->_file = _file;
  _call_storage->_line = _line;
#replace arg_storage

  /* If in spy mode, call the underlying function */
  if (_hypo_mock_descriptor_{{name}}.spy)
    {{name}}({{call_args}});

  return;
}

/* Turn off spy mode for the mock. */
static void
hypo_mock_nospy_{{name}}(void)
{
  /* Switch to mock mode */
  _hypo_mock_descriptor_{{name}}.spy = 0;
}

/* Check the calls to the mock.  This walks through each of the
 * expected calls, verifying that it matches the corresponding actual
 * call to the mock.
 */
static void
_hypo_mock_checkcalls_{{name}}(
    hypo_context_t *hypo_ctx,
    hypo_mock_expectcalls_{{name}} *expected,
    unsigned int count
)
{
  unsigned int i, len;
  hypo_mock_actualcalls_{{name}} *actual;

  /* How many calls were there actually? */
  len = _hypo_list_len(&_hypo_mock_descriptor_{{name}}.calls);

  /* Verify we were called exactly count times */
  hypo_assert(count == len);

  /* Check each of the calls */
  for (i = 0; i < _hypo_min(count, len); i++) {
    actual = (hypo_mock_actualcalls_{{name}} *)_hypo_list_ref(
      &_hypo_mock_descriptor_{{name}}.calls, i
    );

#replace arg_compare
  }
}

/* The macro.  This is used to ensure that the hypocrite context is
 * passed to the _hypo_mock_checkcalls_{{name}} function.
 */
#define hypo_mock_checkcalls_{{name}}(expected, count)			\
  _hypo_mock_checkcalls_{{name}}(hypo_ctx, (expected), (count))

/* Retrieve the number of calls that have been made to the mock. */
#define hypo_mock_callcount_{{name}}()			\
  _hypo_list_len(&_hypo_mock_descriptor_{{name}}.calls)

/* Retrieve the Nth call description; this is an internal convenience
 * macro for building the macros for accessing the call arguments.
 */
#define _hypo_mock_getcall_{{name}}(i)			\
  ((hypo_mock_actualcalls_{{name}} *)_hypo_list_ref(	\
     &_hypo_mock_descriptor_{{name}}.calls, (i)		\
  ))

/* Get the file name from which the Nth call to the mock was made.
 * This will be "const char *".
 */
#define hypo_mock_getfile_{{name}}(i) (_hypo_mock_getcall_{{name}}(i)->_file)

/* Get the line number from which the Nth call to the mock was made.
 * This will be "int".
 */
#define hypo_mock_getline_{{name}}(i) (_hypo_mock_getcall_{{name}}(i)->_line)

/* Get the named argument for the Nth call to the mock.  This will be
 * whatever type was defined for that argument.  The argument name
 * must be a bare word specifying the argument name given when
 * declaring the mock.
 */
#define hypo_mock_getarg_{{name}}(i, arg)	\
  (_hypo_mock_getcall_{{name}}(i)->arg)

/* Clean up the mock.  This is called after every test function run
 * and ensures that the mock is returned to its initial state ("spy"
 * mode), not to mention releasing any memory allocated during the
 * test.
 */
static void
_hypo_mock_cleanup_{{name}}(void)
{
  /* Reset mock to "spy" mode */
  _hypo_mock_descriptor_{{name}}.spy = 1;

  /* And clean up the lists */
  _hypo_list_cleanup(&_hypo_mock_descriptor_{{name}}.calls);
}
%}

%section mock_install {
#undef {{name}}
#define {{name}}({{call_args}})				\
  _hypo_mock_{{name}}(__FILE__, __LINE__{{macro_args}})
%}

%section mock_uninstall {
#undef {{name}}
%}

%section mock_cleanup {
  _hypo_mock_cleanup_{{name}}();
%}
