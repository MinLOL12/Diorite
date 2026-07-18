from fastapi import APIRouter, HTTPException
from ...services.ai_context_service import AIContextService
from ...models.schemas import AIContextRequest, AIChatRequest
import os

router = APIRouter(prefix="/api/ai", tags=["ai"])
context_service = AIContextService()

@router.post("/context")
def build_context(req: AIContextRequest):
    try:
        ctx = context_service.build_context(
            project_id=req.project_id,
            open_files=req.open_files,
            current_file=req.current_file,
            cursor_pos=req.cursor_position
        )
        return ctx
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
def ai_chat(req: AIChatRequest):
    try:
        ctx = context_service.build_context(
            project_id=req.project_id,
            open_files=req.open_files,
            current_file=req.current_file
        )
        # In real implementation, call LLM with context
        # For now, provide mock project-aware response

        # If OPENAI_API_KEY exists, we could call it, but we'll simulate for offline
        api_key = os.getenv("OPENAI_API_KEY")

        # Craft intelligent mock response based on context
        prompt = req.message.lower()

        # Simple heuristic responses
        response = ""
        if "block" in prompt:
            response = f"""Based on your project **{ctx['project'].get('name')}** ({ctx['loader']} {ctx['minecraft_version']}):

To create a block, use the scaffold action or manually:

```java
// In your ModBlocks class
public static final Block MY_BLOCK = Registry.register(
    BuiltInRegistries.BLOCK,
    ResourceLocation.fromNamespaceAndPath("{ctx['mod_id']}", "my_block"),
    new Block(BlockBehaviour.Properties.of().strength(3.0f))
);
```

Current open files involve: {', '.join(ctx['open_files'][:3])}
I see you have {len(ctx['symbols'])} symbol groups analyzed. Would you like me to scaffold a new block?

Project structure snippet:
```
{ctx['structure'][:500]}
```
"""
        elif "item" in prompt:
            response = f"""For **{ctx['mod_id']}** ({ctx['loader']}):

```java
public static final Item MY_ITEM = Registry.register(
    BuiltInRegistries.ITEM,
    ResourceLocation.fromNamespaceAndPath("{ctx['mod_id']}", "my_item"),
    new Item(new Item.Properties().stacksTo(16))
);
```

You have {ctx['recent_files'].__len__()} recently edited files. Current MC version is {ctx['minecraft_version']}.
"""
        else:
            response = f"""I'm Diorite AI, project-aware assistant for **{ctx['project'].get('name', 'your mod')}**.

Context I've built:
- Loader: {ctx['loader']} {ctx['minecraft_version']}
- Mod ID: {ctx['mod_id']}
- Open files: {len(ctx['open_files'])} (currently: {ctx['current_file']})
- Recent files: {ctx['recent_files'][:3]}
- Dependencies: {list(ctx['dependencies'].get('gradle_props', {}).keys())[:5]}
- Token estimate: {ctx['context_tokens_estimate']}

Your question: "{req.message}"

Here's a tailored suggestion for {ctx['loader']} {ctx['minecraft_version']}:
- Use shared cache at ~/.diorite - your Java {ctx['project'].get('java_version', 21)} is already cached
- Follow {ctx['loader']} registration patterns for {ctx['minecraft_version']}
- Consider using data components for custom item data (new in 1.20.5+)

Would you like me to scaffold something (block/item/entity/screen/recipe/component)?

*Tip: This response is project-aware, using open files, structure, symbols, version, mappings, dependencies, and recently edited files rather than sending full workspace.*
"""

        return {
            "response": response,
            "context_used": {
                "open_files": ctx["open_files"],
                "current_file": ctx["current_file"],
                "mc_version": ctx["minecraft_version"],
                "loader": ctx["loader"],
                "mod_id": ctx["mod_id"],
                "symbols_count": len(ctx["symbols"]),
                "recent": ctx["recent_files"][:5],
                "tokens": ctx["context_tokens_estimate"]
            },
            "model": "diorite-mock-v1" if not api_key else "gpt-4o-mini-with-project-context"
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
