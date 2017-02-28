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

%define test_args_decl {
{%- for fix, inject in fixtures -%}
{% if inject and fix.return_type %}, {{fix.return_type}} {{fix.name}}{% endif %}
{%- endfor -%}
%}

%section test_decl {
static void
hypo_test_{{name}}(hypo_context_t *hypo_ctx{{test_args_decl}})
{
#replace code
}
%}

%define fix_call {
{% for fix, inject in fixtures -%}
{% if fix.return_type %}  {{fix.name}} = {% else %}  {% endif -%}
hypo_fix_setup_{{fix.name}}(hypo_ctx);
{% endfor %}
%}

%define test_args {
{%- for fix, inject in fixtures -%}
{% if inject and fix.return_type %}, {{fix.name}}{% endif %}
{%- endfor -%}
%}

%define fix_cleanup {
{% for fix, inject in fixtures -%}
{% if fix.cleanup %}  hypo_fix_teardown_{{fix.name}}(
{%- if fix.return_type %}{{fix.name}}{% endif %});
{% endif -%}
{% endfor %}
%}

%section test_call {
  /* Save the test name */
  hypo_ctx->cur_test = "{{name}}";

  /* Let the user know what's being tested */
  printf("%s::%s... ", hypo_ctx->test_fname, hypo_ctx->cur_test);
  fflush(stdout);

  /* Initialize fixtures for {{name}} */
#replace fix_call

  /* Run the test */
  hypo_test_{{name}}(hypo_ctx{{test_args}});

  /* Clean up the fixtures for {{name}} */
#replace fix_cleanup

  /* Finally, clean up the mocks for {{name}} */
  _hypo_mock_cleanup();

  /* Let the user know of the status of the test */
  printf((hypo_ctx->flags & _HYPO_FLAG_FAIL) ? "FAIL\n" : "PASS\n");
  hypo_ctx->flags &= ~_HYPO_FLAG_FAIL;

  /* Check if we encountered a fatal error while running {{name}} */
  if (hypo_ctx->flags & _HYPO_FLAG_FATAL)
    return 0;

%}
