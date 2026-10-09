"""Rule engine: apply the saved layout (order, visibility, overrides) to the upstream guide."""
import gzip
import re

from lxml import etree

from . import xmltv

_PARSER = etree.XMLParser(recover=True, resolve_entities=False)


def guess_group(channel_id, name):
    """Starting group for a newly seen channel: "UK: BBC One" -> UK, "bbc1.uk" -> UK."""
    # ponytail: naive heuristic, XMLTV has no group concept. Groups are editable in the UI;
    # import group-title from the M3U playlist if real provider groups are needed.
    prefix = re.match(r"\s*([A-Za-z]{2,5})\s*[:|]", name)
    suffix = re.search(r"\.([A-Za-z]{2,3})$", channel_id)
    found = prefix or suffix
    return found[1].upper() if found else ""


def _child(el, tag, index=None):
    child = el.find(tag)
    if child is None:
        child = etree.Element(tag)
        el.insert(len(el) if index is None else index, child)
    return child


def apply_overrides(el, row):
    """Apply one layout row's display-name / logo / LCN overrides to its <channel> element."""
    if row["name"]:
        _child(el, "display-name", 0).text = row["name"]
    if row["icon"]:
        _child(el, "icon").set("src", row["icon"])
    if row["lcn"]:
        _child(el, "lcn").text = row["lcn"]
    return el


def _clean(value):
    return str(value).replace('"', "'").replace("\r", " ").replace("\n", " ")


def build_playlist(dst, layout):
    """Write the playlist body (everything after the #EXTM3U line) in player order; dst is replaced atomically."""
    tmp = dst.with_suffix(".part")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for row in layout:
            attrs = {
                "tvg-id": row["tvg"],
                "tvg-name": row["shown_name"],
                "tvg-logo": row["shown_icon"],
                "tvg-chno": row["shown_lcn"],
                "group-title": row["grp"],
            }
            ours = " ".join(f'{k}="{_clean(v)}"' for k, v in attrs.items() if v)
            f.write(f'#EXTINF:-1 {ours} {row["extra"] or ""}'.rstrip() + f',{_clean(row["shown_name"])}\n{row["url"]}\n')
    tmp.replace(dst)


def build(src, dst, layout):
    """Write dst (gzipped XMLTV): layout's channels in order, then their programmes streamed from src.

    dst is replaced atomically, so players never download a half-written guide.
    """
    keep = {row["id"] for row in layout}
    programmes = 0
    tmp = dst.with_suffix(".part")
    with gzip.open(tmp, "wb", compresslevel=6) as gz, etree.xmlfile(gz, encoding="utf-8") as xf:
        xf.write_declaration()
        with xf.element("tv", {"generator-info-name": "GuideForge"}):
            xf.write("\n")
            for row in layout:
                xf.write(apply_overrides(etree.fromstring(row["xml"], _PARSER), row))
                xf.write("\n")
            for el in xmltv.iter_elements(src):
                if el.tag == "programme" and el.get("channel") in keep:
                    xf.write(el)
                    programmes += 1
    tmp.replace(dst)
    return {"channels": len(layout), "programmes": programmes}
