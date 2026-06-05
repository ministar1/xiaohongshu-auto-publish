from __future__ import annotations

from xiaohongshu_auto_publish.assets.library import AssetLibrary


def test_asset_library_append_filter_and_search(app_config: object) -> None:
    library = AssetLibrary(app_config)
    record = library.record_from_package("task-1", "default", "睡眠", "睡眠标题", ["健康"], "通过")
    library.append(record)
    assert library.list_by_account("default")[0].task_id == "task-1"
    assert library.search("睡眠")[0].title == "睡眠标题"
    assert library.list_by_account("missing") == []


def test_asset_library_account_shards(app_config: object) -> None:
    library = AssetLibrary(app_config)
    library.append(library.record_from_package("task-1", "a1", "主题", "标题", [], "通过"))
    library.append(library.record_from_package("task-2", "a2", "主题", "标题", [], "通过"))
    assert len(library.list_by_account("a1")) == 1
    assert len(library.list_by_account("a2")) == 1
