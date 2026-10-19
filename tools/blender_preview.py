"""Render all exported cuboid models in Blender, including cast states."""

import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import blender_fish3d as legacy


def render(group=None):
    legacy.setup_scene()
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 320
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    output = ROOT / "build/preview3d"
    output.mkdir(parents=True, exist_ok=True)
    for path in sorted((ROOT / "models3d").rglob("*.json")):
        relative = path.relative_to(ROOT / "models3d")
        category = relative.parts[0] if len(relative.parts) > 1 else ""
        if group is not None and category != group:
            continue
        data = json.loads(path.read_text())
        texture = data["textures"]["0"].split(":", 1)[1]
        image = bpy.data.images.load(
            str(ROOT / "assets/hnmt/textures" / Path(texture + ".png")),
            check_existing=True,
        )
        obj = legacy.build_object(path.stem, data["elements"], image)
        material = obj.data.materials[0]
        nodes = material.node_tree.nodes
        material.node_tree.links.new(
            nodes.get("Image Texture").outputs["Alpha"],
            nodes.get("Principled BSDF").inputs["Alpha"],
        )
        if hasattr(material, "surface_render_method"):
            material.surface_render_method = "DITHERED"
        name = (
            "_".join(relative.with_suffix("").parts)
            if category != "fish"
            else path.stem
        ) + ".png"
        scene.render.filepath = str(output / name)
        bpy.ops.render.render(write_still=True)
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        bpy.data.materials.remove(material)
        print("REVIEW_RENDER", relative, len(data["elements"]), flush=True)


if __name__ == "__main__":
    render()
