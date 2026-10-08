"""
Development seed script.
Usage: python -m scripts.seed
"""
from __future__ import annotations

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import AsyncSessionLocal
from src.services.auth_service import hash_password
from src.models.user import User
from src.models.application import Application
from src.models.controller import Controller
from src.models.endpoint import ApiEndpoint, HttpMethod
from src.utils.slugify import unique_slug


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # Create demo user
        user = User(
            email="demo@mockease.dev",
            username="demo",
            password_hash=hash_password("demo1234"),
        )
        session.add(user)
        await session.flush()

        # Create demo application
        app = Application(
            user_id=user.id,
            name="Demo API",
            slug=unique_slug("demo-api"),
            description="Automatically created demo application",
        )
        session.add(app)
        await session.flush()

        # Controller: Users
        users_ctrl = Controller(
            application_id=app.id,
            name="Users",
            description="User management endpoints",
        )
        session.add(users_ctrl)
        await session.flush()

        endpoints_data = [
            (HttpMethod.GET, "/users", "List users"),
            (HttpMethod.GET, "/users/{id}", "Get user by ID"),
            (HttpMethod.POST, "/users", "Create user"),
        ]
        for method, path, name in endpoints_data:
            ep = ApiEndpoint(
                controller_id=users_ctrl.id,
                name=name,
                method=method,
                path=path,
                response_status=200,
                response_body={"success": True, "data": []},
            )
            session.add(ep)

        # Controller: Products
        products_ctrl = Controller(
            application_id=app.id,
            name="Products",
            description="Product catalog endpoints",
        )
        session.add(products_ctrl)
        await session.flush()

        for method, path, name in [
            (HttpMethod.GET, "/products", "List products"),
            (HttpMethod.POST, "/products", "Create product"),
        ]:
            ep = ApiEndpoint(
                controller_id=products_ctrl.id,
                name=name,
                method=method,
                path=path,
                response_status=200,
                response_body={"success": True, "data": []},
            )
            session.add(ep)

        await session.commit()
        print(f"Seed complete. App slug: {app.slug}")


if __name__ == "__main__":
    asyncio.run(seed())
