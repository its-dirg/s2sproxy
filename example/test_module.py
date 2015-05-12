import json

__author__ = 'mathiashedstrom'

from s2sproxy.util.attribute_module_base import AttributeModuleBase


class TestModule(AttributeModuleBase):
    def __init__(self, json_file, translation, attribute_matcher):
        AttributeModuleBase.__init__(self, translation, attribute_matcher)

        with open(json_file) as f:
            self.user_data = json.load(f)

        self.global_data = {'university': 'Small university', 'co': 'Sweden'}

    def get_user_data(self):
        return self.user_data

    def get_global_data(self):
        return self.global_data
