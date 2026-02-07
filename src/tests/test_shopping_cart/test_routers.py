from unittest.mock import AsyncMock
import pytest
from fastapi import status
from sqlalchemy import select

from src.databases.models import CartItem
from src.main import app
from src.securuty.utils import get_current_user

from src.exceptions import (
    UserNotExist,
    UserPermissionDenied,
    CartItemAlreadyExist,
    MovieDoesNotExist,
    CartItemDoesNotExist,
    CartItemsDoesNotExist,
    RepeatPurchaseNotAllowed,
)
from src.schemas import (
    MovieInCartSchema,
    CartItemCreateSchema,
    CartReadSchema,
    CurrentUser,
)

ROUTER_MODULE = "src.routers.shopping_cart"

class TestRouterExceptions:

    @pytest.mark.asyncio
    async def test_create_cart_item_raise_bad_request(
            self,
            client,
            test_user,
            test_movie,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        payload = {"movie_id": test_movie.id}

        mocker.patch(
            f"{ROUTER_MODULE}.create_new_cart_item",
            side_effect=UserNotExist
        )

        response = await client.post(
            f"/cart/{test_user.id}/",
            json=payload
        )

        

        assert response.status_code == status.HTTP_400_BAD_REQUEST


    @pytest.mark.asyncio
    async def test_create_cart_item_raise_forbidden(
            self,
            client,
            test_user,
            test_movie,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        payload = {"movie_id": test_movie.id}

        mocker.patch(
            f"{ROUTER_MODULE}.create_new_cart_item",
            side_effect=UserPermissionDenied("Not enough permission")
        )

        response = await client.post(
            f"/cart/{test_user.id}/",
            json=payload
        )

        

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_delete_cart_item_raise_bad_request(
            self,
            client,
            test_user,
            test_cart_item,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.remove_cart_item",
            side_effect=UserNotExist
        )

        response = await client.delete(
            f"/cart/{test_user.id}/{test_cart_item.id}",
        )

        

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_delete_cart_item_raise_forbidden(
            self,
            client,
            test_user,
            test_cart_item,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.remove_cart_item",
            side_effect=UserPermissionDenied
        )

        response = await client.delete(
            f"/cart/{test_user.id}/{test_cart_item.id}",
        )


        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_delete_cart_items_raise_bad_request(
            self,
            client,
            test_user,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.clear_cart",
            side_effect=UserNotExist
        )

        response = await client.delete(
            f"/cart/{test_user.id}/clean/",
        )


        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_delete_cart_items_raise_forbidden(
            self,
            client,
            test_user,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.clear_cart",
            side_effect=UserPermissionDenied
        )

        response = await client.delete(
            f"/cart/{test_user.id}/clean/",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_cart_items_bad_request(
            self,
            client,
            test_user,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.get_cart",
            side_effect=UserNotExist
        )

        response = await client.get(
            f"/cart/{test_user.id}/",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_get_cart_items_bad_request(
            self,
            client,
            test_user,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.get_cart",
            side_effect=UserPermissionDenied
        )

        response = await client.get(
            f"/cart/{test_user.id}/",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_purchased_cart_bad_request(
            self,
            client,
            test_user,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.get_purchased_items",
            side_effect=UserNotExist
        )

        response = await client.get(
            f"/cart/{test_user.id}/purchased/",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_get_purchased_cart_forbidden(
            self,
            client,
            test_user,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.get_purchased_items",
            side_effect=UserPermissionDenied
        )

        response = await client.get(
            f"/cart/{test_user.id}/purchased/",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRouterSuccessResponse:
    @pytest.mark.asyncio
    async def test_create_cart_item_success(
            self,
            client,
            test_user,
            test_movie,
            auth_user_schema,
            mocker
    ):

        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        payload = {"movie_id": test_movie.id}

        mock_response = MovieInCartSchema.model_validate(test_movie)

        mocker.patch(
            f"{ROUTER_MODULE}.create_new_cart_item",
            side_effect=AsyncMock(return_value=mock_response)
        )

        response = await client.post(
            f"/cart/{test_user.id}/",
            json=payload
        )

        

        data = response.json()

        assert response.status_code == status.HTTP_201_CREATED
        assert data["title"] == test_movie.name
        assert data["price"] == test_movie.price
        assert data["release_year"] == test_movie.year

    @pytest.mark.asyncio
    async def test_delete_cart_item_success(
            self,
            client,
            test_user,
            test_cart_item,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.remove_cart_item"
        )

        response = await client.delete(
            f"/cart/{test_user.id}/{test_cart_item.id}",
        )
        

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_delete_cart_items_success(
            self,
            client,
            test_user,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.clear_cart"
        )

        response = await client.delete(
            f"/cart/{test_user.id}/clean/",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_get_cart_items_success(
            self,
            client,
            test_user,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.get_cart"
        )

        response = await client.get(
            f"/cart/{test_user.id}/",
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_purchased_cart_success(
            self,
            client,
            test_user,
            auth_user_schema,
            mocker
    ):
        app.dependency_overrides[get_current_user] = lambda: auth_user_schema

        mocker.patch(
            f"{ROUTER_MODULE}.get_purchased_items"
        )

        response = await client.get(
            f"/cart/{test_user.id}/purchased/",
        )

        assert response.status_code == status.HTTP_200_OK
