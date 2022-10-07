from fastapi import APIRouter

router = APIRouter(prefix="/users")


@router.get("/{username}", tags=["users"])
async def get_user(username: str):
    """
    This is one endpoint I am creating to test how FastAPI works.

    I also want to understand how things are documented in OpenAPI
    """
    return {"username": username}
