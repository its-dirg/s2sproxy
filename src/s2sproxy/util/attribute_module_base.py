__author__ = 'mathiashedstrom'


class NoUserData(Exception):
    pass


class SingleAttributeMatcher(object):
    def __init__(self, idp_attribute_name, backing_attribute_name):
        self.idp_attribute_name = idp_attribute_name
        self.backing_attribute_name = backing_attribute_name

    def __call__(self, user, idp_attribute_values):
        return any(value in user[self.backing_attribute_name] for value in
                   idp_attribute_values[self.idp_attribute_name])


class AttributeModuleBase(object):
    def __init__(self, translation, attribute_matcher):
        self.translation = translation
        self.attribute_matcher = attribute_matcher

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
