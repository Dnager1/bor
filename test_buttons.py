#!/usr/bin/env python3
"""
Button/View audit for Discord bot.
Validates button wiring, custom IDs, and handler coverage.
"""

from pathlib import Path
import asyncio

from cogs.main_control_panel import MainControlPanelView
from cogs.reservations_system import ReservationsMenuView, ReservationSectionView
from cogs.alliance_system import AllianceMenuView
from cogs.management_system import ManagementPanelView
from utils.buttons import MainMenuView as LegacyMainMenuView


def custom_ids_from_view(view):
    ids = []
    for child in view.children:
        custom_id = getattr(child, "custom_id", None)
        if custom_id:
            ids.append(custom_id)
    return ids


def assert_unique(items, title):
    duplicates = {item for item in items if items.count(item) > 1}
    if duplicates:
        raise AssertionError(f"{title}: duplicate custom_ids found: {sorted(duplicates)}")


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def assert_contains_all(source, tokens, title):
    missing = [token for token in tokens if token not in source]
    if missing:
        raise AssertionError(f"{title}: missing handlers/tokens: {missing}")


async def _async_main():
    print("🔎 Button audit started")

    # 1) Build views and verify custom IDs exist + unique
    main_ids = custom_ids_from_view(MainControlPanelView("123", is_admin=True, is_owner=True))
    res_menu_ids = custom_ids_from_view(ReservationsMenuView("123"))
    res_build_ids = custom_ids_from_view(ReservationSectionView("123", "building"))
    alliance_ids = custom_ids_from_view(AllianceMenuView("123", has_permissions=True))
    mgmt_ids = custom_ids_from_view(ManagementPanelView("123", is_owner=True))
    legacy_ids = custom_ids_from_view(LegacyMainMenuView())

    for title, ids in [
        ("MainControlPanelView", main_ids),
        ("ReservationsMenuView", res_menu_ids),
        ("ReservationSectionView", res_build_ids),
        ("AllianceMenuView", alliance_ids),
        ("ManagementPanelView", mgmt_ids),
        ("LegacyMainMenuView", legacy_ids),
    ]:
        if not ids:
            raise AssertionError(f"{title}: no custom_ids found")
        assert_unique(ids, title)

    # 2) Verify routing coverage in each cog
    main_source = read_text("cogs/main_control_panel.py")
    assert_contains_all(
        main_source,
        [
            "main_btn_alliance",
            "main_btn_reservations",
            "main_btn_management",
            "main_btn_language",
            "main_btn_my_info",
        ],
        "main_control_panel routing",
    )

    res_source = read_text("cogs/reservations_system.py")
    assert_contains_all(
        res_source,
        [
            "res_building",
            "res_training",
            "res_research",
            "res_my_reservations",
            "res_back_to_menu",
            "res_back",
            "res_create_",
            "res_schedule_",
        ],
        "reservations routing",
    )

    alliance_source = read_text("cogs/alliance_system.py")
    assert_contains_all(
        alliance_source,
        [
            "alliance_info",
            "alliance_members",
            "alliance_ranks",
            "alliance_back",
            "alliance_back_to_menu",
        ],
        "alliance routing",
    )

    mgmt_source = read_text("cogs/management_system.py")
    assert_contains_all(
        mgmt_source,
        [
            "mgmt_alliance",
            "mgmt_reservations",
            "mgmt_users",
            "mgmt_system",
            "mgmt_permissions",
            "mgmt_back",
            "mgmt_back_to_panel",
        ],
        "management routing",
    )

    print("✅ All button/view wiring checks passed")
    print("✅ Main panel buttons checked:", len(main_ids))
    print("✅ Reservations buttons checked:", len(res_menu_ids) + len(res_build_ids))
    print("✅ Alliance buttons checked:", len(alliance_ids))
    print("✅ Management buttons checked:", len(mgmt_ids))
    print("✅ Legacy utility buttons checked:", len(legacy_ids))


def main():
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
