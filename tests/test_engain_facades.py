def test_engain_facade_imports_smoke():
    import engain.kernels.navigation as navigation
    import engain.kernels.spatial as spatial
    import engain.kernels.perception as perception
    import engain.render.trixel as trixel
    import engain.world.field as field

    assert navigation is not None
    assert spatial is not None
    assert perception is not None
    assert trixel is not None
    assert field is not None


def test_navigation_core_symbols_available():
    from engain.kernels.navigation import create_empty_grid, find_path

    assert callable(create_empty_grid)
    assert callable(find_path)
