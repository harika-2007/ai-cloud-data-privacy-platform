"""Database seeding script for development and demo purposes."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import async_session_factory, initialize_database
from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.repositories.file_repository import FileRepository
from app.repositories.scan_repository import ScanResultRepository
from app.repositories.risk_repository import RiskAssessmentRepository


async def seed():
    await initialize_database()
    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        file_repo = FileRepository(session)
        scan_repo = ScanResultRepository(session)
        risk_repo = RiskAssessmentRepository(session)

        # Create admin user
        admin = await user_repo.create(
            name="Admin User",
            email="admin@example.com",
            password_hash=hash_password("Admin@123"),
            role="admin",
        )
        print(f"Created admin: {admin.email} / Admin@123")

        # Create analyst user
        analyst = await user_repo.create(
            name="Analyst User",
            email="analyst@example.com",
            password_hash=hash_password("Analyst@123"),
            role="analyst",
        )
        print(f"Created analyst: {analyst.email} / Analyst@123")

        # Create regular users
        for i in range(1, 4):
            user = await user_repo.create(
                name=f"Test User {i}",
                email=f"user{i}@example.com",
                password_hash=hash_password("User@12345"),
                role="user",
            )
            print(f"Created user: {user.email} / User@12345")

        await session.commit()
        print("\nSeed complete! Users created successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
