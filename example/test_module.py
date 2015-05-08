__author__ = 'mathiashedstrom'

from s2sproxy.util.attribute_module_base import AttributeModuleBase

class TestModule(AttributeModuleBase):

    def _get_user_data(self):
        return [
            {"email": ["a@test.com"],
             "testA": ["a@valueA"],
             "testB": ["a@valueB"]},
            {"email": ["b@test.com"],
             "testA": ["b@valueA"],
             "testB": ["b@valueB"]},
            {"email": ["c@test.com"],
             "testA": ["c@valueA"],
             "testB": ["c@valueB"]}
                ]

    def _get_global_data(self):
        return {
                "university": "small university",
                "co": "sweden",
                }

    def get_attributes(self, eduid_attributes):
        attributes = super(TestModule,self).get_attributes(eduid_attributes)
        eduid_attributes.update(attributes)
        return eduid_attributes
