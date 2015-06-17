__author__ = 'mathiashedstrom'


class NoUserData(Exception):
    pass


class AttributeModule(object):
    def get_user_data(self):
        raise NotImplementedError

    def get_global_data(self):
        raise NotImplementedError

    def _find_user(self, idp_attribute_values):
        users = self.get_user_data()

        for user in users:
            if self.attribute_matcher(user, idp_attribute_values):
                return user
        return None

    def get_attributes(self, idp_attributes):
        user_data = self._find_user(idp_attributes)
        if not user_data:
            raise NoUserData(
                "No user data found for '{}'.".format(idp_attributes))
        user_data.update(self.get_global_data())
        return self._translate(user_data)

    def _translate(self, attributes):
        """
        Rename the added attributes (user specific and global) to SAML.
        """
        for backing_attr_name, saml_attr_name in self.translation.iteritems():
            attributes[saml_attr_name] = attributes.pop(backing_attr_name)

        return attributes
