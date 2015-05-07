from saml2.config import config_factory

__author__ = 'haho0032'


def get_configurations(config_file, metadata_conf):
    sp_config = config_factory("sp", config_file)
    metadata = sp_config.load_metadata(metadata_conf)
    sp_config.metadata = metadata

    idp_config = config_factory("idp", config_file)
    metadata = idp_config.load_metadata(metadata_conf)
    idp_config.metadata = metadata

    return idp_config, sp_config