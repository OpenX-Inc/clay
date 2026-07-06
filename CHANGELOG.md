# Changelog

## 0.1.0 (2026-07-06)


### Features

* **agent:** OpenAI-compatible client (NVIDIA build, default kimi, CLAY_NVIDIA_API_KEY) ([636b8a6](https://github.com/OpenX-Inc/clay/commit/636b8a62ddaec49ab22a5b0af09c729ab7b7a214))
* **agent:** tool-calling loop over the shared registry ([1ef2389](https://github.com/OpenX-Inc/clay/commit/1ef238945a11410e123d82e4c145b8261d461567))
* clay package skeleton + smoke test ([7ea7614](https://github.com/OpenX-Inc/clay/commit/7ea76144f563151baf898b2395388b1ebb355aa0))
* **cli:** 'clay generate' (image/text, --format/--target-tris/--dry-run) + 'clay providers' ([ac16ea7](https://github.com/OpenX-Inc/clay/commit/ac16ea7f249c8e943a7608a521309f0c5b9f2be4))
* **cli:** clay agent + clay mcp commands ([a342ae8](https://github.com/OpenX-Inc/clay/commit/a342ae8541c5262d3c923b971b805d4e447282f4))
* **cli:** clay deploy &lt;provider&gt; — named GPU-backend deploy with scoped tokens ([7cf52ce](https://github.com/OpenX-Inc/clay/commit/7cf52ce4d3b5a7a576a7e9f694dadccaca8d15f1))
* **config:** Pydantic Config + TOML loader (gpu_backend, providers, postprocess, agent, mcp, deploy) ([958ca9f](https://github.com/OpenX-Inc/clay/commit/958ca9fb0ba18b346a1a8e0607786761e7fd97b7))
* **deploy:** DeploySpec/DeployResult/Deployer ABC + provider registry ([0697100](https://github.com/OpenX-Inc/clay/commit/069710012b8abdb10d4296b76b2386bf17039902))
* **deploy:** honest AWS/GCP scaffolds (manual_required, no fake success) ([4dad02e](https://github.com/OpenX-Inc/clay/commit/4dad02ef8af2aa12e6d257850f86391de5322d83))
* **deploy:** ModalDeployer — real modal deploy, per-invocation token scoped to subprocess ([41e5d05](https://github.com/OpenX-Inc/clay/commit/41e5d05cbf84255bf78489601bed8c1b1f92b9b5))
* **deploy:** package exports + deployer registration ([69d9e08](https://github.com/OpenX-Inc/clay/commit/69d9e085e869dd9b5d5a2d1a9e1c19d644b4c152))
* **generator:** orchestrator → GPU backend HTTP contract (image/text→3D, base64 or URL) ([9c8f841](https://github.com/OpenX-Inc/clay/commit/9c8f84113bc1460e108248049e379b30daf47320))
* **gpu-backend:** FastAPI contract server (generate/remesh/texture/health, base64) ([40a0cd5](https://github.com/OpenX-Inc/clay/commit/40a0cd5c5f2770ea9ae6d6c1806838940ba537a0))
* **gpu-backend:** model runtime dispatch — TRELLIS-2 wired, others fail visibly ([7eafee0](https://github.com/OpenX-Inc/clay/commit/7eafee0c7c0f972af1f49f9abf746fab4a7fed07))
* **gpu-backend:** package for the base64 HTTP contract ([49717ab](https://github.com/OpenX-Inc/clay/commit/49717abd95d022ba62737c89d2ccb65553a9f439))
* **gpu-backend:** parameterized Modal deploy (named instances via env) ([0f19442](https://github.com/OpenX-Inc/clay/commit/0f19442d70256963a11bc0acc96cb76e0e9cb4a3))
* **mcp:** streamable-HTTP MCP server exposing the same tool registry ([0f4888c](https://github.com/OpenX-Inc/clay/commit/0f4888ce1d03c2a85e067df687ab23f9a860b38e))
* **pipeline:** end-to-end generate → post-process → game-ready asset ([dad3bf9](https://github.com/OpenX-Inc/clay/commit/dad3bf9d6556fd2bcd4aeb18996f488724610659))
* **postprocess:** game-ready pipeline — decimate to tri budget, xatlas UV unwrap, GLB/OBJ export ([dd86db0](https://github.com/OpenX-Inc/clay/commit/dd86db000b165e41d8258dfc4dd63424e400dae0))
* **providers:** ModelProvider registry (register/get/available, supports) ([73f62ff](https://github.com/OpenX-Inc/clay/commit/73f62ff644f34f5b7f7b8b3e59d7d15eca45e56e))
* **providers:** register TRELLIS-2 (MIT primary), Hunyuan3D-2.1, Hi3DGen ([0eef99f](https://github.com/OpenX-Inc/clay/commit/0eef99f1849afdab3c95e542bab0215c42b804f6))
* **schemas:** GenerationRequest, Texture, Generated3DAsset ([44373cc](https://github.com/OpenX-Inc/clay/commit/44373cc43c2648021b5091a6d4e89cdeae72511f))
* **tools:** asset tools — generate_asset, remesh_asset, list_assets, list_providers ([f907fdc](https://github.com/OpenX-Inc/clay/commit/f907fdc8ba7590caad3092de229962e63b65d8b1))
* **tools:** package exports + registration module ([d7882f0](https://github.com/OpenX-Inc/clay/commit/d7882f03a13a961245f3710c4fd8401f890dd196))
* **tools:** registry — [@tool](https://github.com/tool) decorator, param DSL → JSON Schema, OpenAI/MCP wrappers ([9c9ad61](https://github.com/OpenX-Inc/clay/commit/9c9ad61f8183ab869a355815e1fb724fa68113a8))
* **tools:** result envelope — ok/error as values, not exceptions ([ae4e0a1](https://github.com/OpenX-Inc/clay/commit/ae4e0a1f40c730338df1b0b6d164d112ebaf19a5))
* **tools:** ToolContext + single dispatch chokepoint (exceptions → error values) ([98a9161](https://github.com/OpenX-Inc/clay/commit/98a916189a5aff9b93bafdd39154ff4873ed4f7e))


### Bug Fixes

* ruff — StrEnum for GenMode + wrap long test line ([3be63cd](https://github.com/OpenX-Inc/clay/commit/3be63cd6b4ca7e80729abbc9d647d5794981cdd6))


### Documentation

* README — deploy, agent+MCP, commands, roadmap, honest GPU-gated status ([3f741f1](https://github.com/OpenX-Inc/clay/commit/3f741f1c6644d9eb4578b7e4a519cb85a8eb5047))
* README, CONTRIBUTING, example config ([c338d9b](https://github.com/OpenX-Inc/clay/commit/c338d9bcdd469a224561c86f977456e2021ea264))
