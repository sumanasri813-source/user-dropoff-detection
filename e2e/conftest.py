from __future__ import annotations

import os

import pytest

from src.db.connection import get_session_factory, init_database
from src.db.models import UserProfile
from src.utils.auth import hash_password


@pytest.fixture(scope="session", autouse=True)
def seed_admin_user() -> None:
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:8000")
    admin_user = os.getenv("E2E_ADMIN_USER", "admin@example.com")
    admin_password = os.getenv("E2E_ADMIN_PW", "password")

    if not base_url:
        return

    init_database()
    session_factory = get_session_factory()

    with session_factory() as session:
        user = session.query(UserProfile).filter(
            (UserProfile.email == admin_user) | (UserProfile.external_user_id == admin_user)
        ).first()

        if user is None:
            user = UserProfile(
                external_user_id=admin_user,
                email=admin_user,
                password_hash=hash_password(admin_password),
                roles="admin",
            )
            session.add(user)
        else:
            user.email = admin_user
            user.password_hash = hash_password(admin_password)
            user.roles = "admin"

        session.commit()