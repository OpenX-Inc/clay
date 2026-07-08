# Changelog

## [0.14.0](https://github.com/OpenX-Inc/clay/compare/v0.13.0...v0.14.0) (2026-07-08)


### Features

* **bench:** run_texture validation + texture results ([f621e17](https://github.com/OpenX-Inc/clay/commit/f621e17118ff7d4e550fb94519bf47a5158d6363))
* **gpu-backend:** shared Hunyuan base + paint image (rasterizer, mesh-painter, RealESRGAN, bpy) ([66cc2a1](https://github.com/OpenX-Inc/clay/commit/66cc2a174a22adddf4314ba982a80a7189c42b90))
* **gpu-backend:** wire Hunyuan3D-Paint texture runtime (image→textured GLB; validated on A10G) ([16f5110](https://github.com/OpenX-Inc/clay/commit/16f5110662cff64071c6537595001337387d3c8d))
* **providers:** register hunyuanpaint texture provider (non-commercial, self-host) ([4833cce](https://github.com/OpenX-Inc/clay/commit/4833cce27861769d9ba2b4f690eb8cf2a1b75abe))

## [0.13.0](https://github.com/OpenX-Inc/clay/compare/v0.12.0...v0.13.0) (2026-07-08)


### Features

* **bench:** run_hunyuan — validate Hunyuan3D shape runtime on Modal ([46ee063](https://github.com/OpenX-Inc/clay/commit/46ee063500e6028065c95be8bb4c9683328c75c3))
* **gpu-backend:** Hunyuan3D Modal image (repo on PYTHONPATH, mc path, no diso) ([c17f484](https://github.com/OpenX-Inc/clay/commit/c17f484f646a35a2d76d209953328d64365c982b))
* **gpu-backend:** wire Hunyuan3D-2.1 shape runtime (image→3D, mc extractor; validated watertight on A10G) ([2c6c3da](https://github.com/OpenX-Inc/clay/commit/2c6c3da1f0ddba987d1a69f0f7731531b1ebdf22))

## [0.12.0](https://github.com/OpenX-Inc/clay/compare/v0.11.0...v0.12.0) (2026-07-08)


### Features

* **bench:** run_material — validate the material runtime on Modal ([4c6d0a4](https://github.com/OpenX-Inc/clay/commit/4c6d0a4ddad276631b2e48f41a03bb472534ef30))
* **gpu-backend:** material Modal image (diffusers/StableMaterials) ([4eac139](https://github.com/OpenX-Inc/clay/commit/4eac139a191c23e24294c1357275bc28b2104511))
* **gpu-backend:** wire StableMaterials material runtime — real tiling PBR maps (validated on A10G) ([c1ddeab](https://github.com/OpenX-Inc/clay/commit/c1ddeabc127536b8dc7be659e967d504c9469d6c))
* **material:** include height map in the client map set ([ef68a1a](https://github.com/OpenX-Inc/clay/commit/ef68a1abc62e3934f701d31c97b682ebf0a4c9d3))

## [0.11.0](https://github.com/OpenX-Inc/clay/compare/v0.10.0...v0.11.0) (2026-07-07)


### Features

* **cli:** clay variations command ([08320fe](https://github.com/OpenX-Inc/clay/commit/08320fe34ec887070c1b111c466606851961636d))
* **gpu-backend:** thread seed through the contract (request→payload→runtime) ([985999a](https://github.com/OpenX-Inc/clay/commit/985999ae447fddcbda7c32e2bc978041ffa31546))
* **tools:** generate_variations tool (shape reuse, GPU-gated) ([2665aaf](https://github.com/OpenX-Inc/clay/commit/2665aaf1b497e14cd5706e8ef5ecab01674ab0ff))
* **variations:** generate_variations — N seed-varied generations via the shape pipeline ([c9a3f85](https://github.com/OpenX-Inc/clay/commit/c9a3f8532b58b32acea3b2d9ae0911b3bef76260))


### Bug Fixes

* **test:** import generate_variations directly (ruff N812) ([52968ac](https://github.com/OpenX-Inc/clay/commit/52968ac2055ffa6e82679a53d35e1c88e0b64eda))


### Documentation

* asset tools + commands + provider categories in README/config; roadmap update ([c2f3f17](https://github.com/OpenX-Inc/clay/commit/c2f3f173c65bf3a677e562866946461b4e1cd18c))

## [0.10.0](https://github.com/OpenX-Inc/clay/compare/v0.9.0...v0.10.0) (2026-07-07)


### Features

* **cli:** clay texture command + --texture opt-in flag on generate ([7d62c41](https://github.com/OpenX-Inc/clay/commit/7d62c41276f6bfb11b3a2019f5ee4825d40bba09))
* **gpu-backend:** real /texture route + runtime.generate_texture (honest gating) ([8107c1c](https://github.com/OpenX-Inc/clay/commit/8107c1c1c1bf1b046e2b36efbf23dc0bb75fc7eb))
* **providers:** register texture providers (paint3d/syncmvd/texture) ([a577c39](https://github.com/OpenX-Inc/clay/commit/a577c3954c28bd09e490fbb21ea387c21f3de936))
* **texture:** TextureAssetGenerator — UV-aware (re)texture + decals + manifest via /texture ([81918b8](https://github.com/OpenX-Inc/clay/commit/81918b8c558882332e78a2a2e34f9225b02f9ec5))
* **tools:** texture_asset tool (re-skin any mesh, GPU-gated) ([88cd2bb](https://github.com/OpenX-Inc/clay/commit/88cd2bb30eb4544918cb818593698a19b810b7e1))

## [0.9.0](https://github.com/OpenX-Inc/clay/compare/v0.8.0...v0.9.0) (2026-07-07)


### Features

* **cli:** clay material command + --material opt-in flag on generate ([505e4c2](https://github.com/OpenX-Inc/clay/commit/505e4c22099247e86bfde55c93df43d8aba19c9d))
* **gpu-backend:** /material route + runtime.generate_material (honest GPU gating) ([0f45970](https://github.com/OpenX-Inc/clay/commit/0f459706d2f3054b492cb8ffbc4067c56e31d06f))
* **material:** MaterialGenerator — PBR set + material.json via /material backend route ([b8b9aba](https://github.com/OpenX-Inc/clay/commit/b8b9aba3e22ce2c02cd5d75122ed0d2f3b6f88e1))
* **providers:** provider categories (shape/material/texture) + material providers ([31ec59f](https://github.com/OpenX-Inc/clay/commit/31ec59f8cfb669cdf4da3517ada7e02137bd7131))
* **tools:** generate_material tool (5 PBR maps + manifest, GPU-gated) ([b8cceba](https://github.com/OpenX-Inc/clay/commit/b8cceba3b039c8421087c1890ac90826f46726fe))

## [0.8.0](https://github.com/OpenX-Inc/clay/compare/v0.7.0...v0.8.0) (2026-07-07)


### Features

* **blender:** per-profile auto-rig (biped/quadruped/vehicle/generic) → skinned/parented FBX ([5db594a](https://github.com/OpenX-Inc/clay/commit/5db594a8ddcc57d78b605634d3172dd74101bb04))
* **cli:** clay rig command + --rig/--rig-type opt-in flags on generate ([fa3c9bd](https://github.com/OpenX-Inc/clay/commit/fa3c9bd83fc38db3442bda204e1b292162d11c04))
* **tools:** rig_asset tool (heuristic per-profile, Blender-backed) ([a9eb5f7](https://github.com/OpenX-Inc/clay/commit/a9eb5f753b7a856dd5cf83b4dc48363b36acc621))

## [0.7.0](https://github.com/OpenX-Inc/clay/compare/v0.6.0...v0.7.0) (2026-07-07)


### Features

* **blender:** high→low tangent-space normal (+AO) bake (script + ops) ([085e84b](https://github.com/OpenX-Inc/clay/commit/085e84b0c990f3194dfbc9ad1dbd337115f120d5))
* **cli:** clay bake command + --bake opt-in flag on generate ([ce3c63d](https://github.com/OpenX-Inc/clay/commit/ce3c63d58a86a363fde3e407f4e572d5545df5b7))
* **tools:** bake_normals tool (Blender, decimates low if omitted) ([01b9b16](https://github.com/OpenX-Inc/clay/commit/01b9b16532f387f0612cc03d4650195efc9ab181))

## [0.6.0](https://github.com/OpenX-Inc/clay/compare/v0.5.0...v0.6.0) (2026-07-07)


### Features

* **blender:** shared script helpers + Quadriflow retopo (engine + ops) ([8c57b5b](https://github.com/OpenX-Inc/clay/commit/8c57b5b355f8ff40d65f1f1975118bb15e24e384))
* **cli:** clay retopo command + --retopo opt-in flag on generate ([d9ba1a9](https://github.com/OpenX-Inc/clay/commit/d9ba1a92d960d5980498a8c16c8ab33c35e38753))
* **tools:** retopo_asset tool (Blender Quadriflow, quad-dominant + re-unwrap) ([9a6dcae](https://github.com/OpenX-Inc/clay/commit/9a6dcaef48d019f65cebc5ec296b16228009c233))

## [0.5.0](https://github.com/OpenX-Inc/clay/compare/v0.4.0...v0.5.0) (2026-07-07)


### Features

* **cli:** clay lods command + --with-lods opt-in flag on generate ([54f19eb](https://github.com/OpenX-Inc/clay/commit/54f19eb44262ca085077f59c982853e490d506e1))
* **lods:** make_lods — quadric-decimation LOD chain at descending ratios ([3c68eb9](https://github.com/OpenX-Inc/clay/commit/3c68eb92163f2cee2b18f3657e95fa7fbf698543))
* **tools:** make_lods tool ([69f1332](https://github.com/OpenX-Inc/clay/commit/69f1332ec3e6d645175dcb61b33d9573a4e8572f))

## [0.4.0](https://github.com/OpenX-Inc/clay/compare/v0.3.0...v0.4.0) (2026-07-07)


### Features

* **cli:** clay collision command + --collision opt-in flag on generate ([476d5f6](https://github.com/OpenX-Inc/clay/commit/476d5f69ddbc37f69f84bd57d6ba3a29c68fe8f1))
* **collision:** make_collision — convex/box/simplified/compound (coacd + honest fallback) ([8f15584](https://github.com/OpenX-Inc/clay/commit/8f15584f2bdbaa83f4e3b16fba52adfeb7be7ff8))
* **tools:** make_collision tool (CPU geometry) ([95fc279](https://github.com/OpenX-Inc/clay/commit/95fc27978a106019612d909cb99eb1b34f3b5cb2))

## [0.3.0](https://github.com/OpenX-Inc/clay/compare/v0.2.0...v0.3.0) (2026-07-07)


### Features

* **blender:** FBX export script + ops wrapper ([eb29239](https://github.com/OpenX-Inc/clay/commit/eb2923918b4dde2747251dd727c20f2d79ac7824))
* **blender:** headless Blender engine — resolve binary, run scripts, honest gating ([297934e](https://github.com/OpenX-Inc/clay/commit/297934e6e87b893204dfa445a73c4153548ba38e))
* **cli:** clay export-fbx command ([a3848f9](https://github.com/OpenX-Inc/clay/commit/a3848f997ceecf68c93550f053a15625785d4af8))
* **config:** [blender] section — headless Blender mesh-processing engine path ([39d81ee](https://github.com/OpenX-Inc/clay/commit/39d81eeb07dd7ce7b5e564ffe6e21a043de6878c))
* **postprocess:** real FBX export via Blender (R1) — replaces honest stub ([51fedfe](https://github.com/OpenX-Inc/clay/commit/51fedfe47c305309eef980fd4b11629229653f6c))
* **tools:** export_fbx tool (Blender-backed, fails visibly) ([04da4ae](https://github.com/OpenX-Inc/clay/commit/04da4ae2e3184db1d083f46de86ad9c2a0030619))


### Documentation

* **config:** document [blender] path in example config ([c54d99a](https://github.com/OpenX-Inc/clay/commit/c54d99a25236561e6fa4fc3076b7fc7246c1bcee))

## [0.2.0](https://github.com/OpenX-Inc/clay/compare/v0.1.0...v0.2.0) (2026-07-07)


### Features

* **bench:** default case matrix (tri-budget sweep + object variety) ([6755c28](https://github.com/OpenX-Inc/clay/commit/6755c2806e54c554d848924bfed296e19f3feada))
* **bench:** Modal harness — real runtime + postprocess, per-case metrics/cost, visible failures ([b91daec](https://github.com/OpenX-Inc/clay/commit/b91daece86485027ffe65944c0ba2f1c48bfd258))
* **gpu-backend:** multi-arch ext build (8.0;8.6;8.9) — runs on A10G/A100/L40S; default GPU A10G ([584860a](https://github.com/OpenX-Inc/clay/commit/584860ac74c53a729c3b217cadb7c0b1b7cf9d8f))
* **gpu-backend:** real TRELLIS-2 image — from-source CUDA-extension build (nvdiffrast/diffoctreerast/diff-gaussian-rast/vox2seq, xformers/spconv/kaolin) ([19b5abb](https://github.com/OpenX-Inc/clay/commit/19b5abb9fcc9be145221f2b83d5b73af353fca4e))
* **gpu-backend:** thread target_tris through the contract to the runtime ([9389939](https://github.com/OpenX-Inc/clay/commit/93899392f39bb190f3966ef76684e4b2319a8cb5))
* **preview:** clay preview — self-contained interactive model-viewer HTML ([2f38238](https://github.com/OpenX-Inc/clay/commit/2f38238f6faf992702df75dc118fd782f25fdf6e))


### Bug Fixes

* **bench:** use the real shared TRELLIS image (pip install git+ was invalid) ([95447d4](https://github.com/OpenX-Inc/clay/commit/95447d4459977530f971b0f27c85b9f43dbc2b4e))
* **gpu-backend:** --no-build-isolation for CUDA extension builds (nvdiffrast et al.) ([6fb66db](https://github.com/OpenX-Inc/clay/commit/6fb66dbf11e0ee17bd1817b736636f9a3bd5dfa8))
* **gpu-backend:** add fast-simplification/pygltflib for postprocess (late layer, keeps ext cache) ([e122e0f](https://github.com/OpenX-Inc/clay/commit/e122e0fcc3697b4aad99ca67dad54c15e490ec7e))
* **gpu-backend:** drive TRELLIS to_glb simplify from tri budget (texture-aware decimation) ([b27149a](https://github.com/OpenX-Inc/clay/commit/b27149a6cb9b114bd6aebb9a678e7229d25622ab))
* **gpu-backend:** drop vox2seq (not part of TRELLIS setup); ext build complete ([4e5adbd](https://github.com/OpenX-Inc/clay/commit/4e5adbdb856773f41bfa9d4c900d3b2cd836f3b3))
* **gpu-backend:** force gcc/g++ for CUDA ext builds (inline, keeps torch layer cached) ([1226f78](https://github.com/OpenX-Inc/clay/commit/1226f784090463b74d89b9022c8ef82d47172df2))
* **gpu-backend:** install setuptools/wheel before --no-build-isolation ext builds ([685c8ca](https://github.com/OpenX-Inc/clay/commit/685c8ca43bbef11ff59618b5287ad3ba8a4a873c))
* **gpu-backend:** set ATTN_BACKEND/SPCONV_ALGO before import, run TRELLIS in-place, robust face count ([c4742a3](https://github.com/OpenX-Inc/clay/commit/c4742a310dc7ea3d8c878b837533f5579117b19e))
* **postprocess:** preserve provider-baked textures — skip destructive re-unwrap/decimate when textured ([8e238aa](https://github.com/OpenX-Inc/clay/commit/8e238aa1a6d5be365e7609a50b0b689984ff43bb))


### Documentation

* **bench:** first real TRELLIS-2 results on A10G (5/5 textured, ~1.5-11c/asset) ([6d43b40](https://github.com/OpenX-Inc/clay/commit/6d43b40e4054e035aa3d01054f8af2e80495c4ce))
* **bench:** how to run the Clay benchmarks ([5907e46](https://github.com/OpenX-Inc/clay/commit/5907e46d1d850ae0f736450d12959bba3c0592f5))
* **bench:** input image prompts (single-object, Clay-branded, 3D-friendly) ([d0c39ad](https://github.com/OpenX-Inc/clay/commit/d0c39adf8d95afa5eebc027c8e8c799e4325573e))

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
