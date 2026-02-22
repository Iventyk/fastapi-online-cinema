import datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from pytest_mock import MockerFixture

from src.main import app
from src.exceptions import MovieAlreadyPurchased, OrderNotFound
from src.exceptions.orders import PendingOrderExists, OrderAlreadyPaid
from src.databases.models.orders import StatusEnum

ROUTER_MODULE = "src.routers.orders"


class TestOrderRouterExceptions:

    @pytest.mark.asyncio
    async def test_create_order_bad_request(
        self, client: AsyncClient, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            f"{ROUTER_MODULE}.create_order",
            side_effect=MovieAlreadyPurchased("Already purchased"),
        )

        response = await client.post("/orders/", json={"movie_ids": [1, 2]})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Already purchased"

    @pytest.mark.asyncio
    async def test_cancel_order_not_found(
        self, client: AsyncClient, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            f"{ROUTER_MODULE}.cancel_order",
            side_effect=OrderNotFound("Order not found"),
        )

        response = await client.patch("/orders/999/cancel")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_admin_all_orders_forbidden(
        self, client: AsyncClient, auth_user_schema
    ) -> None:
        response = await client.get("/orders/admin/all/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestOrderRouterSuccess:

    @pytest.mark.asyncio
    async def test_create_order_success(
        self, client: AsyncClient, mocker: MockerFixture, test_order
    ) -> None:
        mock_order_data = {
            "id": test_order.id,
            "user_id": test_order.user_id,
            "total_amount": float(test_order.total_amount),
            "status": "pending",
            "items": [],
            "created_at": datetime.datetime.now().isoformat(),
        }

        mock_res = {
            "order": mock_order_data,
            "removed_purchased": [],
            "removed_unavailable": [],
            "removed_pending": [],
            "message": "Success",
        }

        mocker.patch(f"{ROUTER_MODULE}.create_order", return_value=mock_res)

        response = await client.post("/orders/", json={"movie_ids": [1]})

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Success"
        assert "order" in data

    @pytest.mark.asyncio
    async def test_list_my_orders_success(
        self, client: AsyncClient, mocker: MockerFixture, test_order
    ) -> None:
        mock_order_data = {
            "id": test_order.id,
            "user_id": test_order.user_id,
            "total_amount": float(test_order.total_amount),
            "status": "cancelled",
            "items": [],
            "created_at": datetime.datetime.now().isoformat(),
        }

        mocker.patch(
            f"{ROUTER_MODULE}.get_user_orders", return_value=[mock_order_data]
        )

        response = await client.get("/orders/all/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_cancel_order_success(
        self, client: AsyncClient, mocker: MockerFixture, test_order
    ) -> None:
        test_order.status = StatusEnum.CANCELLED
        mock_order_data = {
            "id": test_order.id,
            "user_id": test_order.user_id,
            "total_amount": float(test_order.total_amount),
            "status": "cancelled",
            "items": [],
            "created_at": datetime.datetime.now().isoformat(),
        }

        mocker.patch(
            f"{ROUTER_MODULE}.cancel_order", return_value=mock_order_data
        )

        response = await client.patch(f"/orders/{test_order.id}/cancel")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_create_order_pending_exists_400(
        self, client: AsyncClient, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            f"{ROUTER_MODULE}.create_order",
            side_effect=PendingOrderExists("Pending order exists"),
        )
        response = await client.post("/orders/", json={"movie_ids": [1]})
        assert response.status_code == 400
        assert response.json()["detail"] == "Pending order exists"

    @pytest.mark.asyncio
    async def test_cancel_order_already_paid_400(
        self, client: AsyncClient, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            f"{ROUTER_MODULE}.cancel_order",
            side_effect=OrderAlreadyPaid(
                "Paid orders can only be cancelled via refund"
            ),
        )
        response = await client.patch("/orders/1/cancel")
        assert response.status_code == 400
        assert "refund_url" in response.json()["detail"]
