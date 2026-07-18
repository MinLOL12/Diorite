import re
from pathlib import Path
from typing import Dict
from ..core.config import get_projects_dir
import json

class ScaffoldService:
    def __init__(self):
        self.projects_root = get_projects_dir()

    def _resolve(self, project_id: str) -> Path:
        p = self.projects_root / project_id
        if not p.exists():
            raise FileNotFoundError(f"Project {project_id} not found")
        return p

    def _sanitize_class(self, name: str) -> str:
        # Convert e.g., "ruby_block" -> "RubyBlock"
        name = re.sub(r'[^a-zA-Z0-9_ ]', '', name)
        parts = re.split(r'[_\s]+', name)
        class_name = ''.join([part.capitalize() for part in parts if part])
        if not class_name:
            class_name = "Example"
        if class_name[0].isdigit():
            class_name = "Custom" + class_name
        return class_name

    def _sanitize_id(self, name: str) -> str:
        return re.sub(r'[^a-z0-9_]', '', name.lower().replace(' ', '_').replace('-', '_'))

    def _find_package_path(self, project_path: Path, mod_id: str) -> Path:
        # Find java source root that contains mod main class
        candidates = list(project_path.rglob("src/main/java"))
        if not candidates:
            # fallback
            src = project_path / "src" / "main" / "java" / "com" / "example" / mod_id
            src.mkdir(parents=True, exist_ok=True)
            return src
        # Look for subfolder containing mod_id
        for base in candidates:
            # Check if any file contains MOD_ID constant
            # Simplify: return base / com / example / mod_id or first mod package
            mod_path = base / "com" / "example" / mod_id
            if mod_path.exists():
                return mod_path
            # Also check for any package structure
            # Use first existing deepest
            for sub in base.rglob("*.java"):
                return sub.parent
        # Fallback to first src/main/java + com/example/mod_id
        return candidates[0] / "com" / "example" / mod_id

    def _get_mod_id(self, project_path: Path, project_id: str) -> str:
        meta_file = project_path / ".diorite" / "project.json"
        if meta_file.exists():
            try:
                data = json.loads(meta_file.read_text())
                return data.get("mod_id", project_id.lower())
            except:
                pass
        return project_id.lower().replace("-", "_")

    def create_block(self, project_id: str, name: str, material: str = "STONE", creative_tab: str = "BUILDING_BLOCKS") -> dict:
        project_path = self._resolve(project_id)
        mod_id = self._get_mod_id(project_path, project_id)
        class_name = self._sanitize_class(name) + "Block"
        block_id = self._sanitize_id(name)

        package_path = self._find_package_path(project_path, mod_id)
        package_path.mkdir(parents=True, exist_ok=True)

        block_dir = package_path / "block"
        block_dir.mkdir(parents=True, exist_ok=True)

        block_file = block_dir / f"{class_name}.java"
        block_package = self._infer_package(project_path, block_dir)

        block_content = f"""package {block_package};

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.block.SoundType;

public class {class_name} extends Block {{
    public {class_name}() {{
        super(BlockBehaviour.Properties.of()
            .mapColor(MapColor.{material})
            .strength(3.0f, 6.0f)
            .sound(SoundType.STONE)
            .requiresCorrectToolForDrops()
        );
    }}
}}
"""

        block_file.write_text(block_content)

        # Create registration snippet
        # Look for ModBlocks or similar, if not create
        mod_blocks_file = package_path / "registry" / "ModBlocks.java"
        mod_blocks_file.parent.mkdir(parents=True, exist_ok=True)

        if not mod_blocks_file.exists():
            reg_package = self._infer_package(project_path, mod_blocks_file.parent)
            mod_blocks_content = f"""package {reg_package};

import {block_package}.{class_name};
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.Block;

public class ModBlocks {{
    public static final Block {block_id.upper()} = register("{block_id}", new {class_name}());

    private static Block register(String name, Block block) {{
        return Registry.register(BuiltInRegistries.BLOCK, ResourceLocation.fromNamespaceAndPath("{mod_id}", name), block);
    }}

    public static void registerAll() {{
        // Called from main mod initializer
        System.out.println("Registering blocks for {mod_id}");
    }}
}}
"""
            mod_blocks_file.write_text(mod_blocks_content)
        else:
            # Append to existing
            try:
                content = mod_blocks_file.read_text()
                new_line = f'    public static final Block {block_id.upper()} = register("{block_id}", new {class_name}());\n'
                # Insert before private static register method or before last }
                if new_line.strip() not in content:
                    # Simple insertion before "private static Block register"
                    content = content.replace("    private static Block register", new_line + "\n    private static Block register")
                    mod_blocks_file.write_text(content)
            except:
                pass

        # Create block item registration hint, model json, etc
        resources_blockstate = project_path / "src" / "main" / "resources" / "assets" / mod_id / "blockstates"
        resources_blockstate.mkdir(parents=True, exist_ok=True)
        (resources_blockstate / f"{block_id}.json").write_text(json.dumps({
            "variants": {"": {"model": f"{mod_id}:block/{block_id}"}}
        }, indent=2))

        resources_models_block = project_path / "src" / "main" / "resources" / "assets" / mod_id / "models" / "block"
        resources_models_block.mkdir(parents=True, exist_ok=True)
        (resources_models_block / f"{block_id}.json").write_text(json.dumps({
            "parent": "block/cube_all",
            "textures": {"all": f"{mod_id}:block/{block_id}"}
        }, indent=2))

        resources_models_item = project_path / "src" / "main" / "resources" / "assets" / mod_id / "models" / "item"
        resources_models_item.mkdir(parents=True, exist_ok=True)
        (resources_models_item / f"{block_id}.json").write_text(json.dumps({
            "parent": f"{mod_id}:block/{block_id}"
        }, indent=2))

        return {"files_created": [str(block_file.relative_to(project_path)), str(mod_blocks_file.relative_to(project_path))], "block_id": block_id, "class": class_name}

    def create_item(self, project_id: str, name: str, stack_size: int = 64, creative_tab: str = "INGREDIENTS") -> dict:
        project_path = self._resolve(project_id)
        mod_id = self._get_mod_id(project_path, project_id)
        class_name = self._sanitize_class(name) + "Item"
        item_id = self._sanitize_id(name)

        package_path = self._find_package_path(project_path, mod_id)
        item_dir = package_path / "item"
        item_dir.mkdir(parents=True, exist_ok=True)

        item_package = self._infer_package(project_path, item_dir)

        # For simple items we can generate a registration helper without custom class if stack_size is default
        # But generate custom class anyway for extensibility
        item_file = item_dir / f"{class_name}.java"
        item_content = f"""package {item_package};

import net.minecraft.world.item.Item;

public class {class_name} extends Item {{
    public {class_name}() {{
        super(new Properties().stacksTo({stack_size}));
    }}
}}
"""
        item_file.write_text(item_content)

        # Registration file
        mod_items_file = package_path / "registry" / "ModItems.java"
        mod_items_file.parent.mkdir(parents=True, exist_ok=True)

        if not mod_items_file.exists():
            reg_package = self._infer_package(project_path, mod_items_file.parent)
            mod_items_content = f"""package {reg_package};

import {item_package}.{class_name};
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;

public class ModItems {{
    public static final Item {item_id.upper()} = register("{item_id}", new {class_name}());

    private static Item register(String name, Item item) {{
        return Registry.register(BuiltInRegistries.ITEM, ResourceLocation.fromNamespaceAndPath("{mod_id}", name), item);
    }}

    public static void registerAll() {{
        System.out.println("Registering items for {mod_id}");
    }}
}}
"""
            mod_items_file.write_text(mod_items_content)
        else:
            try:
                content = mod_items_file.read_text()
                new_line = f'    public static final Item {item_id.upper()} = register("{item_id}", new {class_name}());\n'
                if new_line.strip() not in content:
                    content = content.replace("    private static Item register", new_line + "\n    private static Item register")
                    mod_items_file.write_text(content)
            except:
                pass

        # Model
        resources_models_item = project_path / "src" / "main" / "resources" / "assets" / mod_id / "models" / "item"
        resources_models_item.mkdir(parents=True, exist_ok=True)
        (resources_models_item / f"{item_id}.json").write_text(json.dumps({
            "parent": "item/generated",
            "textures": {"layer0": f"{mod_id}:item/{item_id}"}
        }, indent=2))

        return {"files_created": [str(item_file.relative_to(project_path))], "item_id": item_id, "class": class_name}

    def create_entity(self, project_id: str, name: str, category: str = "CREATURE", width: float = 0.6, height: float = 1.8) -> dict:
        project_path = self._resolve(project_id)
        mod_id = self._get_mod_id(project_path, project_id)
        class_name = self._sanitize_class(name) + "Entity"
        entity_id = self._sanitize_id(name)

        package_path = self._find_package_path(project_path, mod_id)
        entity_dir = package_path / "entity"
        entity_dir.mkdir(parents=True, exist_ok=True)
        entity_package = self._infer_package(project_path, entity_dir)

        entity_file = entity_dir / f"{class_name}.java"
        entity_content = f"""package {entity_package};

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.level.Level;

public class {class_name} extends Animal {{
    public {class_name}(EntityType<? extends Animal> type, Level world) {{
        super(type, world);
    }}

    public static EntityType<{class_name}> createType() {{
        return EntityType.Builder.of({class_name}::new, MobCategory.{category})
            .sized({width}f, {height}f)
            .build("{entity_id}");
    }}

    @Override
    public net.minecraft.world.entity.AgeableMob getBreedOffspring(net.minecraft.server.level.ServerLevel world, net.minecraft.world.entity.AgeableMob entity) {{
        return null;
    }}
}}
"""
        entity_file.write_text(entity_content)

        return {"files_created": [str(entity_file.relative_to(project_path))], "entity_id": entity_id}

    def create_screen(self, project_id: str, name: str) -> dict:
        project_path = self._resolve(project_id)
        mod_id = self._get_mod_id(project_path, project_id)
        class_name = self._sanitize_class(name) + "Screen"
        screen_id = self._sanitize_id(name)

        package_path = self._find_package_path(project_path, mod_id)
        screen_dir = package_path / "screen"
        screen_dir.mkdir(parents=True, exist_ok=True)
        screen_package = self._infer_package(project_path, screen_dir)

        screen_file = screen_dir / f"{class_name}.java"
        content = f"""package {screen_package};

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

public class {class_name} extends AbstractContainerScreen<{class_name}Menu> {{

    public {class_name}({class_name}Menu menu, Inventory inventory, Component title) {{
        super(menu, inventory, title);
    }}

    @Override
    protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {{
        // TODO: render background texture
        // graphics.blit(ResourceLocation.fromNamespaceAndPath("{mod_id}", "textures/gui/{screen_id}.png"), leftPos, topPos, 0, 0, imageWidth, imageHeight);
    }}

    @Override
    public void render(GuiGraphics graphics, int mouseX, int mouseY, float delta) {{
        renderBackground(graphics, mouseX, mouseY, delta);
        super.render(graphics, mouseX, mouseY, delta);
        renderTooltip(graphics, mouseX, mouseY);
    }}
}}

class {class_name}Menu extends net.minecraft.world.inventory.AbstractContainerMenu {{
    public {class_name}Menu(int syncId, Inventory inv) {{
        super(null, syncId);
    }}
    @Override
    public net.minecraft.world.item.ItemStack quickMoveStack(net.minecraft.world.entity.player.Player player, int slot) {{
        return net.minecraft.world.item.ItemStack.EMPTY;
    }}
    @Override
    public boolean stillValid(net.minecraft.world.entity.player.Player player) {{
        return true;
    }}
}}
"""
        screen_file.write_text(content)
        return {"files_created": [str(screen_file.relative_to(project_path))], "screen_id": screen_id}

    def create_recipe(self, project_id: str, name: str, recipe_type: str = "shaped") -> dict:
        project_path = self._resolve(project_id)
        mod_id = self._get_mod_id(project_path, project_id)
        recipe_id = self._sanitize_id(name)

        recipe_dir = project_path / "src" / "main" / "resources" / "data" / mod_id / "recipe"
        recipe_dir.mkdir(parents=True, exist_ok=True)

        if recipe_type == "shaped":
            data = {
                "type": "minecraft:crafting_shaped",
                "pattern": ["###", "# #", "###"],
                "key": {"#": {"item": f"{mod_id}:{recipe_id}"}},
                "result": {"item": f"{mod_id}:{recipe_id}", "count": 1}
            }
        elif recipe_type == "shapeless":
            data = {
                "type": "minecraft:crafting_shapeless",
                "ingredients": [{"item": f"{mod_id}:{recipe_id}"}],
                "result": {"item": f"{mod_id}:{recipe_id}", "count": 1}
            }
        else:  # smelting
            data = {
                "type": "minecraft:smelting",
                "ingredient": {"item": f"{mod_id}:{recipe_id}"},
                "result": f"{mod_id}:{recipe_id}",
                "experience": 0.7,
                "cookingtime": 200
            }

        file_path = recipe_dir / f"{recipe_id}.json"
        file_path.write_text(json.dumps(data, indent=2))
        return {"files_created": [str(file_path.relative_to(project_path))], "recipe_id": recipe_id}

    def create_data_component(self, project_id: str, name: str, component_type: str = "Integer") -> dict:
        project_path = self._resolve(project_id)
        mod_id = self._get_mod_id(project_path, project_id)
        class_name = self._sanitize_class(name) + "Component"
        comp_id = self._sanitize_id(name)

        package_path = self._find_package_path(project_path, mod_id)
        comp_dir = package_path / "component"
        comp_dir.mkdir(parents=True, exist_ok=True)
        comp_package = self._infer_package(project_path, comp_dir)

        file_path = comp_dir / f"{class_name}.java"

        # Map simple types
        type_map = {
            "Integer": "Integer",
            "String": "String",
            "Boolean": "Boolean",
            "Float": "Float"
        }
        java_type = type_map.get(component_type, "Integer")

        content = f"""package {comp_package};

import com.mojang.serialization.Codec;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;

public class {class_name} {{
    public static final DataComponentType<{java_type}> {comp_id.upper()} = Registry.register(
        BuiltInRegistries.DATA_COMPONENT_TYPE,
        ResourceLocation.fromNamespaceAndPath("{mod_id}", "{comp_id}"),
        DataComponentType.<{java_type}>builder().persistent(Codec.{'INT' if java_type=='Integer' else 'STRING' if java_type=='String' else 'BOOL' if java_type=='Boolean' else 'FLOAT'}).build()
    );

    public static void register() {{
        System.out.println("Registering data component {comp_id} for {mod_id}");
    }}
}}
"""
        file_path.write_text(content)
        return {"files_created": [str(file_path.relative_to(project_path))], "component_id": comp_id}

    def _infer_package(self, project_root: Path, file_dir: Path) -> str:
        # Infer package from path relative to src/main/java
        try:
            for base in project_root.rglob("src/main/java"):
                base = base.resolve()
                try:
                    rel = file_dir.resolve().relative_to(base)
                    return ".".join(rel.parts)
                except ValueError:
                    continue
        except:
            pass
        # Fallback guess
        return "com.example.mod"
