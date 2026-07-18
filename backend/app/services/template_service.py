import os
import shutil
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from ..core.config import TEMPLATES_DIR, SUPPORTED_LOADERS, SUPPORTED_MC_VERSIONS

class TemplateService:
    def __init__(self):
        self.templates_root = TEMPLATES_DIR
        self.templates_root.mkdir(parents=True, exist_ok=True)
        # Ensure built-in templates exist (create them if missing)
        self._ensure_builtin_templates()

    def _ensure_builtin_templates(self):
        # If templates folder empty, create default templates
        if not any(self.templates_root.iterdir()):
            self._create_fabric_template("1.21.1")
            self._create_fabric_template("1.20.1")
            self._create_neoforge_template("1.21.1")
            self._create_neoforge_template("1.20.6")
            self._create_forge_template("1.20.1")

    def _create_fabric_template(self, mc_version: str):
        loader_version = "0.107.0" if mc_version == "1.21.1" else "0.96.0"
        yarn_version = f"{mc_version}+build.1"
        tmpl_id = f"fabric-{mc_version}"
        tmpl_path = self.templates_root / tmpl_id
        tmpl_path.mkdir(parents=True, exist_ok=True)

        # Store meta
        (tmpl_path / "template.json").write_text(json.dumps({
            "id": tmpl_id,
            "name": f"Fabric {mc_version}",
            "loader": "fabric",
            "mc_version": mc_version,
            "loader_version": loader_version,
            "description": f"Fabric mod template for Minecraft {mc_version}",
            "java_version": 21 if mc_version.startswith("1.21") else 17
        }, indent=2))

        # Create minimal gradle project
        package_name = "com.example"
        # Use placeholders that will be replaced
        mod_id_placeholder = "{{MOD_ID}}"
        mod_name_placeholder = "{{MOD_NAME}}"

        # build.gradle
        (tmpl_path / "build.gradle").write_text(self._fabric_build_gradle(mc_version, loader_version, yarn_version))
        (tmpl_path / "settings.gradle").write_text('pluginManagement {\n repositories {\n  maven { name = "Fabric"; url = "https://maven.fabricmc.net/" }\n  gradlePluginPortal()\n }\n}\n')
        (tmpl_path / "gradle.properties").write_text(f"""org.gradle.jvmargs=-Xmx1G
org.gradle.parallel=true
# Fabric Properties
# https://fabricmc.net/develop/
minecraft_version={mc_version}
yarn_mappings={yarn_version}
loader_version={loader_version}
# Mod Properties
mod_version = 1.0.0
maven_group = com.example
archives_base_name = {mod_id_placeholder}
# Dependencies
fabric_version=0.107.0+{mc_version}
""")

        # gradlew stub
        (tmpl_path / "gradlew").write_text("#!/bin/sh\n echo \"Gradle Wrapper simulated by Diorite cache\"\n")
        (tmpl_path / "gradlew.bat").write_text("@echo off\necho Gradle Wrapper simulated by Diorite cache\n")

        # src structure
        src_main_java = tmpl_path / "src" / "main" / "java" / "com" / "example" / "{{MOD_ID}}"
        src_main_java.mkdir(parents=True, exist_ok=True)
        src_main_resources = tmpl_path / "src" / "main" / "resources"
        src_main_resources.mkdir(parents=True, exist_ok=True)

        # ExampleMod.java
        (src_main_java / "ExampleMod.java").write_text(f"""package com.example.{mod_id_placeholder};

import net.fabricmc.api.ModInitializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ExampleMod implements ModInitializer {{
    public static final String MOD_ID = "{mod_id_placeholder}";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    @Override
    public void onInitialize() {{
        LOGGER.info("Hello from {{MOD_NAME}}! Initializing...");
    }}
}}
""")

        # fabric.mod.json
        (src_main_resources / "fabric.mod.json").write_text(json.dumps({
            "schemaVersion": 1,
            "id": mod_id_placeholder,
            "version": "${version}",
            "name": mod_name_placeholder,
            "description": "A mod created with Diorite - zero-setup Minecraft IDE",
            "authors": ["Diorite User"],
            "contact": {"homepage": "https://github.com/MinLOL12/Diorite"},
            "license": "MIT",
            "icon": "assets/example/icon.png",
            "environment": "*",
            "entrypoints": {"main": [f"com.example.{mod_id_placeholder}.ExampleMod"]},
            "mixins": [f"{mod_id_placeholder}.mixins.json"],
            "depends": {"fabricloader": f">={loader_version}", "minecraft": mc_version, "java": ">=21" if mc_version.startswith("1.21") else ">=17", "fabric-api": "*"}
        }, indent=2))

        # mixins json
        (src_main_resources / f"{mod_id_placeholder}.mixins.json").write_text(json.dumps({
            "required": True,
            "minVersion": "0.8",
            "package": f"com.example.{mod_id_placeholder}.mixin",
            "compatibilityLevel": "JAVA_21" if mc_version.startswith("1.21") else "JAVA_17",
            "refmap": f"{mod_id_placeholder}.refmap.json",
            "mixins": [],
            "client": [],
            "injectors": {"defaultRequire": 1}
        }, indent=2))

    def _fabric_build_gradle(self, mc_version, loader_version, yarn_version):
        return f"""
plugins {{
    id 'fabric-loom' version '1.8-SNAPSHOT'
    id 'maven-publish'
}}

version = project.mod_version
group = project.maven_group

base {{
    archivesName = project.archives_base_name
}}

repositories {{
    // Add repositories to retrieve artifacts from in here.
    // You should only use this when depending on other mods because
    // Loom adds the essential maven repositories to download Minecraft and libraries from automatically.
    // See https://docs.gradle.org/current/userguide/declaring_repositories.html
    // for more information about repositories.
}}

loom {{
    splitEnvironmentSourceSets()

    mods {{
        "{self._placeholder('MOD_ID')}" {{
            sourceSet sourceSets.main
            sourceSet sourceSets.client
        }}
    }}
}}

dependencies {{
    // To change the versions see the gradle.properties file
    minecraft 'com.mojang:minecraft:${{project.minecraft_version}}'
    mappings 'net.fabricmc:yarn:${{project.yarn_mappings}}:v2'
    modImplementation 'net.fabricmc:fabric-loader:${{project.loader_version}}'

    // Fabric API. This is technically optional, but you probably want it anyway.
    modImplementation 'net.fabricmc.fabric-api:fabric-api:${{project.fabric_version}}'
}}

processResources {{
    inputs.property "version", project.version
    inputs.property "minecraft_version", project.minecraft_version

    filesMatching("fabric.mod.json") {{
        expand "version": project.version
    }}
}}

def targetJavaVersion = {21 if mc_version.startswith("1.21") else 17}
tasks.withType(JavaCompile).configureEach {{
    it.options.encoding = "UTF-8"
    if (targetJavaVersion >= 10 || JavaVersion.current().isJava10Compatible()) {{
        it.options.release = targetJavaVersion
    }}
}}

java {{
    def javaVersion = JavaVersion.toVersion(targetJavaVersion)
    if (JavaVersion.current() < javaVersion) {{
        toolchain.languageVersion = JavaLanguageVersion.of(targetJavaVersion)
    }}
    archivesBaseName = project.archives_base_name
    withSourcesJar()
}}

jar {{
    from("LICENSE") {{
        rename {{ "${{it}}_${{project.archivesBaseName}}"}}
    }}
}}
"""

    def _create_neoforge_template(self, mc_version: str):
        tmpl_id = f"neoforge-{mc_version}"
        tmpl_path = self.templates_root / tmpl_id
        tmpl_path.mkdir(parents=True, exist_ok=True)

        neo_version = "21.1.0" if mc_version == "1.21.1" else "21.0.0"
        (tmpl_path / "template.json").write_text(json.dumps({
            "id": tmpl_id,
            "name": f"NeoForge {mc_version}",
            "loader": "neoforge",
            "mc_version": mc_version,
            "loader_version": neo_version,
            "description": f"NeoForge mod template for Minecraft {mc_version}",
            "java_version": 21
        }, indent=2))

        (tmpl_path / "build.gradle").write_text(self._neoforge_build_gradle(mc_version, neo_version))
        (tmpl_path / "settings.gradle").write_text("pluginManagement { repositories { gradlePluginPortal(); maven { url = 'https://maven.neoforged.net/releases' } } }\nplugins { id 'org.gradle.toolchains.foojay-resolver-convention' version '0.8.0' }\n")
        (tmpl_path / "gradle.properties").write_text(f"""org.gradle.jvmargs=-Xmx3G
org.gradle.daemon=false
minecraft_version={mc_version}
neo_version={neo_version}
mod_version=1.0.0
maven_group=com.example
archives_base_name={{{{MOD_ID}}}}
""")
        (tmpl_path / "gradlew").write_text("#!/bin/sh\necho Gradle simulated\n")
        (tmpl_path / "gradlew.bat").write_text("@echo off\necho Gradle simulated\n")

        src = tmpl_path / "src" / "main" / "java" / "com" / "example" / "{{MOD_ID}}"
        src.mkdir(parents=True, exist_ok=True)
        resources = tmpl_path / "src" / "main" / "resources" / "META-INF"
        resources.mkdir(parents=True, exist_ok=True)

        (src / "ExampleMod.java").write_text("""
package com.example.{{MOD_ID}};

import net.neoforged.fml.common.Mod;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Mod("{{MOD_ID}}")
public class ExampleMod {
    public static final String MOD_ID = "{{MOD_ID}}";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public ExampleMod() {
        LOGGER.info("Hello from {{MOD_NAME}}!");
    }
}
""")
        (resources / "neoforge.mods.toml").write_text("""
modLoader="javafml"
loaderVersion="[4,)"
license="MIT"
[[mods]]
modId="{{MOD_ID}}"
version="${file.jarVersion}"
displayName="{{MOD_NAME}}"
description="A mod created with Diorite"
""")

    def _neoforge_build_gradle(self, mc_version, neo_version):
        return f"""
plugins {{
    id 'java-library'
    id 'eclipse'
    id 'idea'
    id 'maven-publish'
    id 'net.neoforged.gradle.userdev' version '7.0.163'
}}

version = project.mod_version
group = project.maven_group

base {{
    archivesName = project.archives_base_name
}}

java.toolchain.languageVersion = JavaLanguageVersion.of(21)

println "Java: ${{System.getProperty('java.version')}} JVM: ${{System.getProperty('java.vm.version')}} (${{System.getProperty('java.vendor')}}) Arch: ${{System.getProperty('os.arch')}}"

minecraft {{
    mappings channel: 'official', version: '{mc_version}'

    copyIdeResources = true
    generateRunFolders = true

    runs {{
        client {{
            workingDirectory project.file('run')
            property 'forge.logging.markers', 'REGISTRIES'
            property 'forge.logging.console.level', 'debug'
            mods {{
                {self._placeholder('MOD_ID')} {{
                    source sourceSets.main
                }}
            }}
        }}
        server {{
            workingDirectory project.file('run')
            property 'forge.logging.markers', 'REGISTRIES'
            mods {{
                {self._placeholder('MOD_ID')} {{
                    source sourceSets.main
                }}
            }}
        }}
    }}
}}

sourceSets.main.resources {{ srcDir 'src/generated/resources' }}

repositories {{
    // maven {{ url = 'https://maven.neoforged.net/releases' }}
}}

dependencies {{
    implementation "net.neoforged:neoforge:{neo_version}"
}}

tasks.named('processResources', ProcessResources).configure {{
    var replaceProperties = [
        mod_id: "{self._placeholder('MOD_ID')}", mod_name: "{self._placeholder('MOD_NAME')}",
        mod_version: project.mod_version, minecraft_version: project.minecraft_version, neo_version: project.neo_version
    ]
    inputs.properties replaceProperties
    filesMatching(['META-INF/neoforge.mods.toml', 'pack.mcmeta']) {{
        expand replaceProperties + [project: project]
    }}
}}
"""

    def _create_forge_template(self, mc_version: str):
        tmpl_id = f"forge-{mc_version}"
        tmpl_path = self.templates_root / tmpl_id
        tmpl_path.mkdir(parents=True, exist_ok=True)
        (tmpl_path / "template.json").write_text(json.dumps({
            "id": tmpl_id,
            "name": f"Forge {mc_version}",
            "loader": "forge",
            "mc_version": mc_version,
            "loader_version": "47.1.0",
            "description": f"Forge mod template for Minecraft {mc_version}",
            "java_version": 17
        }, indent=2))
        (tmpl_path / "build.gradle").write_text("// Forge 1.20.1 build.gradle placeholder\nplugins { id 'eclipse'; id 'idea'; id 'net.minecraftforge.gradle' version '6.0.+' }\n")
        (tmpl_path / "settings.gradle").write_text("")
        (tmpl_path / "gradle.properties").write_text(f"minecraft_version={mc_version}\n")
        (tmpl_path / "gradlew").write_text("#!/bin/sh\n echo gradle\n")
        (tmpl_path / "gradlew.bat").write_text("@echo off\n echo gradle\n")

    def _placeholder(self, name):
        return "{{" + name + "}}"

    def list_templates(self) -> List[dict]:
        result = []
        for p in self.templates_root.iterdir():
            if not p.is_dir():
                continue
            meta_file = p / "template.json"
            if meta_file.exists():
                try:
                    data = json.loads(meta_file.read_text())
                    result.append(data)
                except Exception:
                    continue
            else:
                result.append({"id": p.name, "name": p.name, "loader": "unknown", "mc_version": "unknown"})
        return sorted(result, key=lambda x: x["id"])

    def get_template(self, template_id: str) -> Optional[dict]:
        meta_file = self.templates_root / template_id / "template.json"
        if meta_file.exists():
            try:
                return json.loads(meta_file.read_text())
            except:
                return None
        return None

    def copy_template(self, template_id: str, dest_path: Path, replacements: Dict[str, str]) -> Path:
        src = self.templates_root / template_id
        if not src.exists():
            raise FileNotFoundError(f"Template {template_id} not found")
        # Copy all files
        shutil.copytree(src, dest_path, dirs_exist_ok=True)

        # Remove template.json from project copy
        tmpl_json = dest_path / "template.json"
        if tmpl_json.exists():
            tmpl_json.unlink()

        # Apply replacements to all text files
        for file_path in dest_path.rglob("*"):
            if file_path.is_file():
                # Skip binary extensions
                if file_path.suffix.lower() in (".jar", ".png", ".jpg", ".ico", ".class"):
                    continue
                try:
                    content = file_path.read_text(encoding='utf-8')
                    # Replace placeholders
                    replaced = content
                    for key, val in replacements.items():
                        replaced = replaced.replace(f"{{{{{key}}}}}", val)
                        replaced = replaced.replace(f"{{{{{key.lower()}}}}}", val.lower())
                    if replaced != content:
                        file_path.write_text(replaced, encoding='utf-8')
                except UnicodeDecodeError:
                    continue
                except Exception:
                    continue

        # Handle special directory renames that contain placeholder in path
        # e.g., com/example/{{MOD_ID}} -> com/example/mymod
        mod_id = replacements.get("MOD_ID", "examplemod")
        for dir_path in sorted(dest_path.rglob("*"), reverse=True):
            if "{{MOD_ID}}" in str(dir_path):
                new_path = Path(str(dir_path).replace("{{MOD_ID}}", mod_id.lower()))
                if not new_path.exists():
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        dir_path.rename(new_path)
                    except Exception:
                        pass

        return dest_path
