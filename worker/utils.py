# import json
# import pickle
# import pendulum
# import requests
# import yaml
# from app.core.settings import settings
# from app.core.telemetry import logger
# def transform_json_distrib_to_bees(json_data, yaml_name):
#     """
#     with open(json_name + '.json', encoding='utf-8') as json_file:
#         json_data = json.load(json_file)
#     """
#     with open(yaml_name + ".yaml", encoding="utf-8") as yaml_file:
#         yaml_config = yaml.safe_load(yaml_file)
#     formated_payload = []
#     for item_payload in json_data:
#         payload_item = {}
#         for item in yaml_config:
#             is_list = item.endswith("[]")
#             key = item[:-2] if is_list else item
#             config = yaml_config[item]
#             type_name = config.get("type", "string")
#             source_path = config.get("source")
#             default_value = config.get("defaultValue")
#             temp_data = None
#             if source_path:
#                 try:
#                     if "+" in source_path:
#                         # Concatenação de múltiplos campos
#                         concat_parts = [p.strip() for p in source_path.split("+")]
#                         raw_values = []
#                         for part in concat_parts:
#                             path_parts = part.split(".")
#                             value = get_value_from_json_path(item_payload, path_parts)
#                             raw_values.append(str(value))
#                         raw_value = " ".join(raw_values)
#                     else:
#                         # Campo único
#                         path_parts = source_path.split(".")
#                         raw_value = get_value_from_json_path(item_payload, path_parts)
#                         temp_data = type_converters[type_name](raw_value)
#                 except Exception:
#                     continue
#             elif default_value is not None:
#                 try:
#                     temp_data = type_converters[type_name](default_value)
#                 except Exception:
#                     continue
#             if temp_data is None:
#                 continue
#             # Monta o payload final
#             parts = key.split(".")
#             current = payload_item
#             for i, part in enumerate(parts):
#                 is_last = i == len(parts) - 1
#                 if is_last:
#                     if is_list:
#                         current.setdefault(part, []).append(temp_data)
#                     else:
#                         current[part] = temp_data
#                 else:
#                     if part.endswith("[]"):
#                         part = part[:-2]
#                         current = current.setdefault(part, [{}])[0]
#                     else:
#                         current = current.setdefault(part, {})
#         formated_payload.append(payload_item)
#     return formated_payload
# def validate_token():
#     try:
#         logger.info("Validating token.")
#         object_token = pickle.loads(client_redis.get("token"))
#     except TypeError:
#         logger.info("Token not exists. Getting new token.")
#         get_token()
#         object_token = pickle.loads(client_redis.get("token"))
#     now = pendulum.now("America/Sao_Paulo")
#     if now > object_token.get("max_time"):
#         logger.info("Token expired. Getting new token.")
#         get_token()
#     return pickle.loads(client_redis.get("token")).get("access_token")
# def send_payload_to_bees_put(payload, entity: str, version: str, set_url: str):
#     token = validate_token()
#     body = {
#         "entity": entity,
#         "version": version,
#         "payload": json.dumps(payload, ensure_ascii=False),
#     }
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": "Bearer " + token,
#         "country": "PE",
#         "requestTraceId": settings.REQUEST_TRACE_ID,
#         "timezone": "America/Lima",
#     }
#     response = requests.put(
#         settings.URL + set_url,
#         headers=headers,
#         data=json.dumps(body),
#     )
#     return response.status_code, response.text
# def transform_json_distrib_to_bees_dict(json_data, yaml_name):
#     with open(yaml_name + ".yaml", encoding="utf-8") as yaml_file:
#         yaml_config = yaml.safe_load(yaml_file)
#     payload_item = {}
#     for item in yaml_config:
#         is_list = item.endswith("[]")
#         key = item[:-2] if is_list else item
#         config = yaml_config[item]
#         type_name = config.get("type", "string")
#         source_path = config.get("source")
#         default_value = config.get("defaultValue")
#         temp_data = None
#         if source_path:
#             try:
#                 if "+" in source_path:
#                     # Concatenação de múltiplos campos
#                     concat_parts = [p.strip() for p in source_path.split("+")]
#                     raw_values = []
#                     for part in concat_parts:
#                         path_parts = part.split(".")
#                         value = get_value_from_json_path(json_data, path_parts)
#                         raw_values.append(str(value))
#                     raw_value = " ".join(raw_values)
#                 else:
#                     # Campo único
#                     path_parts = source_path.split(".")
#                     raw_value = get_value_from_json_path(json_data, path_parts)
#                 temp_data = type_converters[type_name](raw_value)
#             except Exception:
#                 continue
#         elif default_value is not None:
#             try:
#                 temp_data = type_converters[type_name](default_value)
#             except Exception:
#                 continue
#         if temp_data is None:
#             continue
#         # Monta o payload final
#         parts = key.split(".")
#         current = payload_item
#         for i, part in enumerate(parts):
#             is_last = i == len(parts) - 1
#             if is_last:
#                 if is_list:
#                     current.setdefault(part, []).append(temp_data)
#                 else:
#                     current[part] = temp_data
#             else:
#                 if part.endswith("[]"):
#                     part = part[:-2]
#                     current = current.setdefault(part, [{}])[0]
#                 else:
#                     current = current.setdefault(part, {})
#     return payload_item
