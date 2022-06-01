import sys

from behave import *


@given('I am using Python 3')
def step_impl(context):
    print(sys.version_info.major)
    if sys.version_info.major == 3:
        pass
    else:
        assert False, f'Python version is {sys.version_info.major}'


@when('I calculate "{a}" plus "{b}"')
def step_impl(context, a, b):
    context._calc_result = a + b


@then('The result is "{x}"')
def step_impl(context, x):
    assert context._calc_result == x, f'Result was: {context._calc_result}'
