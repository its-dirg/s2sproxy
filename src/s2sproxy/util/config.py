import copy
from saml2.config import config_factory, Config
from importlib import import_module
__author__ = 'haho0032'


def get_configurations(config_file, metadata_conf):
    if config_file.endswith(".py"):
        config_file = config_file[:-3]
    conf = None
    config_file = config_file.rstrip(".py")
    try:
        conf = __import__(config_file)
    except:
        raise Exception("No configuration/invalid file with the name: %s" % config_file)

    idp_config = copy.deepcopy(conf.CONFIG)

    # idp_config["entityid"] = idp_config["entityid"]
    # del(idp_config["service"]["sp"])
    # new_endpoints = {}
    # for endpoint in idp_config["service"]["idp"]["endpoints"]:
    #     new_endpoint = []
    #     for value in idp_config["service"]["idp"]["endpoints"][endpoint]:
    #         new_endpoint.append((value[0], value[1]))
    #     new_endpoints[endpoint] = new_endpoint
    # idp_config["service"]["idp"]["endpoints"] = new_endpoints

    # deal with metadata only once
    sp_config = config_factory("sp", config_file)
    metadata = sp_config.load_metadata(metadata_conf)
    sp_config.metadata = metadata

    if metadata is not None:
        idp_config["metadata"] = {}
    idp_config = Config().load(idp_config, metadata_construction=True)
    if metadata is not None:
        idp_config.metadata = metadata
    return idp_config, sp_config