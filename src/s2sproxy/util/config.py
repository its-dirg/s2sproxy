import copy
from saml2.config import config_factory, Config
from importlib import import_module
__author__ = 'haho0032'


def get_configurations(config_file, metadata_construction=True, metadata=None, cache=None):
    if config_file.endswith(".py"):
            config_file = config_file[:-3]
    conf = None
    try:
        conf = __import__(config_file, level=-1)
    except:
        pass
    assert conf, "No configuration/invalid file with the name: %s" % config_file
    #idp_conf = config_factory("idp", config_file)
    # assert conf.SP_ENTITY_CATEGORIES, "The configuration file must contain a list of entity categories in." \
    #                                   " SP_ENTITY_CATEGORIES"
    # assert isinstance(conf.SP_ENTITY_CATEGORIES, list), "SP_ENTITY_CATEGORIES must be a list."
    # assert len(conf.SP_ENTITY_CATEGORIES)>0, "SP_ENTITY_CATEGORIES list must not be empty."

    base_config = copy.deepcopy(copy.deepcopy(conf.CONFIG))

    idp_config = copy.deepcopy(base_config)
    idp_config["entityid"] = idp_config["entityid"]
    del(idp_config["service"]["sp"])
    new_endpoints = {}
    for endpoint in idp_config["service"]["idp"]["endpoints"]:
        new_endpoint = []
        for value in idp_config["service"]["idp"]["endpoints"][endpoint]:
            new_endpoint.append((value[0], value[1]))
        new_endpoints[endpoint] = new_endpoint
    idp_config["service"]["idp"]["endpoints"] = new_endpoints

    sp_configs = {}
    sp_config = {}
    # if hasattr(conf, 'SP_ENTITY_CATEGORIES'):
    #     sp_entity_categories = copy.deepcopy(conf.SP_ENTITY_CATEGORIES)
    #     if conf.SP_ENTITY_CATEGORIES_DEFAULT is not None:
    #         sp_entity_categories.append({"name": "default", "entcat": conf.SP_ENTITY_CATEGORIES_DEFAULT})
    #     for sp_cat in sp_entity_categories:
    #         sp_name = sp_cat["name"]
    #         sp_url = "/" + sp_name + "_sp"
    #         tmp_sp_config = copy.deepcopy(base_config)
    #         tmp_sp_config["entity_category"] = sp_cat["entcat"]
    #         del(tmp_sp_config["service"]["idp"])
    #         tmp_sp_config["entityid"] = tmp_sp_config["entityid"] % sp_url
    #         new_endpoints = {}
    #         for endpoint in tmp_sp_config["service"]["sp"]["endpoints"]:
    #             new_endpoint = []
    #             for value in tmp_sp_config["service"]["sp"]["endpoints"][endpoint]:
    #                 new_endpoint.append((value[0] % sp_url, value[1]))
    #             new_endpoints[endpoint] = new_endpoint
    #         tmp_sp_config["service"]["sp"]["endpoints"] = new_endpoints
    #         if metadata is not None:
    #             tmp_sp_config["metadata"] = {}
    #         sp_config = {
    #             "url": sp_url,
    #             "name": sp_name,
    #             "entity_id": tmp_sp_config["entityid"],
    #             "config": Config().load(tmp_sp_config, metadata_construction=True)
    #         }
    #         if metadata is not None:
    #             sp_config["config"].metadata = metadata
    #         sp_configs[sp_name] = sp_config
    if metadata is not None:
        idp_config["metadata"] = {}
    idp_config = Config().load(idp_config, metadata_construction=True)
    if metadata is not None:
        idp_config.metadata = metadata
    return idp_config, sp_configs