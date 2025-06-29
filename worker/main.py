from typing import Dict

from worker.config import app


@app.task
def create_items(request: Dict[str, str]):
    # transformed = transform_json_distrib_to_bees(json_data=response[""], yaml_name="items")
    # response_bees = send_payload_to_bees_put(
    #     transformed,
    #     entity=request["BEES_ENTITY_ITEMS"],
    #     version=request["BEES_VERSION_API_V2"],
    #     set_url=request["BEES_URL_V1"],
    # )
    from icecream import ic

    ic(request)
    # await GenericRepository(settings.ITEMS).create(response)
    # return JSONResponse(status_code=200, content=response_bees)
