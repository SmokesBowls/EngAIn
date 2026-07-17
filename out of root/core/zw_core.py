# core/zw_core.py — RECONSTRUCTED SHIM (2026-07-16)
#
# The original core/zw_core.py was lost (it may still exist in the photorec
# deep archive under /mnt/data-drive/burdens/photorec_sda1_2026-03-14.*, but
# no recovered file matching it has been found yet). The ZW editor GUI
# (old_zw_gui_enhanced.py) and official_zw_validator.py import parse_zw from
# here; gui/zw/zw_parser.py carries the same parse_zw API and is proven by
# tests/test_gui_local_zonb_roundtrip.py against the ZONB packer.
#
# If the original zw_core.py is ever recovered, replace this file with it.

from gui.zw.zw_parser import parse_zw  # noqa: F401

__all__ = ["parse_zw"]
